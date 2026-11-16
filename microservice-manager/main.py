from datetime import datetime, timedelta, timezone

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session

from common.database import get_db
from common.models import LigneLivraison, Livraison, PointDepot, Produit, Utilisateur
from common.security import (
    create_access_token,
    decode_token,
    generate_totp_secret,
    get_current_user,
    hash_password,
    require_role,
    verify_password,
    verify_totp,
)

app = FastAPI(title="microservice-manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class DashboardWSManager:
    def __init__(self):
        self.active: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict):
        stale = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)


ws_manager = DashboardWSManager()


# -------- Schemas --------
class LoginRequest(BaseModel):
    telephone: str
    mot_de_passe: str


class TwoFARequest(BaseModel):
    temp_token: str
    code: str


class TwoFASetupVerify(BaseModel):
    code: str


# -------- Health --------
@app.get("/health")
def health():
    return {"status": "ok", "service": "manager"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "ok"}


# -------- Auth --------
@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(Utilisateur).where(Utilisateur.telephone == payload.telephone))
    if not user or not verify_password(payload.mot_de_passe, user.mot_de_passe_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    if user.deux_fa_actif and user.totp_secret:
        temp_token = create_access_token(user, extra={"pending_2fa": True})
        return {"requires_2fa": True, "temp_token": temp_token}
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user_id": user.id}


@app.post("/auth/2fa/verify")
def verify_2fa(payload: TwoFARequest, db: Session = Depends(get_db)):
    data = decode_token(payload.temp_token)
    if not data.get("pending_2fa"):
        raise HTTPException(status_code=400, detail="Jeton 2FA invalide")
    user = db.get(Utilisateur, int(data["sub"]))
    if not user or not user.totp_secret:
        raise HTTPException(status_code=400, detail="2FA non configurée")
    if not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=401, detail="Code 2FA invalide")
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user_id": user.id}


