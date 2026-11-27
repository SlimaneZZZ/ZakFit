#!/usr/bin/env python3
"""Construit la base d'aliments pré-remplie de ZakFit à partir de CIQUAL 2025.

Entrées (chemins passés en arguments, jamais en dur) :
  --ciqual  table CIQUAL 2025 : le XLSX officiel (Table Ciqual 2025_FR_2025_11_03.xlsx)
            ou un export CSV de ce même fichier (même ordre de colonnes) ;
  --xml     alim_2025_11_03.xml (noms anglais alim_nom_eng) ;
  --usda    dossier décompressé FoodData_Central_sr_legacy_food_csv_2018-04
            (food.csv, food_portion.csv, measure_unit.csv).

Fichiers de décision, lus dans le dossier de ce script (modifiable avec --outils) :
  selection.csv       aliments candidats (alim_code, motif) ;
  etiquettes.csv      étiquettes relues à la main (régimes, alcool, allergènes) ;
  portions_choix.csv  portions : portion USDA choisie ou estimation justifiée.

Sorties, écrites dans le dossier parent de outils/ (modifiable avec --sortie) :
  aliments.csv, portions.csv. Le script affiche un rapport de contrôles.
  Avec --verifier, rien n'est écrit : le script compare ce qu'il produirait
  aux fichiers existants et échoue s'ils diffèrent.

Bibliothèque standard Python uniquement. Lancer avec : python3 -I construire_aliments.py ...
"""

import argparse
import collections
import csv
import io
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------

# Index des colonnes de l'onglet « composition nutritionnelle » (documentation
# CIQUAL 2025, section 4.2). Les en-têtes sont aussi vérifiés à la lecture.
COLONNES = {
    "grp_code": (0, "alim_grp_code"),
    "ssgrp_code": (1, "alim_ssgrp_code"),
    "grp_nom": (3, "alim_grp_nom_fr"),
    "ssgrp_nom": (4, "alim_ssgrp_nom_fr"),
    "code": (6, "alim_code"),
    "nom": (7, "alim_nom_fr"),
    "kcal": (10, "Energie, Règlement UE N° 1169 2011 (kcal 100 g)"),
    "proteines": (15, "Protéines, N x 6.25 (g 100 g)"),
    "glucides": (16, "Glucides (g 100 g)"),
    "lipides": (17, "Lipides (g 100 g)"),
    "fibres": (26, "Fibres alimentaires (g 100 g)"),
    "alcool": (29, "Alcool (éthanol) (g 100 g)"),
}

# Les 14 allergènes du règlement (UE) n° 1169/2011, annexe II, codes courts.
ALLERGENES = [
    "gluten", "crustaces", "oeufs", "poisson", "arachides", "soja", "lait",
    "fruits_a_coque", "celeri", "moutarde", "sesame", "sulfites", "lupin",
    "mollusques",
]
ALLERGENES_ANIMAUX = {"crustaces", "oeufs", "poisson", "lait", "mollusques"}
ALLERGENES_MER = {"crustaces", "poisson", "mollusques"}
DRAPEAUX = ["viande", "porc", "poisson_fruits_de_mer", "produit_animal", "alcool"]

COLONNES_ALIMENTS = [
    "ciqual_code", "nom_fr", "nom_en", "groupe_code", "groupe_fr", "kcal_100g",
    "proteines_100g", "glucides_100g", "lipides_100g", "fibres_100g", "alcool_100g",
    "viande", "porc", "poisson_fruits_de_mer", "produit_animal", "alcool",
    "allergenes",
]
COLONNES_PORTIONS = ["ciqual_code", "libelle_fr", "libelle_en", "grammes", "source"]


def espaces(texte):
    """Remplace les retours à la ligne et espaces multiples par une espace."""
    return re.sub(r"\s+", " ", texte or "").strip()


# ---------------------------------------------------------------------------
# Lecture de CIQUAL (XLSX officiel ou CSV)
# ---------------------------------------------------------------------------

