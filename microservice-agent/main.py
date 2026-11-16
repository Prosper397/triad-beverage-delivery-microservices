from datetime import datetime, timezone
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, text
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

app = FastAPI(title="microservice-agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -------- Schemas --------
class RegisterRequest(BaseModel):
    nom: str
    telephone: str
    mot_de_passe: str


class LoginRequest(BaseModel):
    telephone: str
    mot_de_passe: str


class TwoFARequest(BaseModel):
    temp_token: str
    code: str


class TwoFASetupVerify(BaseModel):
    code: str


class LigneVente(BaseModel):
    produit_id: int
    quantite: int


class SaisieVenteRequest(BaseModel):
    client_telephone: str
    point_depot_id: int | None = None
    latitude: float | None = None
    longitude: float | None = None
    montant_percu: float = 0
    lignes: list[LigneVente] = []


# -------- Health --------
@app.get("/health")
def health():
    return {"status": "ok", "service": "agent"}


@app.get("/health/db")
def health_db(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"database": "ok"}


# -------- Auth --------
@app.post("/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.scalar(select(Utilisateur).where(Utilisateur.telephone == payload.telephone))
    if existing:
        raise HTTPException(status_code=400, detail="Téléphone déjà utilisé")
    user = Utilisateur(
        nom=payload.nom,
        telephone=payload.telephone,
        mot_de_passe_hash=hash_password(payload.mot_de_passe),
        role="agent",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "nom": user.nom, "telephone": user.telephone, "role": user.role}


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(Utilisateur).where(Utilisateur.telephone == payload.telephone))
    if not user or not verify_password(payload.mot_de_passe, user.mot_de_passe_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides")
    if user.role != "agent":
        raise HTTPException(status_code=403, detail="Compte non agent")
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
    if not user or not user.totp_secret or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=401, detail="Code 2FA invalide")
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "role": user.role, "user_id": user.id}


@app.post("/auth/2fa/setup")
def setup_2fa(user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    if not user.totp_secret:
        user.totp_secret = generate_totp_secret()
    user.deux_fa_actif = False
    db.commit()
    uri = f"otpauth://totp/Triad:{user.telephone}?secret={user.totp_secret}&issuer=Triad"
    return {"secret": user.totp_secret, "otpauth_uri": uri}


@app.post("/auth/2fa/enable")
def enable_2fa(payload: TwoFASetupVerify, user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    if not user.totp_secret or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=400, detail="Code invalide")
    user.deux_fa_actif = True
    db.commit()
    return {"deux_fa_actif": True}


# -------- Tournée / Livraisons --------
@app.get("/tournee")
def ma_tournee(user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    livraisons = db.scalars(
        select(Livraison)
        .where(Livraison.agent_id == user.id, Livraison.statut.in_(["en_attente", "en_cours"]))
        .order_by(Livraison.date_heure.desc())
    ).all()
    return [_serialize_livraison(v, db) for v in livraisons]


@app.get("/livraisons/disponibles")
def livraisons_disponibles(user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    livraisons = db.scalars(
        select(Livraison).where(Livraison.statut == "en_attente", Livraison.agent_id.is_(None))
        .order_by(Livraison.date_heure.asc())
    ).all()
    return [_serialize_livraison(v, db) for v in livraisons]


@app.post("/livraisons/{livraison_id}/prendre")
def prendre_livraison(livraison_id: int, user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    livraison = db.get(Livraison, livraison_id)
    if not livraison:
        raise HTTPException(status_code=404, detail="Livraison introuvable")
    if livraison.agent_id and livraison.agent_id != user.id:
        raise HTTPException(status_code=400, detail="Livraison déjà prise")
    livraison.agent_id = user.id
    livraison.statut = "en_cours"
    db.commit()
    db.refresh(livraison)
    return _serialize_livraison(livraison, db)


@app.post("/livraisons/{livraison_id}/livrer")
def livrer(livraison_id: int, latitude: float | None = None, longitude: float | None = None,
           user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    livraison = db.get(Livraison, livraison_id)
    if not livraison or livraison.agent_id != user.id:
        raise HTTPException(status_code=404, detail="Livraison introuvable")
    livraison.statut = "livree"
    if latitude is not None:
        livraison.latitude = latitude
    if longitude is not None:
        livraison.longitude = longitude
    db.commit()
    db.refresh(livraison)
    return _serialize_livraison(livraison, db)


# -------- Saisie de vente avec GPS --------
@app.post("/ventes", status_code=201)
def saisir_vente(payload: SaisieVenteRequest, user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    if payload.point_depot_id is not None and not db.get(PointDepot, payload.point_depot_id):
        raise HTTPException(status_code=400, detail="Point de dépôt introuvable")

    lignes_data = []
    total = Decimal("0")
    for l in payload.lignes:
        produit = db.get(Produit, l.produit_id)
        if not produit:
            raise HTTPException(status_code=400, detail=f"Produit {l.produit_id} introuvable")
        if l.quantite <= 0:
            raise HTTPException(status_code=400, detail="Quantité invalide")
        prix_u = Decimal(str(produit.prix))
        total += prix_u * l.quantite
        lignes_data.append((produit.id, l.quantite, prix_u))

    montant = Decimal(str(payload.montant_percu)) if payload.montant_percu else total
    livraison = Livraison(
        agent_id=user.id,
        client_telephone=payload.client_telephone,
        point_depot_id=payload.point_depot_id,
        statut="livree",
        latitude=payload.latitude,
        longitude=payload.longitude,
        montant_percu=montant,
        date_heure=datetime.now(timezone.utc),
    )
    db.add(livraison)
    db.flush()
    for produit_id, quantite, prix_u in lignes_data:
        db.add(LigneLivraison(livraison_id=livraison.id, produit_id=produit_id, quantite=quantite, prix_unitaire=prix_u))
    db.commit()
    db.refresh(livraison)
    return _serialize_livraison(livraison, db)


@app.get("/mes-ventes")
def mes_ventes(user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    ventes = db.scalars(
        select(Livraison).where(Livraison.agent_id == user.id).order_by(Livraison.date_heure.desc()).limit(100)
    ).all()
    return [_serialize_livraison(v, db) for v in ventes]


@app.get("/produits")
def list_produits(user: Utilisateur = Depends(require_role("agent")), db: Session = Depends(get_db)):
    produits = db.scalars(select(Produit).order_by(Produit.nom)).all()
    return [{"id": p.id, "nom": p.nom, "type": p.type, "prix": float(p.prix)} for p in produits]


def _serialize_livraison(v: Livraison, db: Session) -> dict:
    depot = db.get(PointDepot, v.point_depot_id) if v.point_depot_id else None
    lignes = db.scalars(select(LigneLivraison).where(LigneLivraison.livraison_id == v.id)).all()
    return {
        "id": v.id,
        "statut": v.statut,
        "client_telephone": v.client_telephone,
        "point_depot": depot.nom if depot else None,
        "point_depot_id": v.point_depot_id,
        "latitude": v.latitude,
        "longitude": v.longitude,
        "montant_percu": float(v.montant_percu or 0),
        "date_heure": v.date_heure.isoformat() if v.date_heure else None,
        "lignes": [
            {"produit_id": l.produit_id, "quantite": l.quantite, "prix_unitaire": float(l.prix_unitaire)}
            for l in lignes
        ],
    }
