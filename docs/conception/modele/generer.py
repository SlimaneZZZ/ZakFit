"""Génère, depuis modele.py : dictionnaire, MCD et MLD (Markdown et draw.io), script MariaDB.

Usage, depuis docs/conception :  python3 -I modele/generer.py
Les données de référence viennent de donnees/aliments.csv, donnees/portions.csv
et du tableau des activités de 02-formules.md (section 7).
"""
import csv
import os
import re
import sys
import uuid
from xml.sax.saxutils import escape

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
import modele as M  # noqa: E402

RACINE = os.path.dirname(ICI)
ESPACE = uuid.UUID("6f1c2a52-7f3e-4b7e-9d6a-0c5a2f3b8e11")
DATE_CHARGEMENT = "2026-11-25 00:00:00"

ENT = {e["nom"]: e for e in M.ENTITES}


def esc(s):
    return escape(s, {'"': "&quot;"})


def uid(*parts):
    return uuid.uuid5(ESPACE, ":".join(parts)).hex


# Contrôles du modèle ---------------------------------------------------------

def controler():
    erreurs = []
    verbes = [a["verbe"] for a in M.ASSOCIATIONS]
    if len(set(verbes)) != len(verbes):
        erreurs.append("verbes en double")
    reliees = {a["a"][0] for a in M.ASSOCIATIONS} | {a["b"][0] for a in M.ASSOCIATIONS}
    for e in M.ENTITES:
        noms = [at[0] for at in e["attributs"]]
        if len(set(noms)) != len(noms):
            erreurs.append("attribut en double dans %s" % e["nom"])
        if not noms[0].startswith("id_"):
            erreurs.append("%s : l'identifiant doit venir en premier" % e["nom"])
        if e["nom"] not in reliees:
            erreurs.append("%s n'est reliée à aucune association" % e["nom"])
        for at in e["attributs"]:
            if len(at) != 8:
                erreurs.append("%s.%s : il faut 8 champs" % (e["nom"], at[0]))
    for a in M.ASSOCIATIONS:
        for cote in ("a", "b"):
            if a[cote][0] not in ENT:
                erreurs.append("%s : entité inconnue %s" % (a["verbe"], a[cote][0]))
        if a["regle"] == "R2" and "table" not in a:
            erreurs.append("%s : R2 sans table de liaison" % a["verbe"])
        if a["regle"] != "R2" and "fk" not in a:
            erreurs.append("%s : clé étrangère manquante" % a["verbe"])
        ca, cb = a["a"][1], a["b"][1]
        attendu = regle_attendue(ca, cb)
        if attendu != a["regle"]:
            erreurs.append("%s : règle %s annoncée, %s attendue" % (a["verbe"], a["regle"], attendu))
    if erreurs:
        sys.exit("Contrôles du modèle en échec :\n- " + "\n- ".join(erreurs))


def regle_attendue(ca, cb):
    maxa, maxb = ca.split(",")[1], cb.split(",")[1]
    paire = {ca, cb}
    if maxa == "n" and maxb == "n":
        return "R2"
    if paire == {"1,1"}:
        return "R3"
    if paire == {"0,1", "1,1"}:
        return "R4"
    if paire == {"0,1"}:
        return "R5"
    if "1,1" in paire:
        return "R1"
    return "Hors cours"


# Clés étrangères et tables ---------------------------------------------------

def cles_etrangeres():
    """Pour chaque table : liste de (colonne, table cible, obligatoire, on_delete, unique)."""
    fks = {e["nom"]: [] for e in M.ENTITES}
    liaisons = []
    for a in M.ASSOCIATIONS:
        if a["regle"] == "R2":
            liaisons.append(a)
            continue
        table, col, oblig, ondel, uniq = a["fk"]
        cible = a["a"][0] if a["b"][0] == table else a["b"][0]
        fks[table].append((col, cible, oblig, ondel, uniq, a["verbe"]))
    return fks, liaisons


def ordre_tables(fks):
    ordre, faites = [], set()
    while len(ordre) < len(M.ENTITES):
        avance = False
        for e in M.ENTITES:
            n = e["nom"]
            if n in faites:
                continue
            if all(c[1] in faites or c[1] == n for c in fks[n]):
                ordre.append(n)
                faites.add(n)
                avance = True
        if not avance:
            sys.exit("Cycle de clés étrangères")
    return ordre


# Markdown --------------------------------------------------------------------