def lire_xlsx(chemin):
    """Lit la première feuille d'un XLSX dont toutes les cellules sont du texte."""
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(chemin) as z:
        partages = []
        racine = ET.fromstring(z.read("xl/sharedStrings.xml"))
        for si in racine.findall("m:si", ns):
            partages.append("".join(t.text or "" for t in si.iter("{%s}t" % ns["m"])))
        feuille = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    lignes = []
    for row in feuille.find("m:sheetData", ns).findall("m:row", ns):
        cellules = {}
        for c in row.findall("m:c", ns):
            lettres = re.match(r"[A-Z]+", c.get("r")).group(0)
            col = 0
            for lettre in lettres:
                col = col * 26 + (ord(lettre) - 64)
            v = c.find("m:v", ns)
            if v is None:
                valeur = ""
            elif c.get("t") == "s":
                valeur = partages[int(v.text)]
            else:
                valeur = v.text or ""
            cellules[col - 1] = valeur
        largeur = max(cellules) + 1 if cellules else 0
        lignes.append([cellules.get(i, "") for i in range(largeur)])
    return lignes


def lire_ciqual(chemin):
    chemin = Path(chemin)
    if chemin.suffix.lower() == ".xlsx":
        lignes = lire_xlsx(chemin)
    else:
        with open(chemin, encoding="utf-8-sig", newline="") as f:
            lignes = list(csv.reader(f))
    entete, donnees = lignes[0], lignes[1:]
    for cle, (idx, attendu) in COLONNES.items():
        lu = espaces(entete[idx]).replace("/", " ")
        if espaces(attendu) != espaces(lu):
            sys.exit("En-tête inattendu colonne %d : %r (attendu %r)" % (idx, lu, attendu))
    table = {}
    for ligne in donnees:
        ligne = ligne + [""] * (84 - len(ligne))
        al = {cle: ligne[idx].strip() for cle, (idx, _) in COLONNES.items()}
        for cle in ("nom", "grp_nom", "ssgrp_nom"):
            al[cle] = espaces(al[cle])
        if al["code"]:
            table[al["code"]] = al
    return table


def lire_xml(chemin):
    noms = {}
    for alim in ET.parse(chemin).getroot().findall("ALIM"):
        code = (alim.findtext("alim_code") or "").strip()
        noms[code] = (espaces(alim.findtext("alim_nom_fr")), espaces(alim.findtext("alim_nom_eng")))
    return noms


# ---------------------------------------------------------------------------
# Valeurs CIQUAL : nombre, « traces », « < x », « - »
# ---------------------------------------------------------------------------

def valeur(texte):
    """Retourne (texte_sortie, nombre, statut).

    statut : 'mesure', 'traces', 'inferieur' (< x) ou 'inconnu' (-).
    Une valeur inconnue n'est jamais transformée en zéro (doc CIQUAL 3.2.2).
    """
    t = texte.strip()
    if t in ("-", ""):
        return "", None, "inconnu"
    if t.lower() == "traces":
        return "0", 0.0, "traces"
    if t.startswith("<"):
        return "0", 0.0, "inferieur"
    t = t.replace(",", ".")
    nombre = float(t)  # lève une erreur si la valeur est inattendue
    return t, nombre, "mesure"


SOMME_MAX = 100.5      # tolérance d'arrondi : CIQUAL publie 3 chiffres significatifs
SEUIL_ALCOOL = 0.5     # g d'éthanol pour 100 g à partir duquel l'étiquette alcool est obligatoire


