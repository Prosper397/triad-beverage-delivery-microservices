<h1>
  <img src="docs/icons/cup-soda.svg" height="34" align="top">
  Triad-Beverage-Delivery
</h1>

Plateforme de livraison de boissons en architecture microservices, réalisée pour le cours de Programmation Distribuée (SAÉ), à partir du cahier des charges de l'entreprise ESSIVIVI-Sarl.

<p>
  <img src="docs/icons/python.svg" alt="Python" title="Python" height="30">&nbsp;
  <img src="docs/icons/fastapi.svg" alt="FastAPI" title="FastAPI" height="30">&nbsp;
  <img src="docs/icons/postgresql.svg" alt="PostgreSQL" title="PostgreSQL" height="30">&nbsp;
  <img src="docs/icons/supabase.svg" alt="Supabase" title="Supabase" height="30">&nbsp;
  <img src="docs/icons/sqlalchemy.svg" alt="SQLAlchemy" title="SQLAlchemy" height="30">&nbsp;
  <img src="docs/icons/html5.svg" alt="HTML5" title="HTML5" height="30">&nbsp;
  <img src="docs/icons/tailwindcss.svg" alt="Tailwind CSS" title="Tailwind CSS" height="30">&nbsp;
  <img src="docs/icons/javascript.svg" alt="JavaScript" title="JavaScript" height="30">&nbsp;
  <img src="docs/icons/git.svg" alt="Git" title="Git" height="30">
</p>

Le projet est en cours de construction : la maquette est terminée, le backend FastAPI est en cours de mise en place.

## <img src="docs/icons/target.svg" height="24" align="top"> Le besoin

ESSIVIVI-Sarl livre des boissons à des bars et des restaurants. Le cahier des charges demande trois choses : que les agents commerciaux enregistrent leurs ventes sur le terrain, avec la position GPS du point de dépôt ; que les clients puissent commander depuis leur téléphone ; et que le gérant ait une vue d'ensemble de l'activité (ventes, performance des agents, points de dépôt les plus rentables).

## <img src="docs/icons/smartphone.svg" height="24" align="top"> Les trois interfaces

| | Interface | Utilisateur | Ce qu'elle permet |
|---|---|---|---|
| <img src="docs/icons/shopping-bag.svg" height="22"> | Client | Le client final | Parcourir le catalogue, remplir un panier, valider une commande si l'on est assez près du point de dépôt, débloquer la visite 360° (200 FCFA) |
| <img src="docs/icons/truck.svg" height="22"> | Agent | Le commercial | Voir sa tournée, saisir une vente, capturer la position GPS du point de dépôt |
| <img src="docs/icons/layout-dashboard.svg" height="22"> | Gestionnaire | Le responsable | Suivre le chiffre d'affaires, les livraisons, les agents, le point de dépôt le plus rentable |

## <img src="docs/icons/network.svg" height="24" align="top"> Architecture

```text
                   Base PostgreSQL (Supabase)
                              |
          +-------------------+-------------------+
          |                   |                   |
  microservice-client  microservice-manager  microservice-agent
     FastAPI :8001        FastAPI :8000        FastAPI :8002
          ^                   ^                   ^
          | HTTP/JSON         | HTTP/JSON         | HTTP/JSON
          |                   | + WebSocket       |
    Interface client   Dashboard gestionnaire  Interface agent
```

Chaque service a ses propres routes et son propre port. Les trois partagent une même base de données et un paquet commun (`common/`) qui contient les modèles : c'est un choix de simplicité, pas une séparation stricte des données.

## <img src="docs/icons/wrench.svg" height="24" align="top"> Choix techniques

| Sujet | Choix | Pourquoi |
|---|---|---|
| Backend | FastAPI | Imposé par le sujet, documentation Swagger générée automatiquement |
| Base de données | PostgreSQL hébergée sur Supabase | Nos données sont relationnelles et le dashboard repose sur des agrégations (SUM, GROUP BY) |
| Accès aux données | SQLAlchemy | Les modèles sont écrits une fois et partagés entre les services |
| Authentification | JWT et 2FA par code à 6 chiffres (TOTP, via pyotp) | Compatible avec les applications d'authentification, sans dépendre d'un service SMS payant |
| Vérification de distance | Formule de Haversine côté serveur, carte Google Maps côté interface | Le calcul reste fiable et testable, la carte sert à l'affichage |
| Temps réel | WebSocket | Les nouvelles ventes apparaissent sur le dashboard sans recharger la page |
| Paiement de la visite 3D | Simulé | Le cahier des charges ne précise aucune passerelle de paiement |
| Interfaces | Pages web responsives au format mobile (HTML, Tailwind, JavaScript) | Dans la continuité de la maquette, avec géolocalisation du navigateur |