def dictionnaire_md():
    lignes = [
        "# ZakFit — dictionnaire des données",
        "",
        "Généré par `modele/generer.py` depuis `modele/modele.py`. Ne pas modifier à la main.",
        "",
        "Les 7 colonnes sont celles du cours : nom, description, type, format, contraintes, origine, fréquence de mise à jour.",
        "Les clés étrangères ne figurent pas ici : elles naissent des associations du MCD (voir `04-mcd-mld-mpd.md`).",
        "Une entité marquée ★ porte des données de santé (article 9 du RGPD), effacées au retrait du consentement. Le retrait efface aussi les séances importées de Santé et les kcal estimées des séances, et vide les associations de HEALTH_PROFILE (RG11).",
        "",
    ]
    for bloc in M.TITRES_BLOCS:
        ents = [e for e in M.ENTITES if e["bloc"] == bloc]
        if not ents:
            continue
        lignes += ["## %s" % bloc, ""]
        for e in ents:
            marque = " ★" if e.get("sensible") else ""
            lignes += ["### %s%s" % (e["nom"].upper(), marque), "", "Une occurrence : %s." % e["ligne"], "",
                       "| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |",
                       "|---|---|---|---|---|---|---|"]
            for at in e["attributs"]:
                lignes.append("| `%s` | %s |" % (at[0], " | ".join(x.replace("|", "\\|") for x in at[1:7])))
            lignes.append("")
    return "\n".join(lignes)


