# Carte-FH — Faisceaux Hertziens (ANFR)

Carte interactive des stations et liaisons Faisceaux Hertziens (FH) en **France métropolitaine, Corse et Outre-Mer (5 DROM)** à partir des données ouvertes de l'**ANFR**.

Accéder à la carte : https://julierose23.github.io/Carte-FH/

## Fonctionnalités

- **Territoires couverts** : France métropolitaine, Corse et 5 DROM (Guadeloupe 971, Martinique 972, Guyane 973, La Réunion 974, Mayotte 976).
- **Opérateurs (avec noms locaux)** :
  - Métropole & Corse : Orange, SFR, Bouygues Telecom, Free Mobile, Autres (TDF, etc.).
  - La Réunion & Mayotte : Orange, SRR (SFR), Telco OI (Free), Zeop / Autres.
  - Antilles & Guyane : Orange Caraïbe, Outremer Telecom (SFR), Free Caraïbe, Digicel / Dauphin / Autres.
- **Bandes de fréquence (GHz)** : < 10 GHz, 11–15 GHz, 18 GHz, 23–26 GHz, 32–38 GHz, 70–80 GHz.
- **Historique mensuel** : sélection de l'archive ANFR par mois (`data/archives.json`).
- **Liaisons point-à-point** : appariement géométrique par azimut réciproque et contrôle d'occultation.

## Pipeline & Mise à jour

- `index.html` : interface Leaflet + OpenStreetMap.
- `generer_fh.py` : traitement des tables ANFR et génération des GeoJSON dans `data/AAAA-MM/`.
- `maj.sh` : automatisation Termux (extraction des `202*.zip`, détection de la date du ZIP, génération et `git push`).

Source : données ouvertes ANFR sur data.gouv.fr (Licence Ouverte).
