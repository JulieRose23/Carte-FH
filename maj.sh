#!/data/data/com.termux/files/usr/bin/bash
set -e
cd ~/Carte-FH
git pull

# Liste tous les prefixes de date (ex: 202609, 202610...) tries par ordre chronologique
PREFIXES=$(ls ~/storage/downloads/202*.zip 2>/dev/null | xargs -n 1 basename | cut -c1-6 | sort -u || true)

if [ -z "$PREFIXES" ]; then
  echo "Aucune archive ANFR (202*.zip) trouvee dans Telechargements !"
  exit 1
fi

TRAITES=0

for P in $PREFIXES; do
  PAIR=$(ls ~/storage/downloads/${P}*.zip 2>/dev/null || true)
  COUNT=$(echo "$PAIR" | grep -c "\.zip" || true)

  if [ "$COUNT" -eq 2 ]; then
    ARCHIVE_DATE="${P:0:4}-${P:4:2}"
    echo "=== Traitement de l'archive $ARCHIVE_DATE (prefixe $P) ==="
    rm -f SUP_*.txt
    for Z in $PAIR; do
      echo "Extraction de : $Z"
      unzip -o "$Z" -d .
    done

    python generer_fh.py "$ARCHIVE_DATE"

    echo "Nettoyage des fichiers .txt et .zip pour $ARCHIVE_DATE..."
    rm -f SUP_*.txt
    rm -f ~/storage/downloads/${P}*.zip

    TRAITES=$((TRAITES + 1))
  else
    echo "Ignore $P : $COUNT fichier(s) trouve(s) au lieu de 2 (supports + emetteurs requis)."
  fi
done

if [ "$TRAITES" -eq 0 ]; then
  echo "Aucun mois complet n'a pu etre traite."
  exit 1
fi

git add data/
git commit -m "Ajout automatique de $TRAITES archive(s) ANFR (Metropole + DROM)"
git push

echo "Termine ! $TRAITES mois publie(s). La carte sera a jour dans 1 minute."
