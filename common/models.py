"""Modèles SQLAlchemy partagés par les 3 microservices."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, DateTime, Float, ForeignKey,
    Integer, Numeric, String, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateur"
    __table_args__ = (
        CheckConstraint("role in ('client', 'agent', 'manager')", name="ck_role"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    telephone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    mot_de_passe_hash: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[str] = mapped_column(String, nullable=False)
    deux_fa_actif: Mapped[bool] = mapped_column(Boolean, default=False)
    totp_secret: Mapped[str | None] = mapped_column(String)
    visite_3d_debloquee: Mapped[bool] = mapped_column(Boolean, default=False)
    cree_le: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    livraisons_agent: Mapped[list["Livraison"]] = relationship(
        back_populates="agent", foreign_keys="Livraison.agent_id"
    )
    commandes: Mapped[list["Livraison"]] = relationship(
        back_populates="client", foreign_keys="Livraison.client_id"
    )


class PointDepot(Base):
    __tablename__ = "point_depot"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    adresse: Mapped[str | None] = mapped_column(String)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    livraisons: Mapped[list["Livraison"]] = relationship(back_populates="point_depot")


class Produit(Base):
    __tablename__ = "produit"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    prix: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


class Livraison(Base):
    __tablename__ = "livraison"
    __table_args__ = (
        CheckConstraint(
            "statut in ('en_attente', 'en_cours', 'livree')", name="ck_statut"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    client_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id"))
    agent_id: Mapped[int | None] = mapped_column(ForeignKey("utilisateur.id"))
    client_telephone: Mapped[str] = mapped_column(String, nullable=False)
    point_depot_id: Mapped[int | None] = mapped_column(ForeignKey("point_depot.id"))
    statut: Mapped[str] = mapped_column(String, nullable=False, default="en_attente")
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    montant_percu: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    date_heure: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    agent: Mapped["Utilisateur | None"] = relationship(
        back_populates="livraisons_agent", foreign_keys=[agent_id]
    )
    client: Mapped["Utilisateur | None"] = relationship(
        back_populates="commandes", foreign_keys=[client_id]
    )
    point_depot: Mapped["PointDepot | None"] = relationship(back_populates="livraisons")
    lignes: Mapped[list["LigneLivraison"]] = relationship(
        back_populates="livraison", cascade="all, delete-orphan"
    )


class LigneLivraison(Base):
    __tablename__ = "ligne_livraison"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    livraison_id: Mapped[int] = mapped_column(
        ForeignKey("livraison.id", ondelete="CASCADE"), nullable=False
    )
    produit_id: Mapped[int] = mapped_column(ForeignKey("produit.id"), nullable=False)
    quantite: Mapped[int] = mapped_column(Integer, nullable=False)
    prix_unitaire: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    livraison: Mapped["Livraison"] = relationship(back_populates="lignes")
    produit: Mapped["Produit"] = relationship()