def controle_rg18(kcal, p, g, l, fibres, alcool):
    """Règle RG18 révisée (décision du 23/11/2026) ; retourne la liste des écarts.

    Énergie calculée = 4 P + 4 G + 9 L + 2 fibres + 7 alcool ; fibres et alcool
    inconnus valent 0 pour ce calcul seulement. Somme P+G+L <= 100,5 g.
    """
    ecarts = []
    if not 0 <= kcal <= 900:
        ecarts.append("énergie hors de 0 à 900 kcal")
    for nom, x in (("protéines", p), ("glucides", g), ("lipides", l)):
        if not 0 <= x <= 100:
            ecarts.append("%s hors de 0 à 100 g" % nom)
    if p + g + l > SOMME_MAX:
        ecarts.append("somme P+G+L = %s g > %s g" % (round(p + g + l, 3), SOMME_MAX))
    calcule = 4 * p + 4 * g + 9 * l + 2 * fibres + 7 * alcool
    tolerance = max(20, 0.20 * kcal)
    if abs(kcal - calcule) > tolerance:
        ecarts.append("écart énergie |%s - %s| = %s > %s kcal"
                      % (kcal, round(calcule, 1), round(abs(kcal - calcule), 1), round(tolerance, 1)))
    return ecarts


# ---------------------------------------------------------------------------
# Proposition automatique d'étiquettes (règles par groupe et mots-clés).
# Elle ne sert qu'au rapport : les étiquettes livrées sont celles de
# etiquettes.csv, relues à la main ; le rapport liste les écarts.
# ---------------------------------------------------------------------------

MOTS = {
    "porc": r"porc|jambon(?! de (dinde|poulet|volaille))|lardon|saucisson|chorizo|rillettes|pâté|"
            r"toulouse|strasbourg|carbonara|tartiflette|quiche lorraine|cassoulet|royale",
    "viande": r"boeuf|bœuf|veau|agneau|mouton|poulet|dinde|canard|volaille|viande|merguez|"
              r"kebab|hamburger|bolognaise|hachis|blanquette|chili con carne",
    "mer": r"poisson|thon|saumon|sardine|maquereau|cabillaud|colin|crevette|\bmoules?\b|calmar|"
           r"huître|surimi|sushi",
    "vegetal": r"végétal|(?<!sans )soja|tofu|végan",
    "lait": r"\blait\b(?! de coco)|fromage|\bbeurre\b(?! de cacahuète)|crème|yaourt|emmental|comté|"
            r"camembert|feta|chèvre|parmesan|mozzarella|roquefort|reblochon|chantilly|gratin|pizza|"
            r"béchamel|tzatziki|croissant|brioche|petit suisse|tiramisu",
    "oeufs": r"\b(oeuf|œuf)s?\b|omelette|mayonnaise|brioche|madeleine|crêpe|flan|quiche|carbonara",
    "gluten": r"blé|pain|pâtes|semoule|couscous|boulgour|biscuit|biscotte|farine|pizza|croissant|"
              r"brioche|gâteau|madeleine|crêpe|tarte|quiche|hamburger|sandwich|avoine|muesli|"
              r"céréales|pétales|bière|cookie|spéculoos|seitan|gnocchi|tortilla|nuggets|taboulé",
    "fruits_a_coque": r"amande|noisette|noix(?! de coco)|cajou|pistache",
    "arachides": r"cacahuète|arachide",
    "sesame": r"sésame|tahin|houmous",
    "moutarde": r"moutarde|mayonnaise|vinaigrette|rémoulade",
    "celeri": r"céleri",
    "sulfites": r"\bvin\b|cidre|balsamique",
    "alcool": r"\bvin\b|bière|cidre|bourguignon|marinière",
}