def mcd_mld_md(fks, liaisons, ordre):
    L = [
        "# ZakFit — MCD, MLD et MPD",
        "",
        "Généré par `modele/generer.py` depuis `modele/modele.py`. Ne pas modifier à la main.",
        "Schémas : `diagrammes/modelisation.drawio` (pages dictionnaire, MCD, MLD). Script : `sql/`.",
        "",
        "## 1. MCD : entités",
        "",
        "Notation du cours : entité en majuscules, identifiant souligné (ici en premier), propriétés ensuite.",
        "",
    ]
    for e in M.ENTITES:
        attrs = ", ".join(("<u>%s</u>" % at[0]) if i == 0 else at[0] for i, at in enumerate(e["attributs"]))
        L.append("- **%s** (%s) : %s" % (e["nom"].upper(), attrs, e["ligne"]))
    L += ["", "## 2. MCD : associations", "",
          "Chaque cardinalité se lit depuis l'entité, et se justifie par deux phrases. La règle de passage au MLD est celle du cours (R1 à R5) ; « Hors cours » désigne le cas 0,1 face à 0,n, traité par une clé étrangère facultative (Roy p. 155 et 161, Baptiste PDF 44).",
          "",
          "| Verbe | Patte A | Patte B | Phrases | Règle | Traduction au MLD |",
          "|---|---|---|---|---|---|"]
    for a in M.ASSOCIATIONS:
        if a["regle"] == "R2":
            trad = "Table de liaison `%s(#id_%s, #id_%s)`" % (a["table"], a["a"][0], a["b"][0])
        else:
            t, col, oblig, ondel, uniq = a["fk"]
            trad = "`%s.#%s` %s%s, ON DELETE %s" % (t, col, "obligatoire" if oblig else "facultative (NULL)",
                                                   ", UNIQUE" if uniq else "", ondel)
        note = (" " + a["note"]) if a.get("note") else ""
        L.append("| %s | %s %s | %s %s | %s %s%s | %s | %s |" % (
            a["verbe"].upper(), a["a"][0].upper(), a["a"][1], a["b"][0].upper(), a["b"][1],
            a["phrases"][0], a["phrases"][1], note, a["regle"], trad))
    L += ["", "## 3. MLD", "",
          "Notation du cours : `TABLE(clé_primaire, attribut, #clé_étrangère)`. Les clés primaires sont les premiers champs.",
          ""]
    for n in ordre:
        e = ENT[n]
        cols = ["<u>%s</u>" % e["attributs"][0][0]] + [at[0] for at in e["attributs"][1:]]
        cols += ["#%s" % c[0] for c in fks[n]]
        L.append("- `%s`(%s)" % (n, ", ".join(cols)))
    for a in liaisons:
        L.append("- `%s`(<u>#id_%s</u>, <u>#id_%s</u>)" % (a["table"], a["a"][0], a["b"][0]))
    L += ["", "## 4. MPD : choix physiques (MariaDB 10.4)", "",
          "- **Identifiants :** UUID stockés en `VARBINARY(16)`, comme le fait Fluent avec le pilote MySQL. Les données de référence ont des UUID stables (version 5), pour que le script se rejoue à l'identique.",
          "- **Listes de valeurs :** type `ENUM`, contrôlé par MariaDB.",
          "- **Dates :** `DATETIME(6)` en UTC pour les instants ; `DATE` pour les jours locaux (repas, pesées, énergie active), calculés dans le fuseau de l'utilisateur (RG23, RG38).",
          "- **Nombres :** `DECIMAL` pour les grammes et les kcal (pas d'erreur d'arrondi binaire, 02-formules.md §5).",
          "- **Suppressions :** ON DELETE CASCADE pour les données d'un utilisateur (RG43) ; RESTRICT pour les référentiels, qu'on archive au lieu de supprimer (RG22, RG46) ; SET NULL pour l'unité d'une ligne.",
          "- **Suppression d'un compte (RG43) :** les lignes de repas et de favoris protègent leur aliment (RESTRICT), y compris un aliment personnalisé. Le service supprime donc, dans une transaction : les repas, puis les favoris, puis le compte, dont la cascade efface le reste. La base refuse l'ordre inverse. Le test `modele/tester_sql.py` vérifie les deux cas.",
          "- **Contraintes de plusieurs lignes**, posées avec une colonne générée PERSISTENT et un index unique :",
          "  - un seul consentement actif par utilisateur (`health_consent.active_flag`) ;",
          "  - un seul objectif d'activité par mesure, période et catégorie, catégorie vide comprise (`activity_goal.category_key`), car un index unique ordinaire accepte plusieurs NULL.",
          "- **Règles vérifiées par l'API, pas par la base** (elles demandent la date du jour, un calcul ou le contexte de la requête) :",
          "  - âge d'au moins 18 ans (RG12), dates non futures (RG23, RG30), cohérence de l'énergie d'un aliment (RG18) ;",
          "  - au moins une ligne par repas et par favori ; priorité d'une pesée saisie sur Santé (RG39) ;",
          "  - aucune donnée de santé sans consentement actif (RG10), et le service de retrait du consentement (RG11) ;",
          "  - un aliment personnalisé n'est lu et utilisé que par son créateur (RG19, RG09). Sans ce contrôle, un repas d'un autre utilisateur pourrait le référencer, et la suppression du compte du créateur échouerait (RESTRICT) ;",
          "  - calcul de l'objectif en mode computed (RG34) ; MET d'un type jamais modifié (RG29) ; rôle et protection de l'administrateur contre lui-même (RG07) ;",
          "  - correspondance des types de séance de Santé avec le référentiel (RG33).",
          "- **Valeurs dérivées :** aucune n'est stockée (totaux, objectif calculé, kcal brûlées du jour), sauf trois valeurs figées volontairement : les valeurs d'une ligne de repas (RG25), les kcal estimées d'une séance (qui dépendent du poids au jour de la séance) et les versions de l'objectif calorique (RG52), pour qu'un bilan passé ne change pas quand l'objectif change.",
          "- **Chiffrement au repos (p. 25) :** toutes les tables InnoDB sont chiffrées par MariaDB (`innodb_encrypt_tables = ON`, plugin `file_key_management`, clé hors du dépôt). C'est un réglage du serveur, sans effet sur le script ni sur le code. Mise en place prévue avec le socle Vapor (30/11), avec une preuve conservée sans secret : plugin chargé, variables actives, tables chiffrées (`information_schema.INNODB_TABLESPACES_ENCRYPTION`).",
          "- **Conservation :** pas de purge automatique en version 1. Les données d'un compte vivent tant que le compte existe ; l'utilisateur les efface lui-même (RG11, RG43). Une durée de conservation des comptes inactifs reste à décider avant toute mise en ligne (article 5.1.e du RGPD).",
          "- **Index de lecture :** " + ", ".join("`%s(%s)`" % (t, c) for t, _, c in M.INDEX) + ".",
          ""]
    return "\n".join(L)


# SQL -------------------------------------------------------------------------

