"""Script de données de test pour Triad-Beverage-Delivery.

Usage (depuis la racine du dépôt, Git Bash) :
    PYTHONPATH=. python database/seed.py

Idempotent : relancé plusieurs fois, il ne crée pas de doublons.
Refusé si ENV=production.
"""
import os
import sys
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from common.database import SessionLocal
from common.models import PointDepot, Produit, Utilisateur
from common.security import hash_password

if os.getenv("ENV", "").strip().lower() == "production":
    print("ERREUR : le seed est interdit en production (ENV=production).", file=sys.stderr)
    sys.exit(1)


# --- Données de démo ---
DEPOT = {
    "nom": "Point de dépôt Lomé Centre",
    "adresse": "Boulevard du 13 Janvier, Lomé, Togo",
    "latitude": 6.1319,
    "longitude": 1.2228,
}

PRODUITS = [
    {"nom": "Coca-Cola 33cl", "type": "soda", "prix": Decimal("400.00")},
    {"nom": "Sprite 33cl", "type": "soda", "prix": Decimal("400.00")},
    {"nom": "Jus d'orange 1L", "type": "jus", "prix": Decimal("1200.00")},
]

UTILISATEURS = [
    {
        "nom": "Client Démo",
        "telephone": "90000001",
        "mot_de_passe": "client123",
        "role": "client",
    },
    {
        "nom": "Agent Démo",
        "telephone": "90000002",
        "mot_de_passe": "agent123",
        "role": "agent",
    },
    {
        "nom": "Manager Démo",
        "telephone": "90000003",
        "mot_de_passe": "manager123",
        "role": "manager",
    },
]


def seed_depot(db: Session) -> PointDepot:
    depot = db.scalar(
        select(PointDepot).where(
            PointDepot.nom == DEPOT["nom"],
            PointDepot.latitude == DEPOT["latitude"],
            PointDepot.longitude == DEPOT["longitude"],
        )
    )
    if depot:
        print(f"[=] Point de dépôt déjà présent : {depot.nom} (id={depot.id})")
        return depot

    depot = PointDepot(**DEPOT)
    db.add(depot)
    db.flush()
    print(f"[+] Point de dépôt créé : {depot.nom} (id={depot.id})")
    return depot


def seed_produits(db: Session) -> None:
    for data in PRODUITS:
        produit = db.scalar(select(Produit).where(Produit.nom == data["nom"]))
        if produit:
            print(f"[=] Produit déjà présent : {produit.nom} (id={produit.id})")
            continue
        produit = Produit(**data)
        db.add(produit)
        db.flush()
        print(f"[+] Produit créé : {produit.nom} (id={produit.id})")


def seed_utilisateurs(db: Session) -> None:
    for data in UTILISATEURS:
        user = db.scalar(
            select(Utilisateur).where(Utilisateur.telephone == data["telephone"])
        )
        if user:
            print(f"[=] Utilisateur déjà présent : {user.telephone} ({user.role}, id={user.id})")
            continue
        user = Utilisateur(
            nom=data["nom"],
            telephone=data["telephone"],
            mot_de_passe_hash=hash_password(data["mot_de_passe"]),
            role=data["role"],
        )
        db.add(user)
        db.flush()
        print(f"[+] Utilisateur créé : {user.telephone} ({user.role}, id={user.id})")


def main() -> None:
    db = SessionLocal()
    try:
        seed_depot(db)
        seed_produits(db)
        seed_utilisateurs(db)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    print("\n=== Identifiants de démo ===")
    for u in UTILISATEURS:
        print(f"- {u['role']:<8} téléphone={u['telephone']}  mot de passe={u['mot_de_passe']}")
    print(f"- point de dépôt : {DEPOT['nom']} ({DEPOT['latitude']}, {DEPOT['longitude']})")
    print("Fin du seed.")


if __name__ == "__main__":
    main()