@app.post("/auth/2fa/setup")
def setup_2fa(user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.totp_secret:
        user.totp_secret = generate_totp_secret()
    user.deux_fa_actif = False
    db.commit()
    uri = f"otpauth://totp/Triad:{user.telephone}?secret={user.totp_secret}&issuer=Triad"
    return {"secret": user.totp_secret, "otpauth_uri": uri}


@app.post("/auth/2fa/enable")
def enable_2fa(payload: TwoFASetupVerify, user: Utilisateur = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.totp_secret or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=400, detail="Code invalide")
    user.deux_fa_actif = True
    db.commit()
    return {"deux_fa_actif": True}


# -------- Dashboard / Gestion --------
@app.get("/dashboard/summary")
def dashboard_summary(user: Utilisateur = Depends(require_role("manager")), db: Session = Depends(get_db)):
    today = datetime.now(timezone.utc).date()
    start_day = datetime(today.year, today.month, today.day, tzinfo=timezone.utc)
    end_day = start_day + timedelta(days=1)

    ca_jour = db.scalar(
        select(func.coalesce(func.sum(Livraison.montant_percu), 0)).where(
            Livraison.statut == "livree",
            Livraison.date_heure >= start_day,
            Livraison.date_heure < end_day,
        )
    )
    livraisons_jour = db.scalar(
        select(func.count(Livraison.id)).where(
            Livraison.date_heure >= start_day, Livraison.date_heure < end_day
        )
    )
    nb_agents = db.scalar(select(func.count(Utilisateur.id)).where(Utilisateur.role == "agent"))
    nb_clients = db.scalar(select(func.count(Utilisateur.id)).where(Utilisateur.role == "client"))
    return {
        "chiffre_affaires_jour": float(ca_jour or 0),
        "livraisons_jour": int(livraisons_jour or 0),
        "nombre_agents": int(nb_agents or 0),
        "nombre_clients": int(nb_clients or 0),
    }


@app.get("/ventes")
def list_ventes(user: Utilisateur = Depends(require_role("manager")), db: Session = Depends(get_db)):
    ventes = db.scalars(select(Livraison).order_by(Livraison.date_heure.desc()).limit(200)).all()
    result = []
    for v in ventes:
        agent = db.get(Utilisateur, v.agent_id) if v.agent_id else None
        depot = db.get(PointDepot, v.point_depot_id) if v.point_depot_id else None
        result.append(
            {
                "id": v.id,
                "date_heure": v.date_heure.isoformat() if v.date_heure else None,
                "statut": v.statut,
                "montant_percu": float(v.montant_percu or 0),
                "client_telephone": v.client_telephone,
                "agent": agent.nom if agent else None,
                "point_depot": depot.nom if depot else None,
                "latitude": v.latitude,
                "longitude": v.longitude,
            }
        )
    return result


@app.get("/agents")
def list_agents(user: Utilisateur = Depends(require_role("manager")), db: Session = Depends(get_db)):
    agents = db.scalars(select(Utilisateur).where(Utilisateur.role == "agent")).all()
    out = []
    for a in agents:
        ventes_count = db.scalar(
            select(func.count(Livraison.id)).where(Livraison.agent_id == a.id, Livraison.statut == "livree")
        )
        ca = db.scalar(
            select(func.coalesce(func.sum(Livraison.montant_percu), 0)).where(
                Livraison.agent_id == a.id, Livraison.statut == "livree"
            )
        )
        out.append(
            {
                "id": a.id,
                "nom": a.nom,
                "telephone": a.telephone,
                "ventes_livrees": int(ventes_count or 0),
                "chiffre_affaires": float(ca or 0),
            }
        )
    return out


@app.get("/points-depot/rentables")
def points_depot_rentables(user: Utilisateur = Depends(require_role("manager")), db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            PointDepot.id,
            PointDepot.nom,
            PointDepot.adresse,
            func.coalesce(func.sum(Livraison.montant_percu), 0).label("chiffre_affaires"),
            func.count(Livraison.id).label("nb_livraisons"),
        )
        .join(Livraison, Livraison.point_depot_id == PointDepot.id)
        .where(Livraison.statut == "livree")
        .group_by(PointDepot.id, PointDepot.nom, PointDepot.adresse)
        .order_by(func.sum(Livraison.montant_percu).desc())
    ).all()
    return [
        {
            "id": r.id,
            "nom": r.nom,
            "adresse": r.adresse,
            "chiffre_affaires": float(r.chiffre_affaires or 0),
            "nb_livraisons": int(r.nb_livraisons or 0),
        }
        for r in rows
    ]


@app.get("/ventes/7jours")
def ventes_7_jours(user: Utilisateur = Depends(require_role("manager")), db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            func.date(Livraison.date_heure).label("jour"),
            func.coalesce(func.sum(Livraison.montant_percu), 0).label("ca"),
        )
        .where(Livraison.statut == "livree", Livraison.date_heure >= func.now() - timedelta(days=7))
        .group_by(func.date(Livraison.date_heure))
        .order_by(func.date(Livraison.date_heure))
    ).all()
    return [{"jour": str(r.jour), "chiffre_affaires": float(r.ca or 0)} for r in rows]


@app.get("/repartition-boissons")
def repartition_boissons(user: Utilisateur = Depends(require_role("manager")), db: Session = Depends(get_db)):
    rows = db.execute(
        select(
            Produit.nom,
            func.coalesce(func.sum(LigneLivraison.quantite), 0).label("quantite"),
        )
        .join(LigneLivraison, LigneLivraison.produit_id == Produit.id)
        .join(Livraison, Livraison.id == LigneLivraison.livraison_id)
        .where(Livraison.statut == "livree")
        .group_by(Produit.nom)
        .order_by(func.sum(LigneLivraison.quantite).desc())
    ).all()
    return [{"produit": r[0], "quantite": int(r.quantite or 0)} for r in rows]


# -------- Temps réel (WebSocket) --------
@app.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket, token: str | None = None):
    if not token:
        await websocket.close(code=1008)
        return
    try:
        payload = decode_token(token)
    except HTTPException:
        await websocket.close(code=1008)
        return
    if payload.get("pending_2fa") or payload.get("role") != "manager":
        await websocket.close(code=1008)
        return

    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({"type": "connected", "message": "Dashboard temps réel connecté"})
        while True:
            # Le client peut envoyer des pings; on garde la connexion ouverte.
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