def sql_schema(fks, liaisons, ordre):
    L = ["-- ZakFit : schéma MariaDB 10.4. Généré par docs/conception/modele/generer.py, ne pas modifier à la main.",
         "-- À exécuter dans une base vide : mariadb -u <compte> <base> < 01-schema.sql",
         "SET NAMES utf8mb4;", ""]
    for n in ordre:
        e = ENT[n]
        cols = ["  %s %s" % (at[0], at[7]) for at in e["attributs"]]
        for col, cible, oblig, ondel, uniq, _ in fks[n]:
            cols.append("  %s VARBINARY(16) %s" % (col, "NOT NULL" if oblig else "NULL"))
        for extra in M.CONTRAINTES_SUPPLEMENTAIRES.get(n, []):
            if not extra.startswith("CONSTRAINT"):
                cols.append("  " + extra)
        cons = ["  CONSTRAINT pk_%s PRIMARY KEY (%s)" % (n, e["attributs"][0][0])]
        for col, cible, oblig, ondel, uniq, _ in fks[n]:
            cons.append("  CONSTRAINT fk_%s_%s FOREIGN KEY (%s) REFERENCES `%s` (id_%s) ON DELETE %s" % (
                n, col.replace("id_", "", 1), col, cible, cible, ondel))
            if uniq:
                cons.append("  CONSTRAINT uq_%s_%s UNIQUE (%s)" % (n, col, col))
        for a in M.ASSOCIATIONS:
            if a.get("unique") and a["unique"][0] == n:
                cons.append("  CONSTRAINT %s UNIQUE (%s)" % (a["unique"][1], a["unique"][2]))
        cons += ["  " + c for c in e["sql_contraintes"]]
        cons += ["  " + c for c in M.CONTRAINTES_SUPPLEMENTAIRES.get(n, []) if c.startswith("CONSTRAINT")]
        L.append("CREATE TABLE `%s` (\n%s\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n" % (
            n, ",\n".join(cols + cons)))
    for a in liaisons:
        t, ea, eb = a["table"], a["a"][0], a["b"][0]
        L.append(("CREATE TABLE `%s` (\n  id_%s VARBINARY(16) NOT NULL,\n  id_%s VARBINARY(16) NOT NULL,\n"
                  "  CONSTRAINT pk_%s PRIMARY KEY (id_%s, id_%s),\n"
                  "  CONSTRAINT fk_%s_%s FOREIGN KEY (id_%s) REFERENCES `%s` (id_%s) ON DELETE CASCADE,\n"
                  "  CONSTRAINT fk_%s_%s FOREIGN KEY (id_%s) REFERENCES `%s` (id_%s) ON DELETE RESTRICT\n"
                  ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;\n") % (
            t, ea, eb, t, ea, eb, t, ea, ea, ea, ea, t, eb, eb, eb, eb))
    for t, nom, cols in M.INDEX:
        L.append("CREATE INDEX %s ON `%s` (%s);" % (nom, t, cols))
    return "\n".join(L) + "\n"


ALLERGENES = [
    ("gluten", "Céréales contenant du gluten", "Cereals containing gluten"),
    ("crustaces", "Crustacés", "Crustaceans"),
    ("oeufs", "Œufs", "Eggs"),
    ("poisson", "Poissons", "Fish"),
    ("arachides", "Arachides", "Peanuts"),
    ("soja", "Soja", "Soybeans"),
    ("lait", "Lait (y compris le lactose)", "Milk (including lactose)"),
    ("fruits_a_coque", "Fruits à coque", "Nuts"),
    ("celeri", "Céleri", "Celery"),
    ("moutarde", "Moutarde", "Mustard"),
    ("sesame", "Graines de sésame", "Sesame seeds"),
    ("sulfites", "Anhydride sulfureux et sulfites", "Sulphur dioxide and sulphites"),
    ("lupin", "Lupin", "Lupin"),
    ("mollusques", "Mollusques", "Molluscs"),
]
GROUPES_EN = {
    "01": "Starters and mixed dishes", "02": "Fruits, vegetables, legumes and nuts", "03": "Cereal products",
    "04": "Meat, eggs and fish", "05": "Dairy products", "06": "Water and other beverages", "07": "Sugary products",
    "08": "Ice cream and sorbets", "09": "Fats and oils", "10": "Culinary aids and miscellaneous ingredients",
}
CATEGORIES = [
    ("walking", "Marche", "Walking"), ("cardio", "Cardio", "Cardio"), ("strength", "Musculation", "Strength training"),
    ("yoga", "Yoga et souplesse", "Yoga and flexibility"), ("sports", "Sports", "Sports"),
]
GROUPES_MUSCULAIRES = [
    ("legs", "Jambes", "Legs"), ("glutes", "Fessiers", "Glutes"), ("back", "Dos", "Back"),
    ("chest", "Pectoraux", "Chest"), ("shoulders", "Épaules", "Shoulders"), ("arms", "Bras", "Arms"),
    ("core", "Abdominaux et gainage", "Core"), ("full_body", "Corps entier", "Full body"),
]
# Proposition ZakFit, à relire par l'administrateur : le Compendium ne donne pas les muscles sollicités.
MUSCLES_PAR_CODE = {
    "17152": "legs glutes", "17190": "legs glutes", "17200": "legs glutes", "17080": "legs glutes core",
    "12030": "legs glutes core", "12050": "legs glutes core", "12070": "legs glutes core",
    "01010": "legs glutes", "01040": "legs glutes", "18240": "full_body shoulders back",
    "02071": "back legs arms", "02048": "legs glutes arms", "02214": "full_body", "15551": "legs shoulders",
    "02054": "full_body", "02050": "full_body", "02035": "full_body", "02175": "core full_body",
    "02105": "core", "15610": "legs glutes", "15055": "legs shoulders", "15675": "arms shoulders legs",
    "03025": "legs core", "15110": "arms shoulders core",
}


