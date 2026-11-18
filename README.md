# Carte-FH - Faisceaux Hertziens en France

Carte interactive permettant de visualiser et d explorer les liaisons et supports **Faisceaux Hertziens (FH)** deployes en France a partir des donnees ouvertes publiees chaque mois par l **ANFR** (Agence Nationale des Frequences).

**Acceder a la carte en ligne :** [https://julierose23.github.io/Carte-FH/](https://julierose23.github.io/Carte-FH/)

---

## Fonctionnalites

- **Filtrage par operateur** avec code couleur dedie (Orange, SFR, Bouygues Telecom, Free Mobile, Autres/TDF).
- **Filtrage par bande de frequence** (< 10 GHz, 11 - 15 GHz, 18 GHz, 23 - 26 GHz, 32 - 38 GHz, 70 - 80 GHz E-Band).
- **Filtrage geographique par region** : affichage des limites administratives et filtrage precis des pylones et faisceaux a l interieur de la region selectionnee.
- **Historique mensuel** : selecteur d archives permettant de comparer l evolution du reseau d un mois a l autre.
- **Fiches detaillees des sites** : clic sur un pylone ou une liaison pour afficher les coordonnees, la hauteur, la date de mise en service, les frequences en GHz et un lien direct vers **Cartoradio**.
- **Rendu adaptatif au zoom** : ajustement automatique de la taille des marqueurs et de l epaisseur des liaisons selon le niveau de zoom.
- **Fonds de carte multiples et resilience** : choix entre **OpenStreetMap**, **Plan IGN** et **Satellite IGN** (Geoplateforme), avec bascule automatique vers le Plan IGN en cas d indisponibilite d OSM.

---

## Structure du depot

- `index.html` : Interface cartographique interactive (Leaflet)
- `generer_fh.py` : Script Python de traitement et conversion des donnees ANFR en GeoJSON
- `data/` : Archives mensuelles GeoJSON et contours des regions francaises
- `lib/` : Bibliotheque Leaflet hebergee en local (sans dependance CDN externe)

---

## Source des donnees

- **Donnees radioelectriques :** Data.gouv.fr - ANFR (Observatoire 2G/3G/4G/5G et Faisceaux Hertziens), mises a jour mensuellement.
- **Fonds cartographiques :** Contributeurs OpenStreetMap et IGN Geoplateforme.
