import os
from decimal import Decimal

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from common.database import get_db
from common.haversine import distance_km
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

app = FastAPI(title="microservice-client")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DISTANCE_MAX_KM = float(os.getenv("DISTANCE_MAX_KM", "1"))


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


class LigneCommande(BaseModel):
    produit_id: int
    quantite: int


class CommandeRequest(BaseModel):
    point_depot_id: int
    latitude: float | None = None
    longitude: float | None = None
    lignes: list[LigneCommande]


class DistanceCheckRequest(BaseModel):
    point_depot_id: int
    latitude: float
    longitude: float


# -------- Health --------
@app.get("/health")
def health():
    return {"status": "ok", "service": "client"}


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
        role="client",
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
    if user.role != "client":
        raise HTTPException(status_code=403, detail="Compte non client")
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
def setup_2fa(user: Utilisateur = Depends(require_role("client")), db: Session = Depends(get_db)):
    if not user.totp_secret:
        user.totp_secret = generate_totp_secret()
    user.deux_fa_actif = False
    db.commit()
    uri = f"otpauth://totp/Triad:{user.telephone}?secret={user.totp_secret}&issuer=Triad"
    return {"secret": user.totp_secret, "otpauth_uri": uri}


@app.post("/auth/2fa/enable")
def enable_2fa(payload: TwoFASetupVerify, user: Utilisateur = Depends(require_role("client")), db: Session = Depends(get_db)):
    if not user.totp_secret or not verify_totp(user.totp_secret, payload.code):
        raise HTTPException(status_code=400, detail="Code invalide")
    user.deux_fa_actif = True
    db.commit()
    return {"deux_fa_actif": True}


# -------- Catalogue --------
@app.get("/produits")
def list_produits(db: Session = Depends(get_db)):
    produits = db.scalars(select(Produit).order_by(Produit.nom)).all()
    return [{"id": p.id, "nom": p.nom, "type": p.type, "prix": float(p.prix)} for p in produits]


@app.get("/points-depot")
def list_points_depot(db: Session = Depends(get_db)):
    depots = db.scalars(select(PointDepot).order_by(PointDepot.nom)).all()
    return [{"id": d.id, "nom": d.nom, "adresse": d.adresse, "latitude": d.latitude, "longitude": d.longitude} for d in depots]


# -------- Distance --------
@app.post("/distance/check")
def check_distance(payload: DistanceCheckRequest, db: Session = Depends(get_db)):
    depot = db.get(PointDepot, payload.point_depot_id)
    if not depot:
        raise HTTPException(status_code=404, detail="Point de dépôt introuvable")
    dist = distance_km(payload.latitude, payload.longitude, depot.latitude, depot.longitude)
    return {
        "distance_km": round(dist, 3),
        "distance_max_km": DISTANCE_MAX_KM,
        "autorise": dist <= DISTANCE_MAX_KM,
    }


# -------- Commande / Panier --------
@app.post("/commandes", status_code=201)
def creer_commande(payload: CommandeRequest, user: Utilisateur = Depends(require_role("client")), db: Session = Depends(get_db)):
    depot = db.get(PointDepot, payload.point_depot_id)
    if not depot:
        raise HTTPException(status_code=404, detail="Point de dépôt introuvable")
    if payload.latitude is not None and payload.longitude is not None:
        dist = distance_km(payload.latitude, payload.longitude, depot.latitude, depot.longitude)
        if dist > DISTANCE_MAX_KM:
            raise HTTPException(
                status_code=400,
                detail=f"Trop éloigné du point de dépôt ({dist:.2f} km > {DISTANCE_MAX_KM} km)",
            )
    if not payload.lignes:
        raise HTTPException(status_code=400, detail="Panier vide")

    total = Decimal("0")
    lignes_data = []
    for l in payload.lignes:
        produit = db.get(Produit, l.produit_id)
        if not produit:
            raise HTTPException(status_code=400, detail=f"Produit {l.produit_id} introuvable")
        if l.quantite <= 0:
            raise HTTPException(status_code=400, detail="Quantité invalide")
        prix_u = Decimal(str(produit.prix))
        total += prix_u * l.quantite
        lignes_data.append((produit.id, l.quantite, prix_u))

    livraison = Livraison(
        client_id=user.id,
        client_telephone=user.telephone,
        point_depot_id=payload.point_depot_id,
        statut="en_attente",
        latitude=payload.latitude,
        longitude=payload.longitude,
        montant_percu=total,
    )
    db.add(livraison)
    db.flush()
    for produit_id, quantite, prix_u in lignes_data:
        db.add(LigneLivraison(livraison_id=livraison.id, produit_id=produit_id, quantite=quantite, prix_unitaire=prix_u))
    db.commit()
    db.refresh(livraison)
    return {"id": livraison.id, "statut": livraison.statut, "montant_total": float(total)}


@app.get("/mes-commandes")
def mes_commandes(user: Utilisateur = Depends(require_role("client")), db: Session = Depends(get_db)):
    commandes = db.scalars(
        select(Livraison).where(Livraison.client_id == user.id).order_by(Livraison.date_heure.desc())
    ).all()
    out = []
    for c in commandes:
        depot = db.get(PointDepot, c.point_depot_id) if c.point_depot_id else None
        out.append(
            {
                "id": c.id,
                "statut": c.statut,
                "montant_percu": float(c.montant_percu or 0),
                "point_depot": depot.nom if depot else None,
                "date_heure": c.date_heure.isoformat() if c.date_heure else None,
            }
        )
    return out


# -------- Visite 3D (simulée) --------
@app.post("/visite-3d/debloquer")
def debloquer_visite_3d(user: Utilisateur = Depends(require_role("client")), db: Session = Depends(get_db)):
    # Paiement simulé : 200 FCFA
    user.visite_3d_debloquee = True
    db.commit()
    return {"visite_3d_debloquee": True, "montant_fcfa": 200, "message": "Visite 360° débloquée (paiement simulé)"}


@app.get("/visite-3d/statut")
def statut_visite_3d(user: Utilisateur = Depends(require_role("client"))):
    return {"visite_3d_debloquee": bool(user.visite_3d_debloquee)}