def difficulte(met):
    """Classe d'intensité du Compendium 2024 (Herrmann et al., §2.5) : léger < 3, modéré 3 à 5,9, vigoureux ≥ 6."""
    m = float(met)
    return "easy" if m < 3 else ("moderate" if m < 6 else "hard")


CATEGORIE_PAR_NOM = {"Marche": "walking", "Cardio": "cardio", "Musculation": "strength",
                     "Yoga et souplesse": "yoga", "Sports": "sports"}


def q(v):
    if v is None or v == "":
        return "NULL"
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def h(x):
    return "UNHEX('%s')" % x


def activites():
    texte = open(os.path.join(RACINE, "02-formules.md"), encoding="utf-8").read()
    sect = texte.split("## 7.")[1].split("## 8.")[0]
    lignes = []
    for l in sect.splitlines():
        m = re.match(r"\|\s*(Marche|Cardio|Musculation|Yoga et souplesse|Sports)\s*\|(.+)\|", l)
        if m:
            cells = [c.strip() for c in m.group(2).split("|")]
            lignes.append((CATEGORIE_PAR_NOM[m.group(1)], cells[0], cells[1], cells[2], cells[3].replace(",", ".")))
    if len(lignes) != 24:
        sys.exit("02-formules.md §7 : 24 activités attendues, %d trouvées" % len(lignes))
    return lignes