def proposer(al, alcool_mesure):
    nom = al["nom"].lower()
    ss = al["ssgrp_code"]
    cherche = lambda cle: re.search(MOTS[cle], nom) is not None
    vegetal = cherche("vegetal")
    viande = (ss in {"0401", "0402", "0403", "0404"} or cherche("viande") or cherche("porc")) and not vegetal
    porc = cherche("porc") and not vegetal
    mer = (ss in {"0405", "0406", "0407", "0408", "0409"} or cherche("mer")) and not vegetal
    allergenes = set()
    if ss in {"0405", "0406", "0409"} or re.search(r"poisson|thon|saumon|sardine|maquereau|cabillaud|colin|surimi|sushi", nom):
        allergenes.add("poisson")
    if re.search(r"crevette|crabe", nom):
        allergenes.add("crustaces")
    if re.search(r"\bmoules?\b|calmar|huître", nom):
        allergenes.add("mollusques")
    if (al["grp_code"] == "05" or cherche("lait")) and not vegetal:
        allergenes.add("lait")
    if ss == "0410" or cherche("oeufs"):
        allergenes.add("oeufs")
    if re.search(r"(?<!sans )soja|tofu|tempeh", nom):
        allergenes.add("soja")
    for cle in ("gluten", "fruits_a_coque", "arachides", "sesame", "moutarde", "celeri", "sulfites"):
        if cherche(cle):
            allergenes.add(cle)
    if "sans gluten" in nom:
        allergenes.discard("gluten")
    animal = viande or mer or bool(allergenes & ALLERGENES_ANIMAUX) or "miel" in nom
    alcool = alcool_mesure or cherche("alcool")
    return {
        "viande": int(viande), "porc": int(porc), "poisson_fruits_de_mer": int(mer),
        "produit_animal": int(animal), "alcool": int(alcool),
        "allergenes": "|".join(a for a in ALLERGENES if a in allergenes),
    }


# ---------------------------------------------------------------------------
# Lecture des fichiers de décision
# ---------------------------------------------------------------------------

def lire_csv_dict(chemin):
    with open(chemin, encoding="utf-8", newline="") as f:
        lignes = list(csv.DictReader(f))
    for n, ligne in enumerate(lignes, start=2):
        if None in ligne:  # virgule non protégée : colonnes en trop
            sys.exit("%s ligne %d : colonnes en trop (virgule à mettre entre guillemets)" % (chemin, n))
    return lignes


