# 🥤 Triad-Beverage-Delivery | ESSIVIVI-Sarl

> **Projet SAÉ : Programmation Distribuée (Architecture Microservices)**
> *Livraison intelligente. Expérience exceptionnelle.*

## 📝 Description du Projet
Ce projet est une application distribuée de livraison de boissons développée pour l'entreprise fictive **ESSIVIVI-Sarl**. L'objectif est de digitaliser le processus de vente, de dépôt et de livraison de boissons, tout en fournissant au gestionnaire un outil de pilotage (Business Intelligence) en temps réel.

L'application repose sur une **architecture en microservices** et utilise **FastAPI** (Python) pour le backend. Elle est développée dans le cadre de la SAÉ "Développer des applications communicantes".

## 🏗️ Architecture (Microservices)
Le système est divisé en 3 interfaces distinctes (et potentiellement 3 microservices backend) :

1.  **📱 Application Mobile Client :** Permet aux clients de consulter le catalogue, gérer un panier, valider la proximité GPS (Google Maps API) et débloquer une visite guidée 3D (fonctionnalité payante).
2.  **💻 Web App Gestionnaire :** Un tableau de bord (Dashboard) pour le responsable de ESSIVIVI-Sarl. Il permet de suivre les ventes, les performances des agents, et d'identifier les points de dépôt les plus rentables.
3.  **🚚 Application Mobile Agent Commercial :** Un outil terrain pour les commerciaux. Ils peuvent voir leur tournée, saisir une vente rapidement et capturer les coordonnées GPS du point de dépôt.

## ✨ Fonctionnalités Clés
- **Authentification sécurisée :** Connexion avec double authentification (2FA).
- **Géolocalisation :** Vérification de la distance client/dépôt via l'API Google Maps.
- **Dashboard Admin :** Visualisation des KPIs (Chiffre d'affaires, livraisons, top agents).
- **Expérience immersive :** Visite guidée à 360° (Visite 3D) déblocable pour 200 FCFA.
- **Saisie Terrain :** Formulaire optimisé pour les agents avec capture GPS.

## 🛠️ Stack Technique
- **Backend :** Python, FastAPI
- **Base de données :** [À définir : ex. Firebase Realtime DB / Azure DB / PostgreSQL]
- **Frontend (Maquette) :** HTML, Tailwind CSS, JavaScript
- **Outils :** VS Code, Git, GitHub

## 📂 Structure du Dépôt
```text
triad-beverage-delivery-microservices/
│
├── index.html                      # Maquette interactive (Prototype HTML/CSS/JS)
├── README.md                       # Documentation du projet
│
├── microservice-client/            # (À venir) Backend FastAPI pour l'app Client
├── microservice-manager/           # (À venir) Backend FastAPI pour le Dashboard
└── microservice-agent/             # (À venir) Backend FastAPI pour l'app Agent

🚀 Installation et Lancement (Prototype Actuel)

Puisque le projet est actuellement au stade de maquette interactive, voici comment le visualiser :

    Clonez ce dépôt :
    bash

    git clone https://github.com/Prosper397/triad-beverage-delivery-microservices.git

    Ouvrez le fichier index.html dans votre navigateur web (double-clic).

    Utilisez le menu de navigation en haut pour basculer entre les 3 interfaces (Client, Gestionnaire, Agent).

👥 Équipe du Projet

    [Prosper] - Chef de projet & Développeur

    [Nom Camarade 1] - Développeur

    [Nom Camarade 2] - Développeur

📅 Roadmap (Prochaines étapes)

    ☑

    Analyse du cahier des charges
    ☑

    Conception de la maquette interactive (UI/UX)
    □

    Initialisation des microservices FastAPI
    □

    Mise en place de la base de données Cloud
    □

    Intégration de l'API Google Maps
    □

    Implémentation de l'authentification 2FA
    □

    Tests et déploiement

Projet réalisé dans le cadre de la SAÉ "Programmation Distribuée" - 2026/2027.