def sql_referentiels():
    A = list(csv.DictReader(open(os.path.join(RACINE, "donnees", "aliments.csv"), encoding="utf-8")))
    P = list(csv.DictReader(open(os.path.join(RACINE, "donnees", "portions.csv"), encoding="utf-8")))
    L = ["-- ZakFit : données de référence. Généré par docs/conception/modele/generer.py, ne pas modifier à la main.",
         "-- Sources : Anses. 2025. Table de composition nutritionnelle des aliments Ciqual (Etalab 2.0) ;",
         "-- USDA FoodData Central SR Legacy 2018 (CC0) ; 2024 Adult Compendium of Physical Activities (pacompendium.com).",
         "SET NAMES utf8mb4;", "START TRANSACTION;", ""]
    L.append("INSERT INTO allergen (id_allergen, code, name_fr, name_en) VALUES\n" + ",\n".join(
        "  (%s, %s, %s, %s)" % (h(uid("allergen", c)), q(c), q(fr), q(en)) for c, fr, en in ALLERGENES) + ";\n")
    groupes = sorted({(a["groupe_code"], a["groupe_fr"]) for a in A})
    L.append("INSERT INTO food_group (id_food_group, ciqual_group_code, name_fr, name_en) VALUES\n" + ",\n".join(
        "  (%s, %s, %s, %s)" % (h(uid("food_group", c)), q(c), q(fr), q(GROUPES_EN[c])) for c, fr in groupes) + ";\n")
    L.append("INSERT INTO activity_category (id_activity_category, code, name_fr, name_en) VALUES\n" + ",\n".join(
        "  (%s, %s, %s, %s)" % (h(uid("activity_category", c)), q(c), q(fr), q(en)) for c, fr, en in CATEGORIES) + ";\n")
    acts = activites()
    L.append("INSERT INTO activity_type (id_activity_type, compendium_code, name_fr, name_en, met, difficulty, is_archived, id_activity_category) VALUES\n" + ",\n".join(
        "  (%s, %s, %s, %s, %s, %s, FALSE, %s)" % (h(uid("activity_type", code)), q(code), q(fr), q(en), met, q(difficulte(met)), h(uid("activity_category", cat)))
        for cat, fr, en, code, met in acts) + ";\n")
    L.append("INSERT INTO muscle_group (id_muscle_group, code, name_fr, name_en) VALUES\n" + ",\n".join(
        "  (%s, %s, %s, %s)" % (h(uid("muscle_group", c)), q(c), q(fr), q(en)) for c, fr, en in GROUPES_MUSCULAIRES) + ";\n")
    codes = {c for _, _, _, c, _ in acts}
    if set(MUSCLES_PAR_CODE) != codes:
        sys.exit("Groupes musculaires : correspondance incomplète avec les 24 activités")
    L.append("-- Groupes musculaires par activité : proposition ZakFit, modifiable dans le back-office.")
    L.append("INSERT INTO activity_type_muscle_group (id_activity_type, id_muscle_group) VALUES\n" + ",\n".join(
        "  (%s, %s)" % (h(uid("activity_type", code)), h(uid("muscle_group", m)))
        for code in sorted(MUSCLES_PAR_CODE) for m in MUSCLES_PAR_CODE[code].split()) + ";\n")
    mer = {"poisson", "crustaces", "mollusques"}
    for a in A:
        if a["poisson_fruits_de_mer"] == "1" and not mer & set(a["allergenes"].split("|")):
            sys.exit("%s : poisson ou fruit de mer sans allergène correspondant" % a["ciqual_code"])
    vals = []
    for a in A:
        vals.append("  (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %d, %d, %d, %d, TRUE, FALSE, %s, %s, NULL)" % (
            h(uid("food", a["ciqual_code"])), q(a["ciqual_code"]), q(a["nom_fr"]), q(a["nom_en"]),
            a["kcal_100g"], a["proteines_100g"], a["glucides_100g"], a["lipides_100g"],
            a["fibres_100g"] or "NULL", a["alcool_100g"] or "NULL",
            int(a["viande"]), int(a["porc"]), int(a["produit_animal"]), int(a["alcool"]),
            q(DATE_CHARGEMENT), h(uid("food_group", a["groupe_code"]))))
    L.append("INSERT INTO food (id_food, ciqual_code, name_fr, name_en, kcal_100g, protein_100g, carbs_100g, fat_100g, "
             "fiber_100g, alcohol_100g, contains_meat, contains_pork, contains_animal_product, contains_alcohol, "
             "labels_verified, is_archived, created_at, id_food_group, id_user) VALUES\n" + ",\n".join(vals) + ";\n")
    fa = ["  (%s, %s)" % (h(uid("food", a["ciqual_code"])), h(uid("allergen", c)))
          for a in A for c in a["allergenes"].split("|") if c]
    L.append("INSERT INTO food_allergen (id_food, id_allergen) VALUES\n" + ",\n".join(fa) + ";\n")
    pv = []
    for i, p in enumerate(P):
        pv.append("  (%s, %s, %s, %s, %s, %s)" % (h(uid("food_portion", p["ciqual_code"], str(i))), q(p["libelle_fr"]),
                                                 q(p["libelle_en"]), p["grammes"], q(p["source"]), h(uid("food", p["ciqual_code"]))))
    L.append("INSERT INTO food_portion (id_food_portion, label_fr, label_en, grams, provenance, id_food) VALUES\n" + ",\n".join(pv) + ";\n")
    L.append("COMMIT;")
    return "\n".join(L) + "\n", len(A), len(P), len(fa)


# draw.io ---------------------------------------------------------------------

class Page:
    def __init__(self, pid, nom, w, h):
        self.pid, self.nom, self.w, self.h, self.cells, self.n = pid, nom, w, h, [], 0

    def nid(self):
        self.n += 1
        return "%s-%d" % (self.pid, self.n)

    def v(self, label, style, x, y, w, h):
        i = self.nid()
        self.cells.append('<mxCell id="%s" value="%s" style="%s" vertex="1" parent="1"><mxGeometry x="%s" y="%s" width="%s" height="%s" as="geometry"/></mxCell>'
                          % (i, esc(label), style, x, y, w, h))
        return i

    def e(self, a, b, style, label="", pos=0.0):
        i = self.nid()
        geo = '<mxGeometry x="%s" relative="1" as="geometry"/>' % pos if label else '<mxGeometry relative="1" as="geometry"/>'
        self.cells.append('<mxCell id="%s" value="%s" style="%s" edge="1" parent="1" source="%s" target="%s">%s</mxCell>'
                          % (i, esc(label), style, a, b, geo))

    def xml(self):
        return ('<diagram id="%s" name="%s"><mxGraphModel dx="1400" dy="900" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="%d" pageHeight="%d" math="0" shadow="0"><root><mxCell id="0"/><mxCell id="1" parent="0"/>%s</root></mxGraphModel></diagram>'
                % (self.pid, esc(self.nom), self.w, self.h, "".join(self.cells)))