def lire_etiquettes(chemin, erreurs):
    etiquettes = {}
    for n, ligne in enumerate(lire_csv_dict(chemin), start=2):
        code = ligne["alim_code"].strip()
        if code in etiquettes:
            erreurs.append("etiquettes.csv ligne %d : alim_code %s en double" % (n, code))
        for d in DRAPEAUX:
            if ligne[d] not in ("0", "1"):
                erreurs.append("etiquettes.csv ligne %d : %s doit valoir 0 ou 1" % (n, d))
        codes = [a for a in ligne["allergenes"].split("|") if a]
        inconnus = [a for a in codes if a not in ALLERGENES]
        if inconnus:
            erreurs.append("etiquettes.csv ligne %d : allergène inconnu %s" % (n, inconnus))
        if ligne["verifie"] != "oui":
            erreurs.append("etiquettes.csv ligne %d : verifie doit valoir « oui »" % n)
        ligne["allergenes"] = "|".join(a for a in ALLERGENES if a in codes)
        etiquettes[code] = ligne
    return etiquettes


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def construire(args):
    erreurs = []
    rapport = []
    dire = rapport.append

    ciqual = lire_ciqual(args.ciqual)
    noms_xml = lire_xml(args.xml)
    outils = Path(args.outils)
    selection = lire_csv_dict(outils / "selection.csv")
    etiquettes = lire_etiquettes(outils / "etiquettes.csv", erreurs)

    dire("CIQUAL : %d aliments lus ; XML : %d aliments." % (len(ciqual), len(noms_xml)))
    dire("Sélection : %d candidats." % len(selection))

    vus = set()
    aliments = []
    exclus = []
    speciaux = collections.Counter()
    ecarts_etiquettes = []
    for n, s in enumerate(selection, start=2):
        code = s["alim_code"].strip()
        if code in vus:
            erreurs.append("selection.csv ligne %d : alim_code %s en double" % (n, code))
            continue
        vus.add(code)
        al = ciqual.get(code)
        if al is None:
            erreurs.append("selection.csv ligne %d : alim_code %s absent de CIQUAL" % (n, code))
            continue
        nom_fr_xml, nom_en = noms_xml.get(code, ("", ""))
        if nom_fr_xml != al["nom"]:
            erreurs.append("%s : nom français différent entre XLSX/CSV et XML" % code)
        if not al["nom"] or not nom_en:
            erreurs.append("%s : nom français ou anglais manquant" % code)

        champs = {}
        for cle in ("kcal", "proteines", "glucides", "lipides", "fibres", "alcool"):
            champs[cle] = valeur(al[cle])
        manquants = [c for c in ("kcal", "proteines", "glucides", "lipides") if champs[c][2] == "inconnu"]
        if manquants:
            exclus.append((code, al["nom"], "valeur inconnue (« - ») pour " + ", ".join(manquants)))
            continue
        k, p, g, l = (champs[c][1] for c in ("kcal", "proteines", "glucides", "lipides"))
        fib = champs["fibres"][1] or 0.0
        alc = champs["alcool"][1] or 0.0
        ecarts = controle_rg18(k, p, g, l, fib, alc)
        if ecarts:
            exclus.append((code, al["nom"], "RG18 : " + " ; ".join(ecarts)))
            continue

        et = etiquettes.get(code)
        if et is None:
            erreurs.append("%s : aucune ligne dans etiquettes.csv" % code)
            continue
        if espaces(et["nom_fr"]) != al["nom"]:
            erreurs.append("%s : nom de etiquettes.csv différent de CIQUAL (code erroné ?)" % code)
        # Contrôles de cohérence des étiquettes relues.
        allg = set(a for a in et["allergenes"].split("|") if a)
        if (et["viande"] == "1" or et["poisson_fruits_de_mer"] == "1") and et["produit_animal"] != "1":
            erreurs.append("%s : viande ou poisson sans produit_animal" % code)
        if et["porc"] == "1" and et["viande"] != "1":
            erreurs.append("%s : porc sans viande" % code)
        if allg & ALLERGENES_ANIMAUX and et["produit_animal"] != "1":
            erreurs.append("%s : allergène d'origine animale sans produit_animal" % code)
        if bool(allg & ALLERGENES_MER) != (et["poisson_fruits_de_mer"] == "1"):
            erreurs.append("%s : allergène de la mer et étiquette poisson incohérents" % code)
        alcool_mesure = champs["alcool"][2] == "mesure" and champs["alcool"][1] >= SEUIL_ALCOOL
        if alcool_mesure and et["alcool"] != "1":
            erreurs.append("%s : éthanol CIQUAL >= %s g/100 g mais alcool = 0" % (code, SEUIL_ALCOOL))
        if et["alcool"] == "1" and not alcool_mesure and "alcool" not in et["note"].lower():
            erreurs.append("%s : alcool = 1 sans éthanol >= %s g ni justification dans la note" % (code, SEUIL_ALCOOL))
        if champs["alcool"][2] == "inconnu":
            erreurs.append("%s : teneur en alcool inconnue, à examiner" % code)

        auto = proposer(al, alcool_mesure)
        for cle in DRAPEAUX + ["allergenes"]:
            if str(auto[cle]) != et[cle]:
                ecarts_etiquettes.append((code, al["nom"], cle, auto[cle], et[cle]))

        for cle in ("kcal", "proteines", "glucides", "lipides", "fibres"):
            if champs[cle][2] in ("traces", "inferieur"):
                speciaux[(cle, champs[cle][2])] += 1
            if champs[cle][2] == "inconnu":
                speciaux[(cle, "inconnu")] += 1

        aliments.append({
            "ciqual_code": code,
            "nom_fr": al["nom"],
            "nom_en": nom_en,
            "groupe_code": al["grp_code"],
            "groupe_fr": al["grp_nom"],
            "kcal_100g": champs["kcal"][0],
            "proteines_100g": champs["proteines"][0],
            "glucides_100g": champs["glucides"][0],
            "lipides_100g": champs["lipides"][0],
            "fibres_100g": champs["fibres"][0],
            "alcool_100g": champs["alcool"][0],
            "viande": et["viande"],
            "porc": et["porc"],
            "poisson_fruits_de_mer": et["poisson_fruits_de_mer"],
            "produit_animal": et["produit_animal"],
            "alcool": et["alcool"],
            "allergenes": et["allergenes"],
            "_grp_code": al["grp_code"],
            "_fib": fib,
            "_alc": alc,
        })

    aliments.sort(key=lambda a: int(a["ciqual_code"]))
    codes_finaux = {a["ciqual_code"] for a in aliments}
    for code in etiquettes:
        if code not in vus:
            dire("Remarque : %s figure dans etiquettes.csv mais pas dans selection.csv." % code)

    # --- Portions -----------------------------------------------------------
    usda = Path(args.usda)
    foods = {r["fdc_id"]: r for r in lire_csv_dict(usda / "food.csv")}
    unites = {r["id"]: r["name"] for r in lire_csv_dict(usda / "measure_unit.csv")}
    portions_usda = {r["id"]: r for r in lire_csv_dict(usda / "food_portion.csv")}
    portions = []
    detail_portions = []
    cles_portions = set()
    for n, c in enumerate(lire_csv_dict(outils / "portions_choix.csv"), start=2):
        code = c["ciqual_code"].strip()
        if code not in codes_finaux:
            erreurs.append("portions_choix.csv ligne %d : %s absent de aliments.csv" % (n, code))
            continue
        cle = (code, c["libelle_fr"])
        if cle in cles_portions:
            erreurs.append("portions_choix.csv ligne %d : portion en double" % n)
        cles_portions.add(cle)
        if c["fdc_id"]:
            p = portions_usda.get(c["portion_id"])
            if p is None or p["fdc_id"] != c["fdc_id"]:
                erreurs.append("portions_choix.csv ligne %d : portion USDA %s introuvable pour fdc_id %s"
                               % (n, c["portion_id"], c["fdc_id"]))
                continue
            food = foods.get(c["fdc_id"])
            if food is None or food["data_type"] != "sr_legacy_food":
                erreurs.append("portions_choix.csv ligne %d : fdc_id %s absent de SR Legacy" % (n, c["fdc_id"]))
                continue
            grammes = p["gram_weight"]
            source = "USDA SR Legacy fdc_id=%s" % c["fdc_id"]
            if c.get("portion_us", "").strip() == "oui":
                source += " (portion US)"
            unite = unites.get(p["measure_unit_id"], "") if p["measure_unit_id"] != "9999" else ""
            mesure = espaces("%s %s %s" % (p["amount"], unite, p["modifier"] or p["portion_description"]))
            detail_portions.append("  %s %-40s %7s g  <- %s [%s]"
                                   % (code, c["libelle_fr"][:40], grammes, food["description"][:60], mesure))
        else:
            if not c["justification"].strip():
                erreurs.append("portions_choix.csv ligne %d : estimation sans justification" % n)
            grammes = c["grammes_estimes"]
            source = "estimation : " + c["justification"].strip()
            detail_portions.append("  %s %-40s %7s g  <- estimation" % (code, c["libelle_fr"][:40], grammes))
        if not grammes or float(grammes) <= 0:
            erreurs.append("portions_choix.csv ligne %d : poids invalide" % n)
        portions.append({"ciqual_code": code, "libelle_fr": c["libelle_fr"],
                         "libelle_en": c["libelle_en"], "grammes": grammes, "source": source})

    # --- Contrôles finaux sur aliments.csv ----------------------------------
    for a in aliments:
        k = float(a["kcal_100g"]); p = float(a["proteines_100g"])
        g = float(a["glucides_100g"]); l = float(a["lipides_100g"])
        if controle_rg18(k, p, g, l, a["_fib"], a["_alc"]):
            erreurs.append("%s : échec RG18 dans la sortie (ne doit pas arriver)" % a["ciqual_code"])
        if not a["nom_fr"] or not a["nom_en"]:
            erreurs.append("%s : nom manquant dans la sortie" % a["ciqual_code"])

    # --- Rapport --------------------------------------------------------------
    dire("")
    dire("== Aliments retenus : %d ==" % len(aliments))
    par_groupe = collections.Counter(a["groupe_fr"] for a in aliments)
    ordre = sorted(par_groupe, key=lambda gnom: min(x["_grp_code"] for x in aliments if x["groupe_fr"] == gnom))
    for gnom in ordre:
        dire("  %-45s %3d" % (gnom, par_groupe[gnom]))
    dire("")
    dire("== Candidats exclus : %d ==" % len(exclus))
    for code, nom, raison in exclus:
        dire("  %s %s -> %s" % (code, nom, raison))
    dire("")
    dire("== Valeurs spéciales dans les aliments retenus (remplacées par 0, sauf « - » laissé vide) ==")
    for (cle, statut), nb in sorted(speciaux.items()):
        dire("  %-10s %-10s %3d" % (cle, statut, nb))
    dire("")
    dire("== Étiquettes : %d écarts entre la règle automatique et la relecture manuelle ==" % len(ecarts_etiquettes))
    for code, nom, cle, auto, final in ecarts_etiquettes:
        dire("  %s %-45s %-22s auto=%-25s relu=%s" % (code, nom[:45], cle, auto, final))
    dire("")
    for d in DRAPEAUX:
        dire("  %-22s %3d aliments" % (d, sum(a[d] == "1" for a in aliments)))
    vege = sum(a["viande"] == "0" and a["poisson_fruits_de_mer"] == "0" for a in aliments)
    vegan = sum(a["produit_animal"] == "0" for a in aliments)
    sans_gluten = sum("gluten" not in a["allergenes"].split("|") for a in aliments)
    dire("  compatibles végétarien : %d ; végan : %d ; sans céréale à gluten : %d" % (vege, vegan, sans_gluten))
    for allg in ALLERGENES:
        dire("  allergène %-15s %3d" % (allg, sum(allg in a["allergenes"].split("|") for a in aliments)))
    dire("")
    nb_est = sum(p["source"].startswith("estimation") for p in portions)
    dire("== Portions : %d (USDA : %d ; estimations : %d) pour %d aliments =="
         % (len(portions), len(portions) - nb_est, nb_est, len({p["ciqual_code"] for p in portions})))
    rapport.extend(detail_portions)

    return aliments, portions, rapport, erreurs


