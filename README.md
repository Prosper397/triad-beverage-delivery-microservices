# 🥤 Triad-Beverage-Delivery

### La livraison de boissons, pensée en microservices.

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-Microservices-009688?logo=fastapi&logoColor=white)
![Status](https://img.shields.io/badge/Statut-En%20d%C3%A9veloppement-orange)
![SAÉ](https://img.shields.io/badge/SA%C3%89-Programmation%20Distribu%C3%A9e-blue)

> Projet SAÉ **Programmation Distribuée** pour l'entreprise **ESSIVIVI-Sarl**.
> Trois profils, trois services, une seule plateforme : vendre, livrer, piloter.

---

## 🎯 Le problème

ESSIVIVI-Sarl livre des boissons à des bars et restaurants. Aujourd'hui, le gérant ne sait pas **qui vend quoi, où, et avec quelle rentabilité**.

**Notre réponse :** une plateforme où chaque vente est enregistrée avec sa position GPS, ses montants et son agent, et où le gérant voit tout en temps réel.

---

## 🏗️ Architecture

```text
                  ┌───────────────────────────┐
                  │    BASE DE DONNÉES CLOUD  │
                  └─────────────┬─────────────┘
                                │
      ┌─────────────────────────┼─────────────────────────┐
      │                         │                         │
┌─────▼──────────┐     ┌────────▼───────┐     ┌───────────▼────┐
│ microservice-  │     │ microservice-  │     │ microservice-  │
│    client      │     │    manager     │     │     agent      │
│ FastAPI :8001  │     │ FastAPI :8000  │     │ FastAPI :8002  │
└─────▲──────────┘     └────────▲───────┘     └───────────▲────┘
      │ HTTP/JSON               │ HTTP/JSON               │ HTTP/JSON
┌─────┴──────────┐     ┌────────┴───────┐     ┌───────────┴────┐
│  📱 App Client │     │ 💻 Dashboard   │     │ 🚚 App Agent   │
│                │     │  Gestionnaire  │     │   Commercial   │
└────────────────┘     └────────────────┘     └────────────────┘
```

| Service | Rôle | Port |
|---|---|---|
| `microservice-client` | Catalogue, panier, vérification de distance, visite 3D | 8001 |
| `microservice-manager` | Dashboard, KPIs, administration | 8000 |
| `microservice-agent` | Tournée du jour, saisie de vente, capture GPS | 8002 |

---

## ✨ Fonctionnalités clés

- 🔐 **Authentification 2FA** : connexion sécurisée avec code à 6 chiffres
- 📍 **Vérification de proximité** : la commande ne se valide que si le client est assez proche du point de dépôt (Google Maps API)
- 🧭 **Visite guidée 360°** : déblocable pour **200 FCFA**
- 📊 **Dashboard gestionnaire** : chiffre d'affaires, livraisons, meilleur agent, **point de dépôt le plus rentable**
- 🛰️ **Saisie terrain** : l'agent enregistre quantité, montant et position GPS en quelques secondes

---

## 🛠️ Stack technique

| Couche | Technologie |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Base de données | Cloud (Firebase / Azure DB / Amazon RDS, choix à valider) |
| Maquette | HTML, Tailwind CSS, JavaScript |
| Outils | VS Code, Git, GitHub |

---

## 🚀 Démarrage rapide

**1. Voir la maquette**

```bash
git clone https://github.com/Prosper397/triad-beverage-delivery-microservices.git
cd triad-beverage-delivery-microservices
```

Ouvrez `index.html` dans votre navigateur et naviguez entre les 3 interfaces.

**2. Lancer un microservice (exemple : Gestionnaire)**

```bash
cd microservice-manager
pip install fastapi uvicorn
uvicorn main:app --reload
```

- API : http://127.0.0.1:8000
- Documentation Swagger : http://127.0.0.1:8000/docs

---

## 📂 Structure du dépôt

```text
triad-beverage-delivery-microservices/
├── index.html               # Maquette interactive
├── README.md
├── LICENSE
├── microservice-client/     # API de l'app Client
├── microservice-manager/    # API du Dashboard
└── microservice-agent/      # API de l'app Agent
```

---

## 👥 L'équipe

| Membre | GitHub |
|---|---|
| **Prosper** | [@Prosper397](https://github.com/Prosper397) |
| **Peace** | [@TCHAZINON](https://github.com/TCHAZINON) |
| **Joanna** | [@Jo-dev-pop](https://github.com/Jo-dev-pop) |

---

## 🔀 Workflow Git

```text
main  ◄── Pull Request ◄── feature-xxx  (une branche par fonctionnalité)
```

1. On ne code **jamais** directement sur `main`
2. Une branche par fonctionnalité : `feature-client`, `feature-manager`, `feature-agent`
3. Pull Request relue par un coéquipier avant fusion

---

## 🗺️ Roadmap

- [x] Analyse du cahier des charges
- [x] Maquette interactive (UI/UX)
- [x] Structure des 3 microservices
- [ ] Modèles de données (Livraison, Agent, Client, Produit)
- [ ] Routes API Manager, Agent et Client
- [ ] Base de données cloud
- [ ] Authentification 2FA
- [ ] Intégration Google Maps API
- [ ] Connexion de la maquette à l'API
- [ ] Tests et déploiement

---

<p align="center">
  SAÉ Programmation Distribuée · 2026/2027 · Fait avec ☕ par l'équipe Triad
</p>