TITRE = "rounded=0;whiteSpace=wrap;html=1;fillColor=#F9A55B;strokeColor=default;fontColor=#3A1F05;fontSize=17;fontFamily=Arial;align=left;verticalAlign=middle;spacingLeft=16;fontStyle=1;"
CASE = "rounded=0;whiteSpace=wrap;html=1;fontSize=13;fontFamily=Arial;align=left;verticalAlign=middle;spacingLeft=8;"
ENTETE = CASE + "fontStyle=1;fillColor=#FDE3CB;"
COULEURS = {"Compte": "#f5f5f5", "Santé": "#f8cecc", "Objectifs": "#e1d5e7", "Alimentation": "#d5e8d4",
            "Activité": "#dae8fc", "Référentiels": "#fff2cc"}
ENTITE = "rounded=0;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=12;align=left;verticalAlign=top;spacingLeft=8;spacingTop=4;fillColor=#FFFFFF;"
ASSO = "ellipse;whiteSpace=wrap;html=1;fontFamily=Arial;fontSize=12;fontStyle=1;fillColor=#FFFFFF;"
PATTE = "endArrow=none;html=1;rounded=0;fontFamily=Arial;fontSize=12;labelBackgroundColor=#FFFFFF;"
FLECHE = "endArrow=block;endFill=1;html=1;rounded=0;strokeColor=#64748b;fontFamily=Arial;fontSize=11;labelBackgroundColor=#FFFFFF;"
LIGNE_H = 18


def hauteur(e):
    return 34 + LIGNE_H * len(e["attributs"])


