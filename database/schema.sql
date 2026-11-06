-- Triad-Beverage-Delivery : schéma PostgreSQL (compatible Supabase)
-- À coller dans Supabase > SQL Editor > Run.
-- Pour repartir de zéro, décommenter la ligne suivante :
-- drop table if exists ligne_livraison, livraison, produit, point_depot, utilisateur cascade;

create table if not exists utilisateur (
    id                  bigint generated always as identity primary key,
    nom                 text        not null,
    telephone           text        not null unique,
    mot_de_passe_hash   text        not null,
    role                text        not null check (role in ('client', 'agent', 'manager')),
    deux_fa_actif       boolean     not null default false,
    totp_secret         text,                          -- secret du code à 6 chiffres (2FA)
    visite_3d_debloquee boolean     not null default false,
    cree_le             timestamptz not null default now()
);

create table if not exists point_depot (
    id        bigint generated always as identity primary key,
    nom       text             not null,
    adresse   text,
    latitude  double precision not null,
    longitude double precision not null
);

create table if not exists produit (
    id   bigint generated always as identity primary key,
    nom  text           not null,
    type text           not null,          -- biere, jus, soda...
    prix numeric(12, 2) not null check (prix >= 0)
);

-- Une livraison commence comme commande du client (en_attente),
-- puis un agent la prend en charge (en_cours) et la livre (livree).
create table if not exists livraison (
    id               bigint generated always as identity primary key,
    client_id        bigint           references utilisateur(id),
    agent_id         bigint           references utilisateur(id),
    client_telephone text             not null,
    point_depot_id   bigint           references point_depot(id),
    statut           text             not null default 'en_attente'
                                      check (statut in ('en_attente', 'en_cours', 'livree')),
    latitude         double precision,             -- GPS capturé par l'agent à la livraison
    longitude        double precision,
    montant_percu    numeric(12, 2)   not null default 0 check (montant_percu >= 0),
    date_heure       timestamptz      not null default now()
);

create table if not exists ligne_livraison (
    id            bigint generated always as identity primary key,
    livraison_id  bigint           not null references livraison(id) on delete cascade,
    produit_id    bigint           not null references produit(id),
    quantite      integer          not null check (quantite > 0),
    prix_unitaire numeric(12, 2)   not null check (prix_unitaire >= 0)
);

create index if not exists idx_livraison_agent  on livraison(agent_id);
create index if not exists idx_livraison_client on livraison(client_id);
create index if not exists idx_livraison_depot  on livraison(point_depot_id);
create index if not exists idx_livraison_statut on livraison(statut);