def en_csv(lignes, colonnes):
    tampon = io.StringIO()
    w = csv.DictWriter(tampon, fieldnames=colonnes, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    w.writerows(lignes)
    return tampon.getvalue()


def main():
    ici = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ciqual", required=True, help="Table Ciqual 2025 (.xlsx officiel ou .csv exporté)")
    ap.add_argument("--xml", required=True, help="alim_2025_11_03.xml")
    ap.add_argument("--usda", required=True, help="dossier FoodData_Central_sr_legacy_food_csv_2018-04")
    ap.add_argument("--outils", default=str(ici), help="dossier des fichiers de décision (défaut : celui du script)")
    ap.add_argument("--sortie", default=str(ici.parent), help="dossier de sortie (défaut : parent de outils/)")
    ap.add_argument("--verifier", action="store_true", help="comparer aux fichiers existants sans rien écrire")
    args = ap.parse_args()

    aliments, portions, rapport, erreurs = construire(args)
    print("\n".join(rapport))
    if erreurs:
        print("\n== ERREURS : %d ==" % len(erreurs))
        for e in erreurs:
            print("  " + e)
        sys.exit(1)

    sorties = {
        Path(args.sortie) / "aliments.csv": en_csv(aliments, COLONNES_ALIMENTS),
        Path(args.sortie) / "portions.csv": en_csv(portions, COLONNES_PORTIONS),
    }
    print("")
    if args.verifier:
        differents = [str(c) for c, contenu in sorties.items()
                      if not c.exists() or c.read_text(encoding="utf-8") != contenu]
        if differents:
            print("VÉRIFICATION : fichiers différents de la régénération : " + ", ".join(differents))
            sys.exit(1)
        print("VÉRIFICATION : aliments.csv et portions.csv sont identiques à la régénération.")
    else:
        for chemin, contenu in sorties.items():
            chemin.write_text(contenu, encoding="utf-8")
            print("Écrit : %s" % chemin)
    print("Tous les contrôles sont passés.")


if __name__ == "__main__":
    main()
