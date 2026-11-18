# Carte-FH — Faisceaux Hertziens en France

Carte interactive permettant de visualiser et d’explorer les liaisons et supports **Faisceaux Hertziens (FH)** déployés en France à partir des données ouvertes publiées chaque mois par l’**ANFR** (Agence Nationale des Fréquences).

**Accéder à la carte en ligne :** https://julierose23.github.io/Carte-FH/

---

## Fonctionnalités

- **Filtrage par opérateur** avec code couleur dédié (Orange, SFR, Bouygues Telecom, Free Mobile, Autres/TDF).
- **Filtrage par bande de fréquence** (< 10 GHz, 11 - 15 GHz, 18 GHz, 23 - 26 GHz, 32 - 38 GHz, 70 - 80 GHz E-Band).
- **Filtrage géographique par région** : affichage des limites administratives et filtrage précis des pylônes et faisceaux à l’intérieur de la région sélectionnée.
- **Historique mensuel** : sélecteur d’archives permettant de comparer l’évolution du réseau d’un mois à l’autre.
- **Fiches détaillées des sites** : clic sur un pylône ou une liaison pour afficher les coordonnées, la hauteur, la date de mise en service, les fréquences en GHz et un lien direct vers **Cartoradio**.
- **Rendu adaptatif au zoom** : ajustement automatique de la taille des marqueurs et de l’épaisseur des liaisons selon le niveau de zoom.
- **Fonds de carte multiples et résilience** : choix entre **OpenStreetMap**, **Plan IGN** et **Satellite IGN** (Géoplateforme), avec bascule automatique vers le Plan IGN en cas d’indisponibilité d’OSM.

---

## Structure du dépôt

- `index.html` : Interface cartographique interactive (Leaflet)
- `generer_fh.py` : Script Python de traitement et conversion des données ANFR en GeoJSON
- `data/` : Archives mensuelles GeoJSON et contours des régions françaises
- `lib/` : Bibliothèque Leaflet hébergée en local (sans dépendance CDN externe)

---

## Source des données

- **Données radioélectriques :** Data.gouv.fr — ANFR (Observatoire 2G/3G/4G/5G et Faisceaux Hertziens), mises à jour mensuellement.
- **Fonds cartographiques :** Contributeurs OpenStreetMap et IGN Géoplateforme.
