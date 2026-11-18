import json
import traceback
from datetime import datetime
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.spatial import cKDTree

DOSSIER_ANFR = Path(__file__).resolve().parent
DOSSIER_DATA = DOSSIER_ANFR / "data"
DOSSIER_LOG = DOSSIER_ANFR / "log"
TOLERANCE_AZIMUT = 3.5
DISTANCE_MAX_KM = 120.0
RAYON_OCCULTATION_KM = 0.08

MOIS_FR = {
    "01": "Janvier", "02": "Février", "03": "Mars", "04": "Avril",
    "05": "Mai", "06": "Juin", "07": "Juillet", "08": "Août",
    "09": "Septembre", "10": "Octobre", "11": "Novembre", "12": "Décembre"
}


def ecrire_log_erreur(exc):
    DOSSIER_LOG.mkdir(parents=True, exist_ok=True)
    horodatage = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    fichier_log = DOSSIER_LOG / f"erreur_{horodatage}.txt"
    with open(fichier_log, "w", encoding="utf-8") as f:
        f.write(f"Erreur survenue le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        f.write(traceback.format_exc())
    print(f"\n[LOG] Le detail de l'erreur a ete enregistre dans : {fichier_log}")


def formater_label_archive(archive_id):
    annee, mois = archive_id.split("-")
    return f"{MOIS_FR.get(mois, mois)} {annee}"


def detecter_archive_depuis_stations(stations):
    dates = pd.to_datetime(stations["DTE_MODIF"], format="%d/%m/%Y", errors="coerce").dropna()
    if not dates.empty:
        d_max = dates.max()
        return f"{d_max.year}-{d_max.month:02d}"
    return datetime.now().strftime("%Y-%m")


def choisir_archive(suggestion_id):
    suggestion_label = formater_label_archive(suggestion_id)
    print(f"\n[ARCHIVE] Mois detecte dans les fichiers ANFR : {suggestion_id} ({suggestion_label})")
    saisie = input("Appuyez sur ENTREE pour confirmer, ou tapez une autre date (AAAA-MM ou AAAAMM) : ").strip()
    if not saisie:
        return suggestion_id, suggestion_label
    if len(saisie) == 6 and saisie.isdigit():
        saisie = f"{saisie[:4]}-{saisie[4:]}"
    if len(saisie) == 7 and saisie[4] == "-" and saisie[:4].isdigit() and saisie[5:].isdigit():
        return saisie, formater_label_archive(saisie)
    print(f"Format non reconnu, utilisation de {suggestion_id}.")
    return suggestion_id, suggestion_label


def nettoyer_texte(val):
    if pd.isna(val):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def dms_to_dd_vec(deg, minute, sec, orientation):
    dd = deg.astype(float) + minute.astype(float) / 60.0 + sec.astype(float) / 3600.0
    signe = np.where(orientation.astype(str).str.strip().str.upper().isin(["S", "W", "O"]), -1.0, 1.0)
    return dd * signe


def lire_table_anfr(nom_fichier, colonnes=None):
    chemin = DOSSIER_ANFR / nom_fichier
    if not chemin.exists():
        raise FileNotFoundError(f"Fichier manquant : {nom_fichier}")
    try:
        return pd.read_csv(chemin, sep=";", encoding="utf-8", usecols=colonnes, low_memory=False)
    except UnicodeDecodeError:
        return pd.read_csv(chemin, sep=";", encoding="latin1", usecols=colonnes, low_memory=False)


def classer_operateur(nom):
    nom = str(nom).upper()
    if "ORANGE" in nom:
        return "orange"
    if "SFR" in nom or "SRR" in nom or "OUTREMER TELECOM" in nom:
        return "sfr"
    if "BOUYGUES" in nom:
        return "bouygues"
    if "FREE" in nom or "TELCO OI" in nom:
        return "free"
    return "autres"


def classer_bande_ghz(ghz):
    if ghz <= 0:
        return "inconnue"
    if ghz < 10:
        return "moins_10"
    if ghz < 16:
        return "11_15"
    if ghz < 20:
        return "18"
    if ghz < 28:
        return "23_26"
    if ghz < 42:
        return "32_38"
    return "70_80"


def mettre_a_jour_index_archives(archive_id, archive_label):
    fichier_index = DOSSIER_DATA / "archives.json"
    if fichier_index.exists():
        with open(fichier_index, "r", encoding="utf-8") as f:
            archives = json.load(f)
    else:
        archives = []

    if not any(a["id"] == archive_id for a in archives):
        archives.append({"id": archive_id, "label": archive_label})
        archives.sort(key=lambda x: x["id"], reverse=True)

    with open(fichier_index, "w", encoding="utf-8") as f:
        json.dump(archives, f, indent=2, ensure_ascii=False)


def filtrer_saute_mouton(liens_candidats, sites_coords_par_bande):
    liens_valides = []
    for lien in liens_candidats:
        b = lien["b"]
        pts = sites_coords_par_bande.get(b)
        if pts is None or len(pts) < 3:
            liens_valides.append(lien)
            continue

        lat1, lon1 = lien["lat1"], lien["lon1"]
        lat2, lon2 = lien["lat2"], lien["lon2"]
        cos_lat = np.cos(np.radians((lat1 + lat2) * 0.5))

        bx = (lon2 - lon1) * 111.32 * cos_lat
        by = (lat2 - lat1) * 110.57
        ab2 = bx * bx + by * by
        if ab2 == 0:
            continue

        px = (pts[:, 1] - lon1) * 111.32 * cos_lat
        py = (pts[:, 0] - lat1) * 110.57

        t = (px * bx + py * by) / ab2
        entre_ab = (t > 0.05) & (t < 0.95)
        if not np.any(entre_ab):
            liens_valides.append(lien)
            continue

        proj_x = t[entre_ab] * bx
        proj_y = t[entre_ab] * by
        dist_perp = np.hypot(px[entre_ab] - proj_x, py[entre_ab] - proj_y)

        if np.any(dist_perp < RAYON_OCCULTATION_KM):
            continue

        liens_valides.append(lien)
    return liens_valides


def main():
    print("1. Chargement des tables ANFR...")
    stations = lire_table_anfr(
        "SUP_STATION.txt",
        ["STA_NM_ANFR", "ADM_ID", "DTE_IMPLANTATION", "DTE_MODIF", "DTE_EN_SERVICE"]
    )

    suggestion_id = detecter_archive_depuis_stations(stations)
    archive_id, archive_label = choisir_archive(suggestion_id)

    dossier_archive = DOSSIER_DATA / archive_id
    dossier_archive.mkdir(parents=True, exist_ok=True)
    print(f"   -> Generation pour l'archive : {archive_label} ({archive_id})")

    supports = lire_table_anfr(
        "SUP_SUPPORT.txt",
        [
            "SUP_ID", "COR_NB_DG_LAT", "COR_NB_MN_LAT", "COR_NB_SC_LAT", "COR_CD_NS_LAT",
            "COR_NB_DG_LON", "COR_NB_MN_LON", "COR_NB_SC_LON", "COR_CD_EW_LON",
            "SUP_NM_HAUT", "ADR_LB_LIEU", "ADR_LB_ADD1", "ADR_NM_CP"
        ]
    )
    emetteurs = lire_table_anfr("SUP_EMETTEUR.txt", ["EMR_ID", "STA_NM_ANFR", "AER_ID", "EMR_LB_SYSTEME"])
    antennes = lire_table_anfr("SUP_ANTENNE.txt", ["AER_ID", "SUP_ID", "AER_NB_AZIMUT", "AER_NB_ALT_BAS"])
    exploitants = lire_table_anfr("SUP_EXPLOITANT.txt", ["ADM_ID", "ADM_LB_NOM"])
    bandes = lire_table_anfr("SUP_BANDE.txt", ["EMR_ID", "BAN_NB_F_DEB", "BAN_FG_UNITE"])

    print("2. Conversion des frequences en GHz et filtrage FH...")
    bandes = bandes.dropna(subset=["BAN_NB_F_DEB"]).drop_duplicates(subset=["EMR_ID"]).copy()
    f_val = pd.to_numeric(bandes["BAN_NB_F_DEB"].astype(str).str.replace(",", "."), errors="coerce").fillna(0.0)
    unite = bandes["BAN_FG_UNITE"].astype(str).str.strip().str.upper()
    bandes["freq_ghz"] = np.where(
        unite == "G", f_val,
        np.where(unite == "K", f_val / 1_000_000.0, f_val / 1000.0)
    )

    em_fh = emetteurs[emetteurs["EMR_LB_SYSTEME"].str.startswith("FH", na=False)].copy()

    df = em_fh.merge(stations, on="STA_NM_ANFR", how="inner")
    df = df.merge(exploitants, on="ADM_ID", how="left")
    df = df.merge(bandes[["EMR_ID", "freq_ghz"]], on="EMR_ID", how="left")
    df = df.merge(antennes, on="AER_ID", how="inner")
    df = df.merge(supports, on="SUP_ID", how="inner")

    df = df.dropna(subset=["AER_NB_AZIMUT", "COR_NB_DG_LAT", "COR_NB_DG_LON"])
    df["azimut"] = pd.to_numeric(df["AER_NB_AZIMUT"].astype(str).str.replace(",", "."), errors="coerce")
    df = df.dropna(subset=["azimut"])

    df["lat"] = dms_to_dd_vec(df["COR_NB_DG_LAT"], df["COR_NB_MN_LAT"], df["COR_NB_SC_LAT"], df["COR_CD_NS_LAT"])
    df["lon"] = dms_to_dd_vec(df["COR_NB_DG_LON"], df["COR_NB_MN_LON"], df["COR_NB_SC_LON"], df["COR_CD_EW_LON"])

    in_metro = (df["lat"] >= 41.0) & (df["lat"] <= 51.5) & (df["lon"] >= -5.5) & (df["lon"] <= 10.0)
    in_gua = (df["lat"] >= 15.7) & (df["lat"] <= 16.6) & (df["lon"] >= -61.9) & (df["lon"] <= -60.9)
    in_mar = (df["lat"] >= 14.3) & (df["lat"] <= 15.0) & (df["lon"] >= -61.3) & (df["lon"] <= -60.7)
    in_guy = (df["lat"] >= 2.0) & (df["lat"] <= 6.0) & (df["lon"] >= -54.8) & (df["lon"] <= -51.5)
    in_reu = (df["lat"] >= -21.5) & (df["lat"] <= -20.8) & (df["lon"] >= 55.1) & (df["lon"] <= 56.0)
    in_may = (df["lat"] >= -13.1) & (df["lat"] <= -12.5) & (df["lon"] >= 44.9) & (df["lon"] <= 45.4)
    df = df[in_metro | in_gua | in_mar | in_guy | in_reu | in_may].copy()

    df["fai"] = df["ADM_LB_NOM"].apply(classer_operateur)
    df["freq_ghz"] = df["freq_ghz"].fillna(0.0)
    df = df.drop_duplicates(subset=["EMR_ID"]).reset_index(drop=True)

    print("3. Appairage geometrique operateur par operateur (anti-superposition + portee par bande)...")
    rayon_recherche_rad = DISTANCE_MAX_KM / 6371.0

    for fai in ["orange", "sfr", "bouygues", "free", "autres"]:
        sub = df[df["fai"] == fai].reset_index(drop=True)
        liens_candidats = []
        emetteurs_utilises = set()
        paires_vues = set()

        if len(sub) > 1:
            coords_rad = np.radians(sub[["lat", "lon"]].values)
            tree = cKDTree(coords_rad)
            paires = tree.query_pairs(r=rayon_recherche_rad, output_type="ndarray")

            if len(paires) > 0:
                idx_i = paires[:, 0]
                idx_j = paires[:, 1]

                sup_ids = sub["SUP_ID"].values
                emr_ids = sub["EMR_ID"].values
                freqs = sub["freq_ghz"].values

                masque = (sup_ids[idx_i] != sup_ids[idx_j]) & (np.abs(freqs[idx_i] - freqs[idx_j]) <= 12.0)
                idx_i = idx_i[masque]
                idx_j = idx_j[masque]

                lats = sub["lat"].values
                lons = sub["lon"].values
                azimuts = sub["azimut"].values

                phi1 = np.radians(lats[idx_i])
                phi2 = np.radians(lats[idx_j])
                dlon = np.radians(lons[idx_j] - lons[idx_i])

                y = np.sin(dlon) * np.cos(phi2)
                x = np.cos(phi1) * np.sin(phi2) - np.sin(phi1) * np.cos(phi2) * np.cos(dlon)
                az_i_vers_j = (np.degrees(np.arctan2(y, x)) + 360.0) % 360.0

                diff1 = np.abs(azimuts[idx_i] - az_i_vers_j) % 360.0
                diff1 = np.where(diff1 > 180.0, 360.0 - diff1, diff1)

                az_j_vers_i = (az_i_vers_j + 180.0) % 360.0
                diff2 = np.abs(azimuts[idx_j] - az_j_vers_i) % 360.0
                diff2 = np.where(diff2 > 180.0, 360.0 - diff2, diff2)

                masque_az = (diff1 <= TOLERANCE_AZIMUT) & (diff2 <= TOLERANCE_AZIMUT)
                idx_i = idx_i[masque_az]
                idx_j = idx_j[masque_az]

                phi1 = np.radians(lats[idx_i])
                phi2 = np.radians(lats[idx_j])
                dphi = phi2 - phi1
                dlambda = np.radians(lons[idx_j] - lons[idx_i])
                a = np.sin(dphi / 2.0) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2.0) ** 2
                distances = np.round(2.0 * 6371.0 * np.arctan2(np.sqrt(a), np.sqrt(1.0 - a)), 2)

                # Portee maximale realiste selon la bande de frequence
                f_moy = (freqs[idx_i] + freqs[idx_j]) * 0.5
                dist_max_bande = np.where(
                    f_moy >= 60.0, 10.0,           # 70-80 GHz (E-Band) : max 10 km
                    np.where(f_moy >= 30.0, 22.0,  # 32-38 GHz : max 22 km
                    np.where(f_moy >= 20.0, 40.0,  # 23-26 GHz : max 40 km
                    DISTANCE_MAX_KM))              # <= 18 GHz : jusqu'a 120 km
                )
                masque_dist = ((np.abs(freqs[idx_i] - freqs[idx_j]) <= 3.0) | (distances <= 10.0)) & (distances <= dist_max_bande)
                idx_i = idx_i[masque_dist]
                idx_j = idx_j[masque_dist]
                distances = distances[masque_dist]

                score_align = diff1[masque_az][masque_dist] + diff2[masque_az][masque_dist]
                ordre = np.argsort(score_align)

                hauteurs_ant = pd.to_numeric(sub["AER_NB_ALT_BAS"].astype(str).str.replace(",", "."), errors="coerce").fillna(0).values
                hauteurs_sup = pd.to_numeric(sub["SUP_NM_HAUT"].astype(str).str.replace(",", "."), errors="coerce").fillna(0).values
                sta_nums = [nettoyer_texte(x) for x in sub["STA_NM_ANFR"].values]
                dtes_imp = [nettoyer_texte(x) for x in sub["DTE_IMPLANTATION"].values]
                dtes_mod = [nettoyer_texte(x) for x in sub["DTE_MODIF"].values]
                dtes_mes = [nettoyer_texte(x) for x in sub["DTE_EN_SERVICE"].values]
                lieux = [nettoyer_texte(x) for x in sub["ADR_LB_LIEU"].values]
                adrs = [nettoyer_texte(x) for x in sub["ADR_LB_ADD1"].values]
                cps = [nettoyer_texte(x).replace(".0", "") for x in sub["ADR_NM_CP"].values]

                def formater_adresse(idx):
                    morceaux = [m for m in (lieux[idx], adrs[idx], cps[idx]) if m]
                    return ", ".join(morceaux) if morceaux else "Adresse non renseignée"

                sites_coords_par_bande = {}

                for pos in ordre:
                    i = int(idx_i[pos])
                    j = int(idx_j[pos])

                    emr_i = int(emr_ids[i])
                    emr_j = int(emr_ids[j])

                    if emr_i in emetteurs_utilises or emr_j in emetteurs_utilises:
                        continue

                    f_ref = float(freqs[i]) if freqs[i] > 0 else float(freqs[j])
                    bande_cat = classer_bande_ghz(f_ref)

                    cle = (min(emr_i, emr_j), max(emr_i, emr_j))
                    if cle in paires_vues:
                        continue

                    emetteurs_utilises.add(emr_i)
                    emetteurs_utilises.add(emr_j)
                    paires_vues.add(cle)

                    sites_coords_par_bande.setdefault(bande_cat, set()).add((float(lats[i]), float(lons[i])))
                    sites_coords_par_bande[bande_cat].add((float(lats[j]), float(lons[j])))

                    liens_candidats.append({
                        "lat1": float(lats[i]), "lon1": float(lons[i]),
                        "lat2": float(lats[j]), "lon2": float(lons[j]),
                        "f": round(f_ref, 1) if f_ref > 0 else "?",
                        "b": bande_cat,
                        "d": float(distances[pos]),
                        "az1": round(float(azimuts[i]), 1),
                        "az2": round(float(azimuts[j]), 1),
                        "h": f"{hauteurs_ant[i]}m / {hauteurs_ant[j]}m",
                        "s1": int(sup_ids[i]), "s2": int(sup_ids[j]),
                        "hs1": float(hauteurs_sup[i]), "hs2": float(hauteurs_sup[j]),
                        "sta1": sta_nums[i], "sta2": sta_nums[j],
                        "di1": dtes_imp[i] or "N/C", "di2": dtes_imp[j] or "N/C",
                        "dm1": dtes_mod[i] or "N/C", "dm2": dtes_mod[j] or "N/C",
                        "ds1": dtes_mes[i] or "N/C", "ds2": dtes_mes[j] or "N/C",
                        "adr1": formater_adresse(i), "adr2": formater_adresse(j),
                    })

                sites_np = {b: np.array(list(pts)) for b, pts in sites_coords_par_bande.items()}
                liens_candidats = filtrer_saute_mouton(liens_candidats, sites_np)

        features = []
        sites = {}

        for l in liens_candidats:
            for sid, cible, az_local, lat, lon, adr, hs, sta, di, dm, ds in (
                (l["s1"], l["s2"], l["az1"], l["lat1"], l["lon1"], l["adr1"], l["hs1"], l["sta1"], l["di1"], l["dm1"], l["ds1"]),
                (l["s2"], l["s1"], l["az2"], l["lat2"], l["lon2"], l["adr2"], l["hs2"], l["sta2"], l["di2"], l["dm2"], l["ds2"]),
            ):
                if sid not in sites:
                    sites[sid] = {
                        "lat": round(lat, 5), "lon": round(lon, 5),
                        "adr": adr, "hs": hs, "sta": sta,
                        "di": di, "dm": dm, "ds": ds,
                        "bandes": set(), "fhs": []
                    }
                sites[sid]["bandes"].add(l["b"])
                sites[sid]["fhs"].append({
                    "az": az_local,
                    "to": cible,
                    "f": l["f"],
                    "d": l["d"],
                    "b": l["b"]
                })

            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": [
                        [round(l["lon1"], 5), round(l["lat1"], 5)],
                        [round(l["lon2"], 5), round(l["lat2"], 5)],
                    ],
                },
                "properties": {
                    "kind": "link",
                    "op": fai,
                    "f": l["f"],
                    "b": l["b"],
                    "d": l["d"],
                    "az": l["az1"],
                    "h": l["h"],
                    "s1": l["s1"],
                    "s2": l["s2"],
                    "ds1": l["ds1"],
                    "ds2": l["ds2"],
                },
            })

        nb_liens = len(features)
        for sid, info in sites.items():
            fhs_tries = sorted(info["fhs"], key=lambda x: x["az"])
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [info["lon"], info["lat"]],
                },
                "properties": {
                    "kind": "site",
                    "op": fai,
                    "sid": sid,
                    "adr": info["adr"],
                    "hs": info["hs"],
                    "sta": info["sta"],
                    "di": info["di"],
                    "dm": info["dm"],
                    "ds": info["ds"],
                    "n": len(fhs_tries),
                    "bs": list(info["bandes"]),
                    "fhs": fhs_tries,
                },
            })

        geojson = {"type": "FeatureCollection", "features": features}
        chemin = dossier_archive / f"fh_{fai}.geojson"
        with open(chemin, "w", encoding="utf-8") as f:
            json.dump(geojson, f, separators=(",", ":"), ensure_ascii=False)
        print(f"   -> {chemin.name} genere ({nb_liens} liaisons, {len(sites)} sites)")

    mettre_a_jour_index_archives(archive_id, archive_label)
    print("4. Index archives.json mis a jour.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        ecrire_log_erreur(e)
        raise