def page_dictionnaire():
    largeurs = [230, 380, 140, 260, 460, 250, 260]
    entetes = ["Nom de la donnée", "Description", "Type", "Format", "Contraintes / règles", "Origine", "Mise à jour"]
    x0, y = 120, 105
    tot = sum(largeurs)
    p = Page("dd", "MERISE - DD", x0 + tot + 80, 200)
    p.v("&nbsp; Dictionnaire de données — ZakFit", TITRE, x0, 40, tot, 65)
    x = x0
    for w, t in zip(largeurs, entetes):
        p.v(t, ENTETE, x, y, w, 56)
        x += w
    y += 56
    for e in M.ENTITES:
        debut = y
        for at in e["attributs"]:
            hl = 30 + 18 * max(1, max(len(at[k]) // (largeurs[k] // 8) for k in range(7)))
            x = x0
            for k, w in enumerate(largeurs):
                p.v(at[k], CASE, x, y, w, hl)
                x += w
            y += hl
        p.v(e["nom"].upper() + (" ★" if e.get("sensible") else ""),
            "whiteSpace=wrap;html=1;horizontal=0;fontFamily=Arial;fontSize=14;fontStyle=1;strokeWidth=0.7;fillColor=%s;" % COULEURS[e["bloc"]],
            40, debut, 80, y - debut)
    p.h = y + 60
    return p


def label_entite(e, avec_fk=None):
    lignes = ["<b>%s</b>" % e["nom"].upper(), "<hr>"]
    for i, at in enumerate(e["attributs"]):
        lignes.append("<u>%s</u>" % at[0] if i == 0 else at[0])
    return "<br>".join(lignes).replace("<br><hr><br>", "<hr>")


def centre(e):
    x, y = e["pos"]
    return x + 105, y + hauteur(e) / 2


def page_mcd():
    p = Page("mcd", "MERISE - MCD", 2560, 2300)
    p.v("&nbsp; Modèle Conceptuel de Données — ZakFit", TITRE, 40, 40, 2460, 65)
    ids = {}
    for e in M.ENTITES:
        x, y = e["pos"]
        ids[e["nom"]] = p.v(label_entite(e), ENTITE + "strokeColor=#333333;", x, y, 210, hauteur(e))
    for a in M.ASSOCIATIONS:
        ea, eb = ENT[a["a"][0]], ENT[a["b"][0]]
        (xa, ya), (xb, yb) = centre(ea), centre(eb)
        cx, cy = (xa + xb) / 2, (ya + yb) / 2
        if "decalage" in a:
            cx += a["decalage"][0]
            cy += a["decalage"][1]
        label = a["verbe"]
        aid = p.v(label, ASSO, cx - 55, cy - 20, 110, 40)
        p.e(ids[a["a"][0]], aid, PATTE, a["a"][1], -0.6)
        p.e(ids[a["b"][0]], aid, PATTE, a["b"][1], -0.6)
    return p


def page_mld(fks, liaisons):
    p = Page("mld", "MERISE - MLD", 3800, 2800)
    p.v("&nbsp; Modèle Logique de Données — ZakFit", TITRE, 40, 40, 3700, 65)
    ids = {}
    boites = []
    for e in M.ENTITES:
        lignes = ["PK %s VARBINARY(16)" % e["attributs"][0][0]]
        lignes += ["%s %s" % (at[0], at[7].split(" NOT NULL")[0].split(" NULL")[0].split(" DEFAULT")[0]) for at in e["attributs"][1:]]
        lignes += ["FK #%s VARBINARY(16)" % c[0] for c in fks[e["nom"]]]
        boites.append((e["nom"], (e["pos"][0] * 1.45, e["pos"][1] * 1.3), lignes))
    for a in liaisons:
        (xa, ya), (xb, yb) = centre(ENT[a["a"][0]]), centre(ENT[a["b"][0]])
        boites.append((a["table"], ((xa + xb) / 2 * 1.45 - 150, (ya + yb) / 2 * 1.3 - 40),
                       ["PK FK #id_%s VARBINARY(16)" % a["a"][0], "PK FK #id_%s VARBINARY(16)" % a["b"][0]]))
    for nom, (x, y), lignes in boites:
        label = "<b>%s</b><hr>%s" % (nom, "<br>".join(esc(l) for l in lignes))
        largeur = max(250, 8 + int(6.2 * max(len(l) for l in lignes)))
        ids[nom] = p.v(label, ENTITE + "strokeColor=#64748b;fontSize=11;", x, y, largeur, 34 + 16 * len(lignes))
    for n, liste in fks.items():
        for col, cible, oblig, ondel, uniq, _ in liste:
            p.e(ids[n], ids[cible], FLECHE, "fk_%s_%s" % (n, col.replace("id_", "", 1)), 0)
    for a in liaisons:
        p.e(ids[a["table"]], ids[a["a"][0]], FLECHE, "fk_%s_%s" % (a["table"], a["a"][0]), 0)
        p.e(ids[a["table"]], ids[a["b"][0]], FLECHE, "fk_%s_%s" % (a["table"], a["b"][0]), 0)
    return p


def main():
    controler()
    fks, liaisons = cles_etrangeres()
    ordre = ordre_tables(fks)
    os.makedirs(os.path.join(RACINE, "sql"), exist_ok=True)
    open(os.path.join(RACINE, "03-dictionnaire.md"), "w", encoding="utf-8").write(dictionnaire_md())
    open(os.path.join(RACINE, "04-mcd-mld-mpd.md"), "w", encoding="utf-8").write(mcd_mld_md(fks, liaisons, ordre))
    open(os.path.join(RACINE, "sql", "01-schema.sql"), "w", encoding="utf-8").write(sql_schema(fks, liaisons, ordre))
    ref, na, np_, nfa = sql_referentiels()
    open(os.path.join(RACINE, "sql", "02-referentiels.sql"), "w", encoding="utf-8").write(ref)
    pages = [page_dictionnaire(), page_mcd(), page_mld(fks, liaisons)]
    open(os.path.join(RACINE, "diagrammes", "modelisation.drawio"), "w", encoding="utf-8").write(
        '<mxfile host="app.diagrams.net" agent="ZakFit">' + "".join(pg.xml() for pg in pages) + "</mxfile>")
    print("Modèle : %d entités, %d associations, %d tables de liaison" % (len(M.ENTITES), len(M.ASSOCIATIONS), len(liaisons)))
    print("Référentiels : %d aliments, %d portions, %d liens aliment-allergène" % (na, np_, nfa))
    print("Écrits : 03-dictionnaire.md, 04-mcd-mld-mpd.md, sql/01-schema.sql, sql/02-referentiels.sql, diagrammes/modelisation.drawio")


if __name__ == "__main__":
    main()