## <img src="docs/icons/panels-top-left.svg" height="24" align="top"> La maquette

Le fichier `index.html` est un prototype interactif sans backend : trois boutons en haut de page permettent de passer d'une interface à l'autre. Les données sont fictives.

- **Client** : catalogue (Coca-Cola, Sprite, jus d'orange, bière locale), panier avec total, message de distance (2,5 km, validation bloquée tant que l'on est à plus de 1 km), bouton de visite 360° à 200 FCFA, connexion 2FA dans une fenêtre dédiée (code de démonstration : `123456`).
- **Gestionnaire** : menu latéral (tableau de bord, clients, agents, stocks et boissons, paramètres), chiffre d'affaires, graphique des ventes sur 7 jours, répartition des boissons, point de dépôt le plus rentable, tableau des dernières transactions (agent, téléphone, adresse, GPS, quantité, montant, heure).
- **Agent** : ventes et livraisons du jour, objectif quotidien, liste des livraisons à faire, et un bouton « + » qui ouvre le formulaire de saisie d'une vente avec capture de la position GPS (géolocalisation du navigateur, position simulée en secours).

Charte : vert profond `#145c45`, orange `#f28c28`, fond crème `#f7f5ef`, polices Inter et Poppins, Tailwind CSS et Font Awesome chargés par CDN.

## <img src="docs/icons/folder-tree.svg" height="24" align="top"> Structure du dépôt

```text
triad-beverage-delivery-microservices/
  index.html               maquette interactive
  database/
    schema.sql             schéma de la base (à exécuter dans Supabase)
  common/
    database.py            connexion à la base
    models.py              modèles SQLAlchemy partagés
  microservice-client/     API de l'interface client
  microservice-manager/    API du dashboard
  microservice-agent/      API de l'interface agent
  docs/icons/              icônes utilisées dans ce README
  .env.example             modèle de configuration
  requirements.txt
```

## <img src="docs/icons/terminal.svg" height="24" align="top"> Lancer le projet

Voir la maquette : cloner le dépôt puis ouvrir `index.html` dans un navigateur.

```bash
git clone https://github.com/Prosper397/triad-beverage-delivery-microservices.git
cd triad-beverage-delivery-microservices
```

Préparer la base :

1. Créer un projet sur Supabase.
2. Coller le contenu de `database/schema.sql` dans le SQL Editor et l'exécuter.
3. Copier `.env.example` en `.env` et renseigner `DATABASE_URL` avec la chaîne de connexion du projet.

Le fichier `.env` contient des secrets : il ne doit jamais être commité.

Lancer un service (exemple : le gestionnaire), depuis la racine du dépôt :

```bash
pip install -r requirements.txt
PYTHONPATH=. uvicorn main:app --app-dir microservice-manager --port 8000 --reload
```

L'API répond sur http://127.0.0.1:8000 et la documentation sur http://127.0.0.1:8000/docs.

## <img src="docs/icons/users.svg" height="24" align="top"> Équipe

| Membre | GitHub |
|---|---|
| Prosper | [Prosper397](https://github.com/Prosper397) |
| Peace | [TCHAZINON](https://github.com/TCHAZINON) |
| Joanna | [Jo-dev-pop](https://github.com/Jo-dev-pop) |

## <img src="docs/icons/git-branch.svg" height="24" align="top"> Organisation du travail

La branche `main` reste stable. Chaque fonctionnalité se développe sur sa propre branche (`feature-...`) et passe par une Pull Request relue par un autre membre de l'équipe avant d'être fusionnée.

## <img src="docs/icons/list-checks.svg" height="24" align="top"> Avancement

- [x] Analyse du cahier des charges
- [x] Maquette interactive
- [x] Structure des trois microservices
- [x] Schéma de la base de données
- [ ] Routes du gestionnaire (ventes, agents, points de dépôt rentables)
- [ ] Routes de l'agent (saisie de vente avec GPS)
- [ ] Routes du client (catalogue, panier, vérification de distance)
- [ ] Authentification et 2FA
- [ ] Intégration de Google Maps
- [ ] Dashboard en temps réel (WebSocket)
- [ ] Connexion de la maquette aux API
- [ ] Tests et déploiement

Projet réalisé dans le cadre de la SAÉ Programmation Distribuée, année 2026-2027.

---

Icônes : [Lucide](https://lucide.dev) (licence ISC) et [Simple Icons](https://simpleicons.org) (CC0).
