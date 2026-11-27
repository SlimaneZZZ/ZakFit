"""Génère sql/03-donnees-demo.sql : les données fictives de démonstration de ZakFit.

Contenu : Zak LeBoss (compte de démonstration, 6 semaines d'historique), 18 autres utilisateurs
aux profils variés et 1 administrateur. Toutes les valeurs calculées suivent 02-formules.md.

Usage, depuis docs/conception :
  DEMO_PASSWORD=<mot de passe> python3 -I donnees/outils/generer_demo.py [--date-reference AAAA-MM-JJ]
  python3 -I donnees/outils/generer_demo.py --verifier "<commande mariadb complète, base comprise>"

Le mot de passe de tous les comptes vient de DEMO_PASSWORD. Il n'est écrit nulle part :
seule son empreinte bcrypt (htpasswd de XAMPP, coût 12, préfixe $2b$) entre dans le SQL.
La graine aléatoire est fixe : à date de référence égale, seules les empreintes changent d'une génération à l'autre.
"""
import argparse
import csv
import datetime as dt
import os
import random
import re
import shlex
import subprocess
import sys
from decimal import ROUND_CEILING, ROUND_HALF_UP, Decimal as D
from zoneinfo import ZoneInfo

ICI = os.path.dirname(os.path.abspath(__file__))
CONCEPTION = os.path.dirname(os.path.dirname(ICI))
sys.dont_write_bytecode = True
sys.path.insert(0, os.path.join(CONCEPTION, "modele"))
import generer as GEN  # noqa: E402  (uid, q, h, activites : mêmes UUID stables que 02-referentiels.sql)

GRAINE = 20261210
ECHELLE_KCAL = 1500
DATE_REFERENCE = "2026-12-10"
HTPASSWD = "/Applications/XAMPP/xamppfiles/bin/htpasswd"
SORTIE = os.path.join(CONCEPTION, "sql", "03-donnees-demo.sql")
UTC = dt.timezone.utc
VERSION_CONSENTEMENT = "2026-v1"

PAL = {"low": D("1.4"), "moderate": D("1.6"), "active": D("1.8"), "very_active": D("2.0")}
AJUSTEMENT = {"lose": -500, "maintain": 0, "gain": 300}
MER = {"poisson", "crustaces", "mollusques"}


def q2(x):
    return D(x).quantize(D("0.01"), ROUND_HALF_UP)


def entier(x):
    return int(D(x).quantize(D(1), ROUND_HALF_UP))


def uid(*parts):
    return GEN.uid("demo", *parts)


class Hex(str):
    pass


class Brut(str):
    pass


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, Hex):
        return GEN.h(v)
    if isinstance(v, Brut):
        return str(v)
    if isinstance(v, (int, D)):
        return str(v)
    if isinstance(v, dt.datetime):
        return "'%s'" % v.strftime("%Y-%m-%d %H:%M:%S")
    if isinstance(v, dt.date):
        return "'%s'" % v.isoformat()
    if isinstance(v, dt.time):
        return "'%s'" % v.strftime("%H:%M:%S")
    return GEN.q(v)


# ---------- Référentiels (lus dans les mêmes fichiers que generer.py) ----------

def charger_referentiels():
    aliments = {}
    for a in csv.DictReader(open(os.path.join(CONCEPTION, "donnees", "aliments.csv"), encoding="utf-8")):
        aliments[a["ciqual_code"]] = {
            "id": Hex(GEN.uid("food", a["ciqual_code"])), "nom": a["nom_fr"],
            # valeurs telles que la base les stocke : kcal en DECIMAL(7,3), macros en DECIMAL(8,4), arrondi 0,5 vers le haut
            "kcal": D(a["kcal_100g"]).quantize(D("0.001"), ROUND_HALF_UP), "p": D(a["proteines_100g"]).quantize(D("0.0001"), ROUND_HALF_UP),
            "g": D(a["glucides_100g"]).quantize(D("0.0001"), ROUND_HALF_UP), "l": D(a["lipides_100g"]).quantize(D("0.0001"), ROUND_HALF_UP),
            "viande": a["viande"] == "1", "porc": a["porc"] == "1", "animal": a["produit_animal"] == "1",
            "alcool": a["alcool"] == "1", "allergenes": {c for c in a["allergenes"].split("|") if c},
        }
    portions = []
    for i, p in enumerate(csv.DictReader(open(os.path.join(CONCEPTION, "donnees", "portions.csv"), encoding="utf-8"))):
        portions.append({"id": Hex(GEN.uid("food_portion", p["ciqual_code"], str(i))), "code": p["ciqual_code"],
                         # food_portion.grams est un DECIMAL(7,2) : la valeur du fichier est gardée telle quelle
                         "libelle": p["libelle_fr"], "g": D(p["grammes"]).quantize(D("0.01"), ROUND_HALF_UP)})
    activites = {code: {"id": Hex(GEN.uid("activity_type", code)), "met": D(met), "cat": cat, "nom": fr}
                 for cat, fr, en, code, met in GEN.activites()}
    return aliments, portions, activites


ALIMENTS, PORTIONS, ACTIVITES = charger_referentiels()


def codes_sante():
    """Codes du Compendium que la table fixe Santé -> ZakFit peut produire (RG33, 05-contrat-api.md §6)."""
    texte = open(os.path.join(CONCEPTION, "05-contrat-api.md"), encoding="utf-8").read()
    sect = texte.split("## 6.")[1].split("\n## ")[0]
    codes = set(re.findall(r"^\|\s*`[^|]+\|\s*(\d{5})\s*\|", sect, re.M))
    if not codes or not codes <= set(ACTIVITES):
        sys.exit("05-contrat-api.md §6 : table de correspondance Santé introuvable ou incohérente")
    return codes


CODES_SANTE = codes_sante()

PERSO = "perso:zak"
ALIMENTS[PERSO] = {
    "id": Hex(uid("food", "zak", "pancakes")), "nom": "Pancakes protéinés maison",
    "kcal": D("220.00"), "p": D("18.00"), "g": D("25.00"), "l": D("5.00"),
    "viande": False, "porc": False, "animal": True, "alcool": False, "allergenes": {"gluten", "oeufs", "lait"},
}


def portion(code, morceau=None):
    trouvees = [p for p in PORTIONS if p["code"] == code and (morceau is None or morceau in p["libelle"])]
    if len(trouvees) != 1:
        sys.exit("Portion introuvable ou ambiguë : %s %r" % (code, morceau))
    return trouvees[0]


# ---------- Modèles de repas ----------
# Un élément : (code, quantité, probabilité). Quantité : ("g", min, max) en grammes, mis à l'échelle de
# l'utilisateur et arrondi à 5 g, ou ("u", nombre ou tuple de nombres, morceau du libellé de l'unité).

def g(lo, hi):
    return ("g", lo, hi)


def u(n, morceau=None):
    return ("u", n, morceau)


PETIT_DEJ = {
    "baguette": [("7001", u(1), 1), ("16400", u(1, "noix"), 1), ("31024", u(1), 1), ("18004", u(1), 1), ("2070", u(1), .5)],
    "avoine": [("32140", g(40, 70), 1), ("19041", g(150, 250), 1), ("13005", u(1, "moyenne"), 1), ("31008", u(1), .5)],
    "fromage_blanc": [("19646", g(150, 200), 1), ("32004", g(30, 50), 1), ("13021", u(1), .6), ("18004", u(1), 1)],
    "croissant": [("7620", u(1), 1), ("18004", u(1), 1), ("2070", u(1), .7)],
    "oeufs": [("7110", u(2), 1), ("22502", u(2), 1), ("20385", u(1, "moyenne"), .5), ("18004", u(1), 1)],
    "yaourt": [("19593", u(1), 1), ("32004", g(25, 40), 1), ("13039", u(1, "moyenne"), 1), ("18020", u(1), 1)],
    "vegetal": [("18901", u(1), 1), ("32140", g(40, 60), 1), ("13005", u(1, "moyenne"), 1), ("15000", u(1, "poignée"), .5)],
    "tartines": [("7111", u(2), 1), ("31032", g(15, 25), 1), ("19041", g(200, 250), 1)],
    "sans_gluten": [("7130", g(60, 80), 1), ("16400", u(1, "noix"), 1), ("31024", u(1), 1), ("18004", u(1), 1)],
    "pancakes": [(PERSO, g(120, 160), 1), ("13014", u((5, 6, 8)), 1), ("18004", u(1), 1)],
}
DEJEUNER = {
    "poulet_riz": [("36018", g(120, 160), 1), ("9104", g(150, 220), 1), ("20320", g(120, 180), 1), ("17270", u(1, "soupe"), 1)],
    "pates_tomate": [("9811", g(200, 260), 1), ("11107", g(70, 100), 1), ("12120", u(2), 1), ("20031", g(40, 60), .6)],
    "jambon_beurre": [("25517", g(220, 280), 1), ("13039", u(1, "moyenne"), .6)],
    "salade_lentilles": [("20587", g(130, 180), 1), ("20385", u(1, "moyenne"), 1), ("12066", g(30, 50), 1), ("11110", u(1), 1)],
    "saumon_quinoa": [("26229", g(120, 150), 1), ("9341", g(130, 180), 1), ("20350", g(120, 180), 1), ("17270", u(1, "café"), 1)],
    "steak_pdt": [("6251", g(100, 125), 1), ("4026", u((1, 2)), 1), ("20031", g(40, 60), 1), ("11013", u(1), .5)],
    "couscous_legumes": [("25150", g(300, 380), 1), ("19593", u(1), .5)],
    "pizza": [("25404", u(2), 1), ("20031", g(50, 80), .7)],
    "kebab": [("25429", g(250, 320), 1), ("18018", u(1), .5)],
    "tofu_riz": [("20904", g(120, 160), 1), ("9103", g(150, 200), 1), ("20020", g(120, 180), 1), ("11104", u(1), 1)],
    "taboule_falafels": [("25608", g(150, 220), 1), ("25590", u((3, 4, 5)), 1), ("25621", u(2), 1)],
    "omelette": [("22500", u(3), 1), ("20031", g(50, 80), 1), ("7001", u(1), .6), ("11110", u(1), 1)],
    "dinde_puree": [("36306", g(110, 140), 1), ("4040", g(180, 230), 1), ("20320", g(100, 150), 1)],
    "cabillaud": [("26025", g(130, 170), 1), ("4003", u(2), 1), ("20336", g(100, 150), 1), ("16400", u(1, "noix"), 1)],
    "chili": [("25111", g(280, 330), 1), ("9104", g(80, 120), 1)],
    "sushis": [("25456", g(200, 260), 1), ("18020", u(1), 1)],
}
DINER = {
    "soupe": [("25903", g(250, 350), 1), ("7110", u(1), 1), ("12007", u(1), .6), ("19593", u(1), .4)],
    "omelette_salade": [("22500", u(2), 1), ("20031", g(50, 80), 1), ("20385", u(1, "moyenne"), 1), ("11110", u(1), 1),
                        ("19644", g(100, 150), .4)],
    "quiche": [("25405", g(130, 180), 1), ("20031", g(50, 80), 1), ("11110", u(1), 1)],
    "pates_thon": [("9871", g(180, 230), 1), ("26039", g(80, 120), 1), ("20385", u(6, "cerise"), 1), ("17270", u(1, "soupe"), 1)],
    "ratatouille_semoule": [("25018", g(220, 280), 1), ("9683", g(130, 180), 1), ("30155", g(80, 110), .6)],
    "gratin_jambon": [("25056", g(180, 230), 1), ("28925", u(2), 1), ("20031", g(40, 60), 1)],
    "risotto": [("25187", g(280, 330), 1), ("12120", u(2), 1)],
    "lentilles_coco": [("20587", g(150, 200), 1), ("9104", g(100, 150), 1), ("18041", g(40, 60), 1), ("20034", g(40, 60), 1)],
    "hachis": [("25009", g(280, 330), 1), ("20031", g(40, 60), 1)],
    "tempeh": [("20917", g(100, 140), 1), ("9341", g(150, 200), 1), ("20350", g(120, 160), 1), ("17270", u(1, "café"), 1)],
    "saumon_pdt": [("26229", g(120, 150), 1), ("4003", u(2), 1), ("20320", g(120, 160), 1)],
    "poulet_patate_douce": [("36006", u(1, "haut de cuisse"), 1), ("4102", u(1), 1), ("20352", g(120, 160), 1)],
    "couscous_viande": [("25152", g(300, 380), 1)],
    "steak_frites": [("6251", g(100, 125), 1), ("4032", g(120, 160), 1), ("11008", u(1), 1)],
    "galette": [("23801", g(70, 90), 1), ("12115", u(1), 1), ("22000", u(1, "moyen"), 1), ("20031", g(40, 60), 1)],
}
COLLATION = {
    "pomme": [("13039", u(1, "moyenne"), 1)],
    "yaourt_fruits": [("19587", u(1), 1)],
    "amandes": [("15000", u(1, "poignée"), 1)],
    "banane_chocolat": [("13005", u(1, "moyenne"), 1), ("31074", g(15, 25), 1)],
    "barre": [("31106", u(1), 1)],
    "proteines": [("19724", u(1), 1)],
    "compote_biscuits": [("13038", u(1), 1), ("24015", u(3), 1)],
    "fromage_blanc_miel": [("19644", g(130, 170), 1), ("31008", u(1), 1)],
    "clementines": [("13024", u(2), 1)],
    "cookies": [("24684", u(2), 1), ("18004", u(1), 1)],
    "noix": [("15005", u(1), 1)],
    "pancakes": [(PERSO, g(80, 120), 1)],
}
ACCOMPAGNEMENTS = [("7001", u(1), .45), ("13039", u(1, "moyenne"), .25), ("19593", u(1), .3), ("12007", u(1), .15),
                   ("31074", g(10, 20), .1), ("13024", u(2), .15)]
EXTRAS_DINER = [("5214", u(1), "vin"), ("19587", u(1), "dessert"), ("13024", u(2), "fruit")]

FAVORIS_ZAK = [
    ("Petit-déj avoine", "breakfast", [("32140", ("g", 50)), ("19041", ("g", 200)), ("13005", ("u", 1, "moyenne")), ("31008", ("u", 1, None))]),
    ("Bowl poulet riz brocoli", "lunch", [("36018", ("u", D("1.5"), "cuit")), ("9104", ("g", 180)), ("20350", ("g", 150)),
                                          ("17270", ("u", 1, "soupe"))]),
]


# ---------- Utilisateurs ----------
# zone : fuseau ; inscrit : jours avant la date de référence ; sante : import depuis Santé ;
# consentement : actif, jamais ou retire (avec le nombre de jours après l'inscription) ; facteur : échelle des portions.

AUTRES = [
    dict(cle="ines", prenom="Inès", nom="Moreau", sexe="female", naissance=1999, taille=164, niveau="moderate", orientation="lose",
         poids=68.4, viande="standard", inscrit=63, sante=True, appetit=1.0, assiduite=.75, nb_seances=(2, 3),
         types=["17200", "02175", "12030"], rythme_poids=-.045),
    dict(cle="lucas", prenom="Lucas", nom="Bernard", sexe="male", naissance=2001, taille=180, niveau="active", orientation="gain",
         poids=71.2, viande="standard", inscrit=55, sante=True, appetit=1.0, assiduite=.8, nb_seances=(3, 5),
         types=["02050", "02054", "15610"], rythme_poids=.03, macros_perso=(160, 400, 100)),
    dict(cle="chloe", prenom="Chloé", nom="Martin", sexe="female", naissance=1996, taille=168, niveau="low", orientation="maintain",
         poids=59.8, vegetarien=True, allergenes=["lait"], inscrit=48, appetit=1.0, assiduite=.6, nb_seances=(1, 3),
         types=["02175", "02105", "17190"], rythme_poids=0),
    dict(cle="hugo", prenom="Hugo", nom="Petit", sexe="male", naissance=1988, taille=176, niveau="moderate", orientation="lose",
         poids=92.6, viande="halal", inscrit=70, appetit=1.0, assiduite=.55, nb_seances=(2, 3),
         types=["12050", "02048", "02054"], rythme_poids=-.05),
    dict(cle="sarah", prenom="Sarah", nom="Lefèvre", sexe="female", naissance=1979, taille=160, niveau="moderate", orientation="maintain",
         poids=61.5, viande="standard", allergenes=["gluten"], inscrit=80, appetit=1.0, assiduite=.7, nb_seances=(1, 3),
         types=["18240", "17200", "02105"], rythme_poids=0, manuel=(10, 1900)),
    dict(cle="mehdi", prenom="Mehdi", nom="Haddad", sexe="male", naissance=1993, taille=184, niveau="very_active", orientation="gain",
         poids=78.0, viande="halal", inscrit=45, sante=True, appetit=1.0, assiduite=.85, nb_seances=(4, 5),
         types=["02050", "15055", "02214"], rythme_poids=.035, macros_perso=(190, 420, 120)),
    dict(cle="camille", prenom="Camille", nom="Roux", sexe="female", naissance=2003, taille=172, niveau="active", orientation="maintain",
         poids=58.3, vegetarien=True, vegan=True, inscrit=38, appetit=1.0, assiduite=.65, nb_seances=(2, 4),
         types=["03025", "02175", "01010"], rythme_poids=0),
    dict(cle="thomas", prenom="Thomas", nom="Fournier", sexe="male", naissance=1972, taille=176, niveau="low", orientation="lose",
         poids=97.8, viande="standard", inscrit=75, sante=True, appetit=1.0, assiduite=.6, nb_seances=(2, 4),
         types=["17190", "01010", "18240"], rythme_poids=-.055),
    dict(cle="lea", prenom="Léa", nom="Girard", sexe="female", naissance=1990, taille=164, niveau="moderate", orientation="gain",
         poids=52.1, viande="standard", inscrit=66, appetit=1.0, assiduite=.55, nb_seances=(2, 3),
         types=["02035", "12030", "03025"], rythme_poids=.025),
    dict(cle="nathalie", prenom="Nathalie", nom="Dupuis", sexe="female", naissance=1968, taille=160, niveau="low", orientation="lose",
         poids=72.0, viande="standard", allergenes=["crustaces"], inscrit=59, appetit=1.0, assiduite=.7, nb_seances=(1, 3),
         types=["17152", "17190", "02175"], rythme_poids=-.04),
    dict(cle="yanis", prenom="Yanis", nom="Benali", sexe="male", naissance=2004, taille=188, niveau="very_active", orientation="gain",
         poids=74.5, viande="no_pork", inscrit=52, appetit=1.0, assiduite=.6, nb_seances=(3, 5),
         types=["15610", "12070", "02050"], rythme_poids=.03),
    dict(cle="julie", prenom="Julie", nom="Lambert", sexe="female", naissance=1985, taille=168, niveau="active", orientation="lose",
         poids=70.8, viande="standard", inscrit=34, sante=True, appetit=1.0, assiduite=.8, nb_seances=(3, 4),
         types=["12050", "02071", "02035"], rythme_poids=-.05),
    dict(cle="antoine", prenom="Antoine", nom="Mercier", sexe="male", naissance=1975, taille=180, niveau="moderate", orientation="maintain",
         poids=82.3, viande="kosher", inscrit=41, appetit=1.0, assiduite=.5, nb_seances=(1, 3),
         types=["15675", "17200", "01040"], rythme_poids=0, manuel=(0, 2500)),
    dict(cle="manon", prenom="Manon", nom="Chevalier", sexe="female", naissance=1998, taille=156, niveau="moderate", orientation="maintain",
         poids=52.4, viande="standard", allergenes=["fruits_a_coque"], inscrit=29, appetit=1.0, assiduite=.65, nb_seances=(1, 3),
         types=["03025", "02105", "15551"], rythme_poids=0),
    dict(cle="paul", prenom="Paul", nom="Garnier", sexe="male", naissance=1963, taille=172, niveau="low", orientation="gain",
         poids=66.0, viande="standard", inscrit=24, appetit=1.0, assiduite=.6, nb_seances=(1, 2),
         types=["17152", "17080", "01010"], rythme_poids=.02),
    dict(cle="emilie", prenom="Émilie", nom="Robin", sexe="female", consentement="jamais", inscrit=57, appetit=1.0, assiduite=.45,
         nb_seances=(1, 2), types=["02175", "17200"], manuel=(0, 1700)),
    dict(cle="karim", prenom="Karim", nom="Saïdi", sexe="male", naissance=1991, taille=176, niveau="active", orientation="maintain",
         poids=79.5, viande="standard", consentement="retire", retrait=18, inscrit=50, appetit=1.0, assiduite=.55, nb_seances=(2, 3),
         types=["15110", "12050", "02054"], rythme_poids=0),
    dict(cle="romain", prenom="Romain", nom="Faure", sexe="male", consentement="jamais", inscrit=36, appetit=1.0, assiduite=.4,
         nb_seances=(0, 2), types=["15055", "02054"], manuel=(0, 2500)),
]

ZAK = dict(cle="zak", prenom="Zak", nom="LeBoss", sexe="male", naissance=1994, taille=180, niveau="moderate", orientation="lose",
           poids=86.4, viande="no_pork", allergenes=["arachides"], inscrit=41, sante=True, appetit=1.0, assiduite=1.0,
           nb_seances=(3, 5), types=[], rythme_poids=-.065)

ADMIN = dict(cle="admin", prenom="Sofia", nom="Admin", email="admin@example.com", role="admin", inscrit=100)

STATUTS = {"romain": ("blocked", 4), "yanis": ("suspended", 9)}  # clé : (statut, jours avant la référence)
LEVEE = ("lea", 25, 22)  # bloquée 25 jours avant la référence, réactivée 22 jours avant


def sans_accents(s):
    table = str.maketrans("àâäéèêëîïôöùûüçÉÈÊÀÂÎÔÛÇ", "aaaeeeeiioouuucEEEAAIOUC")
    return s.translate(table).lower().replace(" ", "")


# ---------- Calculs de 02-formules.md ----------

def objectif_calcule(p, poids, annee):
    """§1 à §3 : Mifflin-St Jeor, PAL, orientation, plancher, plafond, arrondi à la dizaine supérieure."""
    age = annee - p["naissance"]
    ree_exacte = 10 * D(str(poids)) + D("6.25") * p["taille"] - 5 * age + (5 if p["sexe"] == "male" else -161)

    def objectif(ree):
        base = max(ree * PAL[p["niveau"]] + AJUSTEMENT[p["orientation"]], ree, D(1200))
        return min(6000, int((base / 10).to_integral_value(ROUND_CEILING)) * 10)

    resultat = objectif(D(entier(ree_exacte)))
    if resultat != objectif(ree_exacte):
        sys.exit("Objectif ambigu selon l'arrondi de la REE (%s, %s kg)" % (p["cle"], poids))
    return resultat


def macros(kcal):
    """§4 : 15 % de protéines, 48 % de glucides, 37 % de lipides, coefficients d'Atwater."""
    return entier(D(kcal) * D("0.15") / 4), entier(D(kcal) * D("0.48") / 4), entier(D(kcal) * D("0.37") / 9)


def kcal_estimees(met, poids, minutes):
    """§6 : (MET − 1) × poids × heures, figé à 2 décimales."""
    return q2((met - 1) * D(str(poids)) * minutes / 60)


# ---------- Génération ----------

class Jeu:
    def __init__(self, reference):
        self.ref = reference
        self.rng = random.Random(GRAINE)
        self.t = {n: [] for n in [
            "user", "health_profile", "health_consent", "health_profile_allergen", "food", "food_allergen",
            "favorite_meal", "favorite_item", "meal", "meal_item", "activity", "daily_active_energy", "weigh_in",
            "calorie_goal", "calorie_target_history", "activity_goal", "reminder_setting", "login_event", "admin_action"]}
        self.attendu = {}

    # -- outils de date --
    def instant(self, p, jour, h, m=0):
        local = dt.datetime(jour.year, jour.month, jour.day, h, m, tzinfo=ZoneInfo(p["zone"]))
        return local.astimezone(UTC).replace(tzinfo=None)

    def maintenant(self, p):
        return self.instant(p, self.ref, 21, 30)

    # -- compatibilité régime et allergènes (RG16, RG17, RG21) --
    def compatible(self, p, code):
        a = ALIMENTS[code]
        if code == PERSO and p["cle"] != "zak":
            return False
        if a["allergenes"] & set(p.get("allergenes", [])):
            return False
        if p.get("vegan") and a["animal"]:
            return False
        if p.get("vegetarien") and (a["viande"] or a["allergenes"] & MER):
            return False
        if p.get("viande") in ("no_pork", "halal", "kosher") and a["porc"]:
            return False
        if p.get("viande") == "halal" and a["alcool"]:
            return False
        if p.get("viande") == "kosher" and a["allergenes"] & {"crustaces", "mollusques"}:
            return False
        return True

    def modeles(self, p, catalogue):
        return {n: m for n, m in catalogue.items() if all(self.compatible(p, c) for c, _, pr in m if pr == 1)}

    def ligne(self, p, code, quantite, fixe=False):
        a = ALIMENTS[code]
        if quantite[0] == "g":
            if fixe:
                grammes = D(quantite[1])
            else:
                grammes = D(max(5, int(round(self.rng.uniform(quantite[1], quantite[2]) * p["facteur"] / 5)) * 5))
            por, nombre = None, None
        else:
            n = quantite[1]
            nombre = D(str(self.rng.choice(n) if isinstance(n, tuple) else n))
            por = portion(code, quantite[2])
            grammes = nombre * por["g"]
            if grammes != grammes.quantize(D("0.01")):
                sys.exit("Quantité à plus de 2 décimales : %s" % code)
        grammes = grammes.quantize(D("0.01"))
        return {"code": code, "q": grammes, "n": nombre.quantize(D("0.01")) if nombre is not None else None,
                "portion": por["id"] if por else None,
                "kcal": q2(a["kcal"] * grammes / 100), "p": q2(a["p"] * grammes / 100),
                "g": q2(a["g"] * grammes / 100), "l": q2(a["l"] * grammes / 100)}

    def repas(self, p, jour, type_, lignes, origine, heure):
        cle = "%s:%s:%s" % (p["cle"], jour.isoformat(), type_)
        id_ = Hex(uid("meal", cle))
        cree = self.instant(p, jour, *heure) + dt.timedelta(minutes=self.rng.randint(5, 50))
        cree = min(cree, self.maintenant(p))
        modifie = cree + dt.timedelta(minutes=self.rng.randint(1, 30)) if self.rng.random() < .08 else cree
        modifie = min(modifie, self.maintenant(p))
        self.t["meal"].append([id_, type_, jour, origine, cree, modifie, p["id"]])
        for i, l in enumerate(lignes):
            self.t["meal_item"].append([Hex(uid("meal_item", cle, str(i))), l["q"], l["n"], l["kcal"], l["p"], l["g"], l["l"],
                                        None, id_, ALIMENTS[l["code"]]["id"], l["portion"]])
        p["repas"].append({"jour": jour, "type": type_, "lignes": lignes, "origine": origine})

    def composer(self, p, modele, accompagner=False):
        elements = list(modele) + (ACCOMPAGNEMENTS if accompagner else [])
        lignes, vus = [], set()
        for c, qte, pr in elements:
            if c not in vus and self.compatible(p, c) and self.rng.random() < pr:
                lignes.append(self.ligne(p, c, qte))
                vus.add(c)
        return lignes

    def echelle(self, p, cible):
        # portions en grammes proportionnelles à l'objectif de départ (calibré pour couvrir 85 à 105 % de l'objectif)
        p["facteur"] = min(2.2, max(.75, cible / ECHELLE_KCAL * p["appetit"]))

    # -- comptes --
    def compte(self, p, cree, role="user", statut="active", bloque_jusqua=None, modifie=None):
        p["id"] = Hex(uid("user", p["cle"]))
        p.setdefault("zone", "Europe/Paris")
        p["email"] = p.get("email") or "%s.%s@example.com" % (sans_accents(p["prenom"]), sans_accents(p["nom"]))
        p["cree"] = cree
        self.t["user"].append([p["id"], p["nom"], p["prenom"], p["email"], Brut("@HASH_%s@" % p["cle"]), role, statut,
                               bloque_jusqua, cree, p["zone"], cree, modifie or cree])

    def sante(self, p, debut, retrait=None):
        p["id_profil"] = Hex(uid("health_profile", p["cle"]))
        consenti = self.instant(p, debut, *p["heure_inscription"]) + dt.timedelta(minutes=2)
        self.t["health_consent"].append([Hex(uid("health_consent", p["cle"], "1")), VERSION_CONSENTEMENT, consenti, retrait,
                                         p["id"]])
        if retrait:
            # RG11 : au retrait, le profil de santé et ses allergènes sont supprimés ; seul l'historique du consentement reste
            return
        self.t["health_profile"].append([p["id_profil"], p["naissance"], p["sexe"], p["taille"], p["niveau"], p["orientation"],
                                         None if p.get("vegetarien") else p.get("viande", "standard"),
                                         bool(p.get("vegetarien")), bool(p.get("vegan")), consenti + dt.timedelta(minutes=3),
                                         p["id"]])
        for c in p.get("allergenes", []):
            self.t["health_profile_allergen"].append([p["id_profil"], Hex(GEN.uid("allergen", c))])

    # -- pesées --
    def pesees(self, p, jours, depart):
        poids = D(str(p["poids"]))
        resultat = []
        for j in jours:
            ecart = (j - depart).days
            valeur = D(str(p["poids"])) + D(str(p["rythme_poids"])) * ecart + D(str(round(self.rng.uniform(-.25, .25), 2)))
            poids = valeur.quantize(D("0.1"), ROUND_HALF_UP) if j != depart else D(str(p["poids"]))
            sante = p.get("sante") and j != depart and self.rng.random() < .3
            ecrite = p["cle"] == "zak" and not sante and j >= depart + dt.timedelta(days=7)  # pesée saisie écrite dans Santé
            pese = self.instant(p, j, 7, self.rng.randint(0, 20)) if j != depart else p["cree"] + dt.timedelta(minutes=2)
            # au plus une pesée importée ignorée par utilisateur : chez Zak, la première venue de Santé,
            # une pesée d'un proche sur sa balance, qu'il a supprimée (RG39) ; son poids est effacé
            ignoree = bool(sante) and p["cle"] == "zak" and not any(r[5] for r in self.t["weigh_in"] if r[-1] == p["id"])
            self.t["weigh_in"].append([Hex(uid("weigh_in", p["cle"], j.isoformat())), j, None if ignoree else poids.quantize(D("0.01")),
                                       "health" if sante else "manual",
                                       Hex(uid("health", "weigh_in", p["cle"], j.isoformat())) if sante or ecrite else None,
                                       ignoree, pese + dt.timedelta(minutes=2), p["id"]])
            if not ignoree:
                resultat.append((j, poids))
        p["pesees"] = resultat

    def poids_du_jour(self, p, jour):
        avant = [w for j, w in p.get("pesees", []) if j <= jour]
        return avant[-1] if avant else None

    # -- objectif calorique et historique (RG34 à RG36, RG52) --
    def objectif_calorique(self, p, evenements):
        versions = {}
        etat = {"mode": "computed", "manuel": None, "macros": None, "dernier_calcule": None}
        courant = None
        for jour, quoi, valeur in sorted(evenements, key=lambda e: (e[0], e[1] != "pesee")):
            if quoi == "pesee":
                p["_poids"] = valeur
            elif quoi == "manuel":
                etat["mode"], etat["manuel"] = "manual", valeur
            elif quoi == "macros":
                etat["macros"] = valeur
            elif quoi == "retrait":
                for j in [j for j, v in versions.items() if v[4] == "computed"]:
                    del versions[j]  # RG11 : les versions calculées sont effacées
                etat["mode"], etat["manuel"] = "manual", min(6000, max(1200, etat["dernier_calcule"]))
            if etat["mode"] == "computed":
                kcal = objectif_calcule(p, p["_poids"], jour.year)
                etat["dernier_calcule"] = kcal
            else:
                kcal = etat["manuel"]
            cible = (kcal,) + (etat["macros"] or macros(kcal)) + (etat["mode"],)
            if cible != courant:
                versions[jour] = cible
                courant = cible
        p["versions"] = sorted(versions.items())
        id_goal = Hex(uid("calorie_goal", p["cle"]))
        dernier_jour, dernier = p["versions"][-1]
        maj = max(self.instant(p, dernier_jour, 8, 30), p["cree"] + dt.timedelta(minutes=8))
        self.t["calorie_goal"].append([id_goal, etat["mode"], etat["manuel"] if etat["mode"] == "manual" else None,
                                       dernier[1], dernier[2], dernier[3], etat["macros"] is not None, maj, p["id"]])
        for jour, v in p["versions"]:
            self.t["calorie_target_history"].append([Hex(uid("calorie_target_history", p["cle"], jour.isoformat())), jour,
                                                     v[0], v[1], v[2], v[3], v[4], id_goal])

    # -- séances --
    def seance(self, p, jour, code, minutes, heure, source="manual", statut=None, ignoree=False, saisie=None, ecrite=False):
        a = ACTIVITES[code]
        debut = self.instant(p, jour, *heure)
        jour_local = jour_dans_fuseau(debut, p["zone"])  # performed_on : jour local de performed_at (RG38)
        if jour_local != jour:
            sys.exit("Séance hors de sa date locale : %s %s" % (p["cle"], jour))
        fin = debut + dt.timedelta(minutes=minutes)
        poids = self.poids_du_jour(p, jour)
        if source == "health":
            kcal = None if ignoree else q2(kcal_estimees(a["met"], poids or 75, minutes) * D(str(round(self.rng.uniform(.9, 1.15), 3))))
            statut = "unknown" if ignoree else "entered"
            cree = fin + dt.timedelta(minutes=self.rng.randint(10, 90))
        else:
            if statut is None:
                statut = "estimated" if poids is not None and self.rng.random() < .8 else ("entered" if self.rng.random() < .6 else "unknown")
                if statut == "estimated" and poids is None:
                    statut = "entered"
            if statut == "estimated":
                kcal = kcal_estimees(a["met"], poids, minutes)
            elif statut == "entered":
                kcal = D(saisie if saisie is not None else entier(kcal_estimees(a["met"], poids or 75, minutes) * D(str(round(self.rng.uniform(.85, 1.2), 2))))).quantize(D("0.01"))
            else:
                kcal = None
            cree = fin + dt.timedelta(minutes=self.rng.randint(5, 120))
        cree = min(cree, self.maintenant(p))
        if cree < fin:
            sys.exit("Séance non terminée à la date de référence : %s" % p["cle"])
        cle = "%s:%s:%s" % (p["cle"], jour.isoformat(), heure)
        self.t["activity"].append([Hex(uid("activity", cle)), debut, jour_local, minutes, kcal, statut, source,
                                   Hex(uid("health", "activity", cle)) if source == "health" or ecrite else None, ignoree,
                                   cree, cree, p["id"], a["id"]])
        p["seances"].append({"jour": jour, "code": code, "min": minutes, "kcal": kcal, "statut": statut, "ignoree": ignoree,
                             "source": source, "poids": poids})

    # -- connexions (RG53) --
    def connexions(self, p, debut, fin, ecart=(1, 6), exclure=None):
        jour = debut
        while True:
            if exclure and exclure[0] <= jour < exclure[1]:
                jour += dt.timedelta(days=1)
                continue
            instant = self.instant(p, jour, self.rng.randint(7, 21), self.rng.randint(0, 59)) if jour != debut else \
                self.instant(p, jour, *p["heure_inscription"]) + dt.timedelta(minutes=5)
            if instant > fin:
                break
            self.t["login_event"].append([Hex(uid("login_event", p["cle"], jour.isoformat())), instant, p["id"]])
            jour += dt.timedelta(days=self.rng.randint(*ecart))

    # ===== Zak LeBoss =====
    def zak(self):
        p = ZAK
        p.update(repas=[], seances=[], heure_inscription=(8, 5))
        debut = self.ref - dt.timedelta(days=41)
        p["debut"] = debut
        p.setdefault("zone", "Europe/Paris")
        cree = self.instant(p, debut, 8, 5)
        self.compte(p, cree, modifie=cree + dt.timedelta(days=21))
        self.sante(p, debut)
        self.echelle(p, objectif_calcule(p, p["poids"], debut.year))
        jours = [debut + dt.timedelta(days=i) for i in range(42)]

        # pesées : à l'inscription puis environ 2 par semaine, en légère baisse
        pesees = [debut]
        for lundi in sorted({j - dt.timedelta(days=j.weekday()) for j in jours}):
            for choix in ((0, 1), (3, 4, 5)):
                cand = [lundi + dt.timedelta(days=c) for c in choix]
                cand = [c for c in cand if debut < c <= self.ref and c - pesees[-1] >= dt.timedelta(days=2)]
                if cand:
                    pesees.append(self.rng.choice(cand))
        self.pesees(p, pesees, debut)

        # aliment personnalisé et favoris
        perso_cree = self.instant(p, debut + dt.timedelta(days=3), 18, 40)
        self.t["food"].append([ALIMENTS[PERSO]["id"], None, ALIMENTS[PERSO]["nom"], None, ALIMENTS[PERSO]["kcal"],
                               ALIMENTS[PERSO]["p"], ALIMENTS[PERSO]["g"], ALIMENTS[PERSO]["l"], D("2.00"), None,
                               False, False, True, False, False, False, perso_cree, None, p["id"]])
        for c in sorted(ALIMENTS[PERSO]["allergenes"]):
            self.t["food_allergen"].append([ALIMENTS[PERSO]["id"], Hex(GEN.uid("allergen", c))])
        favoris = {}
        for k, (nom, type_, elements) in enumerate(FAVORIS_ZAK):
            id_f = Hex(uid("favorite_meal", "zak", str(k)))
            cree_f = self.instant(p, debut + dt.timedelta(days=2 + 3 * k), 13, 10)
            self.t["favorite_meal"].append([id_f, nom, cree_f, p["id"]])
            lignes = [self.ligne(p, c, qte if qte[0] == "u" else ("g", qte[1]), fixe=True) for c, qte in elements]
            for i, l in enumerate(lignes):
                self.t["favorite_item"].append([Hex(uid("favorite_item", "zak", str(k), str(i))), l["q"], l["n"], id_f,
                                                ALIMENTS[l["code"]]["id"], l["portion"]])
            favoris[type_] = (debut + dt.timedelta(days=2 + 3 * k), lignes)

        # repas : 3 par jour, plus une collation un jour sur deux environ
        pd, dej, din, col = (self.modeles(p, c) for c in (PETIT_DEJ, DEJEUNER, DINER, COLLATION))
        for j in jours:
            for type_, catalogue, heure in (("breakfast", pd, (7, 45)), ("lunch", dej, (12, 40)), ("dinner", din, (19, 50))):
                fav = favoris.get(type_)
                if fav and j > fav[0] and self.rng.random() < (.3 if type_ == "breakfast" else .2):
                    self.repas(p, j, type_, [dict(l) for l in fav[1]], "favorite", heure)
                    continue
                noms = sorted(catalogue)
                if type_ == "breakfast" and j <= debut + dt.timedelta(days=3):
                    noms.remove("pancakes")
                lignes = self.composer(p, catalogue[self.rng.choice(noms)], accompagner=type_ != "breakfast")
                if type_ == "dinner" and j.weekday() in (4, 5) and self.rng.random() < .4:
                    lignes.append(self.ligne(p, "5214", u(1)))
                self.repas(p, j, type_, lignes, "manual", heure)
            if self.rng.random() < .55:
                noms = sorted(col)
                if j <= debut + dt.timedelta(days=3):
                    noms.remove("pancakes")
                self.repas(p, j, "snack", self.composer(p, col[self.rng.choice(noms)]), "manual", (16, 15))

        # séances : 3 à 5 par semaine glissante et par semaine civile complète, dont certaines importées de Santé
        types = [("12050", 30), ("02054", 30), ("01040", 10), ("02214", 10), ("17200", 10), ("12030", 10)]
        duree = {"12050": (30, 50), "02054": (45, 70), "01040": (50, 90), "02214": (20, 30), "17200": (35, 60), "12030": (30, 45)}
        for _ in range(500):
            choisis = set()
            for lundi in sorted({j - dt.timedelta(days=j.weekday()) for j in jours}):
                semaine = [j for j in jours if lundi <= j < lundi + dt.timedelta(days=7)]
                n = self.rng.randint(3, 5) if len(semaine) == 7 else max(1, round(len(semaine) / 7 * self.rng.uniform(3, 5)))
                choisis |= set(self.rng.sample(semaine, min(n, len(semaine))))
            blocs = [sum(1 for j in choisis if 0 <= (self.ref - j).days - 7 * b < 7) for b in range(6)]
            if all(3 <= x <= 5 for x in blocs):
                break
        else:
            sys.exit("Planning des séances de Zak introuvable")
        for j in sorted(choisis):
            code = self.rng.choices([c for c, _ in types], [w for _, w in types])[0]
            minutes = self.rng.randint(*duree[code])
            heure = (10, 0) if j.weekday() >= 5 else ((18, 45) if self.rng.random() < .7 else (7, 40))
            if j == self.ref:
                heure = (18, 0)
            source = "health" if code in CODES_SANTE and code != "02054" and self.rng.random() < .45 else "manual"
            statut = None if source == "health" else ("estimated" if self.rng.random() < .85 else "entered")
            # à partir de la 2e semaine, Zak laisse ZakFit écrire ses séances saisies dans Santé (health_uuid, RG33)
            self.seance(p, j, code, minutes, heure, source=source, statut=statut, ecrite=j >= debut + dt.timedelta(days=7))
        # une séance importée supprimée par Zak : ignorée, sans kcal (RG33)
        libres = [j for j in jours[7:-7] if j not in choisis and j.weekday() < 5]
        self.seance(p, self.rng.choice(libres), "17190", 25, (12, 30), source="health", ignoree=True)

        # énergie active importée de Santé, certains jours
        for j in jours:
            if self.rng.random() < .8:
                importees = sum((s["kcal"] or 0) for s in p["seances"] if s["jour"] == j and s["source"] == "health")
                kcal = q2(D(self.rng.randint(240, 520)) + D(self.rng.randint(0, 99)) / 100 + importees)
                importe = min(self.instant(p, j + dt.timedelta(days=1), 7, 30), self.maintenant(p))
                self.t["daily_active_energy"].append([Hex(uid("daily_active_energy", "zak", j.isoformat())), j, kcal, importe, p["id"]])

        # objectif calorique calculé, versionné à chaque pesée qui change la cible, macros personnalisées au 15e jour
        evenements = [(j, "pesee", w) for j, w in p["pesees"]] + [(debut + dt.timedelta(days=14), "macros", (150, 245, 75))]
        self.objectif_calorique(p, evenements)

        # objectifs d'activité : 3 puis 4 séances par semaine (RG37), minutes par semaine, kcal par séance de cardio
        bascule = debut + dt.timedelta(days=21)
        objectifs = [("sessions", "week", 3, debut, bascule - dt.timedelta(days=1), None),
                     ("sessions", "week", 4, bascule, None, None),
                     ("minutes", "week", 150, debut, None, None),
                     ("kcal", "session", 350, debut + dt.timedelta(days=7), None, "cardio")]
        for k, (metrique, periode, val, de, a, cat) in enumerate(objectifs):
            self.t["activity_goal"].append([Hex(uid("activity_goal", "zak", str(k))), metrique, periode, val, de, a,
                                            self.instant(p, de, 8, 20), p["id"],
                                            Hex(GEN.uid("activity_category", cat)) if cat else None])
        # réglages des rappels (RG42)
        self.rappels(p, [("weigh_in_reminder", True, dt.time(7, 30)), ("motivation", True, dt.time(9, 0)),
                         ("evening_encouragement", False, dt.time(20, 30))])
        self.connexions(p, debut, self.maintenant(p), (2, 5))

    # ===== Autres utilisateurs =====
    def autre(self, p):
        p.update(repas=[], seances=[], heure_inscription=(self.rng.randint(8, 21), self.rng.randint(0, 59)))
        p.setdefault("zone", "Europe/Paris")
        debut = self.ref - dt.timedelta(days=p["inscrit"])
        cree = self.instant(p, debut, *p["heure_inscription"])
        statut, bloque, fin_activite, modifie = "active", None, self.maintenant(p), None
        if p["cle"] in STATUTS:
            statut, jours_avant = STATUTS[p["cle"]]
            moment = self.instant(p, self.ref - dt.timedelta(days=jours_avant), 10, 15)
            fin_activite, modifie = moment - dt.timedelta(hours=2), moment
            if statut == "blocked":
                bloque = self.instant(p, self.ref + dt.timedelta(days=6), 0, 0)
            p["moment_statut"] = moment
        if p["cle"] == LEVEE[0]:
            modifie = self.instant(p, self.ref - dt.timedelta(days=LEVEE[2]), 9, 5)
        self.compte(p, cree, statut=statut, bloque_jusqua=bloque, modifie=modifie)
        consent = p.get("consentement", "actif")
        self.echelle(p, p["manuel"][1] if consent == "jamais" else objectif_calcule(p, p["poids"], debut.year))
        dernier_jour = fin_activite.date()
        jours = [debut + dt.timedelta(days=i) for i in range((dernier_jour - debut).days + 1)]
        bloc = None
        if p["cle"] == LEVEE[0]:
            bloc = (self.ref - dt.timedelta(days=LEVEE[1]), self.ref - dt.timedelta(days=LEVEE[2]))
            jours = [j for j in jours if not bloc[0] <= j < bloc[1]]

        if consent == "actif":
            self.sante(p, debut)
            pesees = [debut] + [j for j in jours[1:] if j.weekday() == self.rng.choice((0, 5, 6)) and self.rng.random() < .75]
            self.pesees(p, pesees, debut)
        elif consent == "retire":
            retrait_jour = debut + dt.timedelta(days=p["retrait"])
            retrait = self.instant(p, retrait_jour, 20, 10)
            self.sante(p, debut, retrait=retrait)
            # les pesées d'avant le retrait sont effacées (RG11) : on ne garde que leur effet sur l'objectif
            p["pesees"] = [(debut, D(str(p["poids"])))]
            p["retrait_jour"] = retrait_jour

        # repas
        pd, dej, din, col = (self.modeles(p, c) for c in (PETIT_DEJ, DEJEUNER, DINER, COLLATION))
        for j in jours:
            if self.rng.random() > p["assiduite"]:
                continue
            fait = 0
            for type_, catalogue, proba, heure in (("breakfast", pd, .8, (8, 0)), ("lunch", dej, .95, (12, 50)),
                                                   ("dinner", din, .9, (20, 0)), ("snack", col, .4, (16, 30))):
                if self.rng.random() < proba or (type_ == "snack" and fait == 0):
                    lignes = self.composer(p, catalogue[self.rng.choice(sorted(catalogue))], accompagner=type_ in ("lunch", "dinner"))
                    if type_ == "dinner" and j.weekday() in (4, 5):
                        for code, qte, _ in EXTRAS_DINER:
                            if self.compatible(p, code) and self.rng.random() < .2:
                                lignes.append(self.ligne(p, code, qte))
                    instant = self.instant(p, j, *heure)
                    if j == debut and instant < cree or instant > fin_activite:
                        continue
                    self.repas(p, j, type_, lignes, "manual", heure)
                    fait += 1

        # séances
        for lundi in sorted({j - dt.timedelta(days=j.weekday()) for j in jours}):
            semaine = [j for j in jours if lundi <= j < lundi + dt.timedelta(days=7) and j > debut]
            if not semaine:
                continue
            n = min(len(semaine), self.rng.randint(*p["nb_seances"]))
            for j in sorted(self.rng.sample(semaine, n)):
                code = self.rng.choice(p["types"])
                met = ACTIVITES[code]["met"]
                minutes = self.rng.choice((20, 30, 40, 45, 60, 75, 90)) if met < 6 else self.rng.choice((20, 30, 45, 60, 75))
                heure = (10, 30) if j.weekday() >= 5 else (18, 30)
                if self.instant(p, j, *heure) + dt.timedelta(minutes=minutes + 60) > fin_activite:
                    continue
                if consent == "actif" and p.get("sante") and code in CODES_SANTE and self.rng.random() < .4:
                    self.seance(p, j, code, minutes, heure, source="health")
                elif consent == "actif":
                    self.seance(p, j, code, minutes, heure, statut="estimated" if self.rng.random() < .7 else "entered")
                elif consent == "retire":
                    # avant le retrait, ses kcal étaient estimées : elles sont effacées (RG11)
                    statut = "unknown" if j < p["retrait_jour"] or self.rng.random() < .5 else "entered"
                    self.seance(p, j, code, minutes, heure, statut=statut)
                else:
                    self.seance(p, j, code, minutes, heure, statut="entered" if self.rng.random() < .5 else "unknown")
        if p["cle"] == "thomas":
            # une séance importée de Santé, puis supprimée : ignorée
            libre = [j for j in jours[7:] if all(s["jour"] != j for s in p["seances"]) and j.weekday() < 5]
            self.seance(p, libre[0], "17190", 30, (12, 15), source="health", ignoree=True)

        if consent == "actif" and p.get("sante"):
            for j in jours:
                if j > debut and self.rng.random() < .8:
                    importees = sum((s["kcal"] or 0) for s in p["seances"] if s["jour"] == j and s["source"] == "health")
                    kcal = q2(D(self.rng.randint(150, 600)) + D(self.rng.randint(0, 99)) / 100 + importees)
                    importe = min(self.instant(p, j + dt.timedelta(days=1), 7, 45), fin_activite)
                    self.t["daily_active_energy"].append([Hex(uid("daily_active_energy", p["cle"], j.isoformat())), j, kcal,
                                                          importe, p["id"]])

        # objectif calorique
        if consent == "jamais":
            p["versions"] = []
            self.objectif_calorique_manuel(p, debut)
        else:
            evenements = [(j, "pesee", w) for j, w in p.get("pesees", [])]
            if "manuel" in p:
                evenements.append((debut + dt.timedelta(days=p["manuel"][0]), "manuel", p["manuel"][1]))
            if "macros_perso" in p:
                evenements.append((debut + dt.timedelta(days=5), "macros", p["macros_perso"]))
            if consent == "retire":
                evenements.append((p["retrait_jour"], "retrait", None))
            self.objectif_calorique(p, evenements)

        # objectifs d'activité
        objectifs = {
            "lucas": [("sessions", "week", 4, 0, None, None)],
            "mehdi": [("minutes", "week", 300, 2, None, None)],
            "julie": [("sessions", "week", 3, 0, None, None), ("kcal", "session", 350, 3, None, "cardio")],
            "thomas": [("minutes", "week", 120, 1, 30, None), ("minutes", "week", 150, 31, None, None)],
            "camille": [("sessions", "week", 3, 0, None, None)],
            "karim": [("sessions", "week", 3, 4, None, None)],
            "ines": [("minutes", "day", 30, 0, None, "walking")],
            "emilie": [("sessions", "week", 2, 3, None, None)],
        }.get(p["cle"], [])
        for k, (metrique, periode, val, de, a, cat) in enumerate(objectifs):
            jour_de = debut + dt.timedelta(days=de)
            self.t["activity_goal"].append([Hex(uid("activity_goal", p["cle"], str(k))), metrique, periode, val, jour_de,
                                            debut + dt.timedelta(days=a) if a is not None else None,
                                            max(self.instant(p, jour_de, 21, 0), p["cree"] + dt.timedelta(minutes=10)), p["id"],
                                            Hex(GEN.uid("activity_category", cat)) if cat else None])
        self.rappels(p, {
            "ines": [("weigh_in_reminder", True, dt.time(7, 0))],
            "lucas": [("workout_reminder", True, dt.time(17, 30)), ("motivation", False, dt.time(18, 0))],
            "julie": [("evening_encouragement", True, dt.time(21, 0))],
            "nathalie": [("motivation", True, dt.time(10, 0)), ("weigh_in_reminder", True, dt.time(7, 15))],
            "romain": [("workout_reminder", False, dt.time(18, 0))],
        }.get(p["cle"], []))
        self.connexions(p, debut, fin_activite, exclure=bloc if p["cle"] == LEVEE[0] else None)

    def rappels(self, p, personnalises):
        # l'inscription crée les 4 réglages par défaut (actifs, 18 h, RG42), puis l'utilisateur en personnalise certains
        choix = {kind: (actif, heure) for kind, actif, heure in personnalises}
        for kind in ("workout_reminder", "weigh_in_reminder", "motivation", "evening_encouragement"):
            actif, heure = choix.get(kind, (True, dt.time(18, 0)))
            self.t["reminder_setting"].append([Hex(uid("reminder_setting", p["cle"], kind)), kind, actif, heure, p["id"]])

    def objectif_calorique_manuel(self, p, debut):
        kcal = p["manuel"][1]
        id_goal = Hex(uid("calorie_goal", p["cle"]))
        m = macros(kcal)
        self.t["calorie_goal"].append([id_goal, "manual", kcal, m[0], m[1], m[2], False, p["cree"] + dt.timedelta(minutes=8), p["id"]])
        self.t["calorie_target_history"].append([Hex(uid("calorie_target_history", p["cle"], debut.isoformat())), debut,
                                                 kcal, m[0], m[1], m[2], "manual", id_goal])
        p["versions"] = [(debut, (kcal,) + m + ("manual",))]

    # ===== Administrateur =====
    def admin(self):
        p = ADMIN
        p.update(heure_inscription=(9, 0), zone="Europe/Paris")
        debut = self.ref - dt.timedelta(days=p["inscrit"])
        self.compte(p, self.instant(p, debut, 9, 0), role="admin")
        self.connexions(p, debut, self.maintenant(p), (3, 7))
        par_cle = {x["cle"]: x for x in AUTRES}
        actions = [
            ("update", "food", Hex(GEN.uid("food", "25429")), 30, (11, 20)),
            ("update", "activity_type", Hex(GEN.uid("activity_type", "02214")), 28, (14, 5)),
            ("block", "user", par_cle["lea"]["id"], LEVEE[1], (10, 12)),
            ("reactivate", "user", par_cle["lea"]["id"], LEVEE[2], (9, 5)),
            ("delete_user", "user", Hex(uid("user", "compte-supprime")), 18, (16, 40)),
            ("suspend", "user", par_cle["yanis"]["id"], STATUTS["yanis"][1], (10, 15)),
            ("block", "user", par_cle["romain"]["id"], STATUTS["romain"][1], (10, 15)),
        ]
        for k, (action, cible, id_cible, jours_avant, heure) in enumerate(actions):
            self.t["admin_action"].append([Hex(uid("admin_action", str(k))), action, cible, id_cible,
                                           self.instant(p, self.ref - dt.timedelta(days=jours_avant), *heure), p["id"]])

    def generer(self):
        self.zak()
        for p in AUTRES:
            self.autre(p)
        self.admin()
        self.controler()
        return self

    # ---------- Contrôles internes ----------
    def controler(self):
        for p in [ZAK] + AUTRES:
            for r in p["repas"]:
                if not r["lignes"]:
                    sys.exit("Repas sans ligne : %s %s" % (p["cle"], r["jour"]))
        emails = [r[3] for r in self.t["user"]]
        if len(set(emails)) != len(emails):
            sys.exit("Emails en double")
        consentis = [p for p in [ZAK] + AUTRES if p.get("consentement", "actif") == "actif"]
        annee = self.ref.year
        for nom, cle in (("sexe", lambda p: p["sexe"]), ("orientation", lambda p: p["orientation"]),
                         ("âge", lambda p: tranche(annee - p["naissance"]))):
            groupes = {}
            for p in consentis:
                groupes[cle(p)] = groupes.get(cle(p), 0) + 1
            if min(groupes.values()) < 5:
                sys.exit("RG47 : groupe de moins de 5 personnes par %s : %s" % (nom, groupes))
            self.attendu[nom] = groupes
        z = ZAK
        jour = [r for r in z["repas"] if r["jour"] == self.ref]
        self.attendu["jour_zak"] = tuple(sum((l[k] for r in jour for l in r["lignes"]), D(0)) for k in ("kcal", "p", "g", "l"))
        self.attendu["repas_zak"] = blocs(self.ref, [r["jour"] for r in z["repas"]])
        self.attendu["seances_zak"] = blocs(self.ref, [s["jour"] for s in z["seances"] if not s["ignoree"]])
        self.attendu["versions_zak"] = z["versions"]

    # ---------- SQL ----------
    def sql(self, empreintes):
        colonnes = {
            "user": "id_user, last_name, first_name, email, password_hash, role, status, blocked_until, adult_declared_at, time_zone, created_at, updated_at",
            "health_profile": "id_health_profile, birth_year, sex, height_cm, activity_level, goal_orientation, meat_preference, is_vegetarian, is_vegan, updated_at, id_user",
            "health_consent": "id_health_consent, text_version, granted_at, withdrawn_at, id_user",
            "health_profile_allergen": "id_health_profile, id_allergen",
            "food": "id_food, ciqual_code, name_fr, name_en, kcal_100g, protein_100g, carbs_100g, fat_100g, fiber_100g, alcohol_100g, contains_meat, contains_pork, contains_animal_product, contains_alcohol, labels_verified, is_archived, created_at, id_food_group, id_user",
            "food_allergen": "id_food, id_allergen",
            "favorite_meal": "id_favorite_meal, name, created_at, id_user",
            "favorite_item": "id_favorite_item, quantity_g, portion_count, id_favorite_meal, id_food, id_food_portion",
            "meal": "id_meal, meal_type, eaten_on, origin, created_at, updated_at, id_user",
            "meal_item": "id_meal_item, quantity_g, portion_count, kcal, protein_g, carbs_g, fat_g, estimated_g, id_meal, id_food, id_food_portion",
            "activity": "id_activity, performed_at, performed_on, duration_min, kcal, kcal_status, source, health_uuid, is_ignored, created_at, updated_at, id_user, id_activity_type",
            "daily_active_energy": "id_daily_active_energy, day, kcal, imported_at, id_user",
            "weigh_in": "id_weigh_in, weighed_on, weight_kg, source, health_uuid, is_ignored, created_at, id_user",
            "calorie_goal": "id_calorie_goal, mode, manual_kcal, protein_g_target, carbs_g_target, fat_g_target, macros_custom, updated_at, id_user",
            "calorie_target_history": "id_calorie_target_history, effective_from, kcal_target, protein_g_target, carbs_g_target, fat_g_target, mode, id_calorie_goal",
            "activity_goal": "id_activity_goal, metric, period, target_value, valid_from, valid_to, created_at, id_user, id_activity_category",
            "reminder_setting": "id_reminder_setting, kind, is_enabled, send_time, id_user",
            "login_event": "id_login_event, logged_in_at, id_user",
            "admin_action": "id_admin_action, action, target_kind, target_id, performed_at, id_user",
        }
        L = ["-- ZakFit : données fictives de démonstration. Généré par docs/conception/donnees/outils/generer_demo.py,",
             "-- ne pas modifier à la main. Date de référence : %s. À charger après 01-schema.sql et 02-referentiels.sql." % self.ref,
             "-- Comptes : Zak LeBoss (zak.leboss@example.com), %d autres utilisateurs, 1 administrateur (admin@example.com)." % len(AUTRES),
             "-- Mot de passe commun : celui de la variable DEMO_PASSWORD au moment de la génération (seules les empreintes bcrypt figurent ici).",
             "-- Attention : chargées avant la date de référence, ces données contiennent des dates futures, que l'API refuse (RG23, RG30).",
             "-- Pour le développement, régénérer avec --date-reference égal au jour même.",
             "SET NAMES utf8mb4;", "START TRANSACTION;", ""]
        for table, lignes in self.t.items():
            for i in range(0, len(lignes), 400):
                L.append("INSERT INTO `%s` (%s) VALUES\n" % (table, colonnes[table]) + ",\n".join(
                    "  (" + ", ".join(lit(v) for v in r) + ")" for r in lignes[i:i + 400]) + ";\n")
        L.append("COMMIT;")
        texte = "\n".join(L) + "\n"
        for cle, empreinte in empreintes.items():
            texte = texte.replace("@HASH_%s@" % cle, GEN.q(empreinte))
        return texte


def jour_dans_fuseau(instant_utc, zone):
    return instant_utc.replace(tzinfo=UTC).astimezone(ZoneInfo(zone)).date()


def tranche(age):
    return "18-29" if age < 30 else ("30-44" if age < 45 else "45+")


def blocs(ref, jours):
    """Nombre d'éléments par bloc de 7 jours finissant à la date de référence (bloc 0 = les 7 derniers jours)."""
    resultat = [0] * 6
    for j in jours:
        b = (ref - j).days // 7
        if 0 <= b < 6:
            resultat[b] += 1
    return resultat


def empreinte(mot_de_passe, htpasswd):
    # -i : le mot de passe passe par l'entrée standard, pas par la ligne de commande (invisible pour ps)
    r = subprocess.run([htpasswd, "-niBC", "12", "x"], input=mot_de_passe, capture_output=True, text=True)
    sortie = r.stdout.strip()
    if r.returncode != 0 or not sortie.startswith("x:$2y$12$"):
        sys.exit("htpasswd a échoué (code %d)" % r.returncode)
    resultat = "$2b$" + sortie[len("x:$2y$"):]
    if len(resultat) != 60:
        sys.exit("Empreinte bcrypt inattendue")
    return resultat


def verifier_mot_de_passe(m):
    if not m:
        sys.exit("DEMO_PASSWORD est obligatoire : exporte le mot de passe des comptes de démonstration.")
    if len(m) < 8 or len(m.encode("utf-8")) > 72 or not any(c.isalpha() for c in m) or not any(c.isdigit() for c in m):
        sys.exit("DEMO_PASSWORD ne respecte pas RG02 (8 caractères au moins, une lettre, un chiffre, 72 octets au plus).")


# ---------- Vérification sur une base chargée ----------

def verifier(jeu, commande):
    cmd = shlex.split(commande)

    def lire(sql):
        r = subprocess.run(cmd + ["-N", "-B", "-e", sql], capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit("Requête refusée : %s\n%s" % (sql[:80], r.stderr))
        return [l.split("\t") for l in r.stdout.strip().splitlines()]

    erreurs = []

    def ok(nom, condition, detail=""):
        print("%s %s%s" % ("OK " if condition else "ÉCHEC", nom, (" : " + detail) if detail else ""))
        if not condition:
            erreurs.append(nom)

    zak = "(SELECT id_user FROM `user` WHERE email = 'zak.leboss@example.com')"
    ref = jeu.ref.isoformat()

    for table, lignes in jeu.t.items():
        filtre = {"food": " WHERE id_user IS NOT NULL",
                  "food_allergen": " WHERE id_food IN (SELECT id_food FROM food WHERE id_user IS NOT NULL)"}.get(table, "")
        n = int(lire("SELECT COUNT(*) FROM `%s`%s" % (table, filtre))[0][0])
        ok("lignes de %s" % table, n == len(lignes), "%d" % n)

    n = lire("SELECT COUNT(*) FROM meal_item mi JOIN food f ON f.id_food = mi.id_food WHERE "
             "mi.kcal <> ROUND(f.kcal_100g * mi.quantity_g / 100, 2) OR mi.protein_g <> ROUND(f.protein_100g * mi.quantity_g / 100, 2) "
             "OR mi.carbs_g <> ROUND(f.carbs_100g * mi.quantity_g / 100, 2) OR mi.fat_g <> ROUND(f.fat_100g * mi.quantity_g / 100, 2)")[0][0]
    ok("valeurs figées des lignes = valeur pour 100 g × grammes / 100 (RG24)", n == "0", "%s écart(s)" % n)
    n = lire("SELECT COUNT(*) FROM meal_item mi JOIN food_portion fp ON fp.id_food_portion = mi.id_food_portion "
             "WHERE mi.quantity_g <> mi.portion_count * fp.grams")[0][0]
    ok("grammes = unités × poids de l'unité (RG20)", n == "0", "%s écart(s)" % n)
    n = lire("SELECT COUNT(*) FROM meal m WHERE NOT EXISTS (SELECT 1 FROM meal_item mi WHERE mi.id_meal = m.id_meal)")[0][0]
    ok("chaque repas a au moins une ligne (RG24)", n == "0")

    r = lire("SELECT SUM(mi.kcal), SUM(mi.protein_g), SUM(mi.carbs_g), SUM(mi.fat_g), "
             "SUM(ROUND(f.kcal_100g * mi.quantity_g / 100, 2)) FROM meal m JOIN meal_item mi ON mi.id_meal = m.id_meal "
             "JOIN food f ON f.id_food = mi.id_food WHERE m.id_user = %s AND m.eaten_on = '%s'" % (zak, ref))[0]
    attendu = jeu.attendu["jour_zak"]
    ok("totaux de Zak le %s (kcal, P, G, L)" % ref, tuple(D(x) for x in r[:4]) == attendu and D(r[4]) == attendu[0],
       "base %s / attendu %s" % (" ; ".join(r[:4]), " ; ".join(str(x) for x in attendu)))

    def par_bloc(table, colonne, condition=""):
        lignes = lire("SELECT DATEDIFF('%s', %s) DIV 7 AS b, COUNT(*) FROM %s WHERE id_user = %s %s GROUP BY b ORDER BY b"
                      % (ref, colonne, table, zak, condition))
        resultat = [0] * 6
        for b, n in lignes:
            if 0 <= int(b) < 6:
                resultat[int(b)] = int(n)
        return resultat

    repas = par_bloc("meal", "eaten_on")
    ok("repas de Zak par semaine glissante (du plus récent au plus ancien)", repas == jeu.attendu["repas_zak"] and
       all(21 <= n <= 28 for n in repas), str(repas))
    seances = par_bloc("activity", "performed_on", "AND is_ignored = FALSE")
    ok("séances de Zak par semaine glissante, 3 à 5", seances == jeu.attendu["seances_zak"] and all(3 <= n <= 5 for n in seances),
       str(seances))
    iso = lire("SELECT YEARWEEK(performed_on, 3), COUNT(*), COUNT(DISTINCT performed_on) FROM activity WHERE id_user = %s "
               "AND is_ignored = FALSE GROUP BY 1 ORDER BY 1" % zak)
    print("    séances de Zak par semaine ISO (semaine, séances) : %s" % ", ".join("%s=%s" % (a, b) for a, b, _ in iso))
    debut = jeu.ref - dt.timedelta(days=41)
    completes = [(a, int(b)) for a, b, _ in iso
                 if dt.date.fromisocalendar(int(a[:4]), int(a[4:]), 1) >= debut and dt.date.fromisocalendar(int(a[:4]), int(a[4:]), 7) <= jeu.ref]
    ok("séances de Zak par semaine ISO complète, 3 à 5", all(3 <= n <= 5 for _, n in completes), str([n for _, n in completes]))
    iso_repas = lire("SELECT YEARWEEK(eaten_on, 3), COUNT(*) FROM meal WHERE id_user = %s GROUP BY 1 ORDER BY 1" % zak)
    print("    repas de Zak par semaine ISO : %s" % ", ".join("%s=%s" % (a, b) for a, b in iso_repas))

    ecarts, lignes = 0, lire("SELECT a.performed_at, a.performed_on, u.time_zone FROM activity a JOIN `user` u USING (id_user)")
    for instant, jour, zone in lignes:
        if jour_dans_fuseau(dt.datetime.fromisoformat(instant), zone).isoformat() != jour:
            ecarts += 1
    ok("performed_on = jour local de performed_at dans user.time_zone (RG38)", ecarts == 0 and len(lignes) == len(jeu.t["activity"]),
       "%d séances, %d écart(s)" % (len(lignes), ecarts))
    r = lire("SELECT (SELECT COUNT(*) FROM weigh_in WHERE is_ignored = TRUE AND id_user = %s), "
             "(SELECT COUNT(*) FROM (SELECT id_user FROM weigh_in WHERE is_ignored = TRUE GROUP BY id_user HAVING COUNT(*) > 1) x), "
             "(SELECT COUNT(*) FROM weigh_in WHERE is_ignored = TRUE AND source <> 'health')" % zak)[0]
    ok("pesées ignorées : une chez Zak, au plus une par utilisateur, toutes importées", r == ["1", "0", "0"], " / ".join(r))
    n = lire("SELECT COUNT(*) FROM activity a JOIN activity_type t ON t.id_activity_type = a.id_activity_type "
             "WHERE a.kcal_status = 'estimated' AND a.kcal <> ROUND((t.met - 1) * (SELECT w.weight_kg FROM weigh_in w "
             "WHERE w.id_user = a.id_user AND w.is_ignored = FALSE AND w.weighed_on <= a.performed_on ORDER BY w.weighed_on DESC LIMIT 1) "
             "* a.duration_min / 60, 2)")[0][0]
    total = lire("SELECT COUNT(*) FROM activity WHERE kcal_status = 'estimated'")[0][0]
    ok("kcal estimées = (MET − 1) × poids du jour × heures", n == "0", "%s séances estimées, %s écart(s)" % (total, n))

    calcul = ("LEAST(6000, CEILING(GREATEST(ree * pal + adj, ree, 1200) / 10) * 10)")
    sous = ("SELECT h.kcal_target, h.protein_g_target, h.carbs_g_target, h.fat_g_target, g.macros_custom, "
            "ROUND(10 * (SELECT w.weight_kg FROM weigh_in w WHERE w.id_user = g.id_user AND w.is_ignored = FALSE "
            "AND w.weighed_on <= h.effective_from "
            "ORDER BY w.weighed_on DESC LIMIT 1) + 6.25 * p.height_cm - 5 * (YEAR(h.effective_from) - p.birth_year) "
            "+ IF(p.sex = 'male', 5, -161)) AS ree, "
            "ELT(FIELD(p.activity_level, 'low', 'moderate', 'active', 'very_active'), 1.4, 1.6, 1.8, 2.0) AS pal, "
            "ELT(FIELD(p.goal_orientation, 'lose', 'maintain', 'gain'), -500, 0, 300) AS adj "
            "FROM calorie_target_history h JOIN calorie_goal g ON g.id_calorie_goal = h.id_calorie_goal "
            "JOIN health_profile p ON p.id_user = g.id_user WHERE h.mode = 'computed'")
    r = lire("SELECT COUNT(*), SUM(kcal_target <> %s), SUM(macros_custom = FALSE AND (protein_g_target <> ROUND(kcal_target * 0.15 / 4) "
             "OR carbs_g_target <> ROUND(kcal_target * 0.48 / 4) OR fat_g_target <> ROUND(kcal_target * 0.37 / 9))) FROM (%s) x"
             % (calcul, sous))[0]
    ok("versions calculées = Mifflin-St Jeor × PAL ± orientation, plancher, dizaine supérieure ; macros 15/48/37",
       r[1] == "0" and r[2] == "0", "%s versions calculées, %s écart(s) kcal, %s écart(s) macros" % tuple(r))
    r = lire("SELECT h.effective_from, h.kcal_target, h.protein_g_target, h.carbs_g_target, h.fat_g_target, h.mode "
             "FROM calorie_target_history h JOIN calorie_goal g ON g.id_calorie_goal = h.id_calorie_goal "
             "WHERE g.id_user = %s ORDER BY h.effective_from" % zak)
    ok("historique de l'objectif de Zak : au moins 2 versions, dont une calculée (RG52)",
       len(r) >= 2 and any(x[5] == "computed" for x in r), " | ".join("%s %s kcal P%s G%s L%s %s" % tuple(x) for x in r))
    r = lire("SELECT COUNT(*), SUM(valid_to IS NOT NULL) FROM activity_goal WHERE id_user = %s" % zak)[0]
    ok("objectifs d'activité de Zak, dont un versionné (RG37)", int(r[1]) >= 1, "%s objectifs, %s clos" % tuple(r))

    sans = ("(SELECT u.id_user FROM `user` u WHERE NOT EXISTS (SELECT 1 FROM health_consent c "
            "WHERE c.id_user = u.id_user AND c.withdrawn_at IS NULL))")
    r = lire("SELECT (SELECT COUNT(*) FROM weigh_in WHERE id_user IN %s), (SELECT COUNT(*) FROM daily_active_energy WHERE id_user IN %s), "
             "(SELECT COUNT(*) FROM activity WHERE id_user IN %s AND (source = 'health' OR kcal_status = 'estimated')), "
             "(SELECT COUNT(*) FROM health_profile p WHERE id_user IN %s), "
             "(SELECT COUNT(*) FROM calorie_target_history h JOIN calorie_goal g ON g.id_calorie_goal = h.id_calorie_goal "
             "WHERE g.id_user IN %s AND h.mode = 'computed')" % ((sans,) * 5))[0]
    ok("aucune donnée de santé sans consentement actif (RG10, RG11)", r == ["0"] * 5,
       "pesées, énergie active, séances Santé ou estimées, profils de santé, versions calculées : %s" % " / ".join(r))
    r = lire("SELECT (SELECT COUNT(*) FROM health_profile), (SELECT COUNT(*) FROM health_consent WHERE withdrawn_at IS NULL), "
             "(SELECT COUNT(*) FROM health_profile_allergen hpa JOIN health_profile p USING (id_health_profile) WHERE p.id_user IN %s)" % sans)[0]
    ok("aucun profil de santé sans consentement actif : profils = consentements actifs (RG11)", r[0] == r[1] and r[2] == "0",
       "%s profils, %s consentements actifs, %s allergène(s) orphelin(s)" % tuple(r))
    codes = ", ".join("'%s'" % c for c in sorted(CODES_SANTE))
    r = lire("SELECT COUNT(*), SUM(t.compendium_code NOT IN (%s)) FROM activity a JOIN activity_type t USING (id_activity_type) "
             "WHERE a.source = 'health'" % codes)[0]
    ok("séances importées : seulement des codes de la table Santé de 05-contrat-api.md §6 (RG33)", r[1] == "0",
       "%s séances importées, %s hors table" % tuple(r))
    r = lire("SELECT COUNT(*), SUM(n <> 4) FROM (SELECT u.id_user, COUNT(r.id_reminder_setting) n FROM `user` u "
             "LEFT JOIN reminder_setting r ON r.id_user = u.id_user WHERE u.role = 'user' GROUP BY u.id_user) x")[0]
    ok("4 réglages de rappel par utilisateur (RG42)", r[1] == "0", "%s utilisateurs, %s sans leurs 4 réglages" % tuple(r))
    r = lire("SELECT (SELECT COUNT(*) FROM activity WHERE id_user = %s AND source = 'manual' AND health_uuid IS NOT NULL), "
             "(SELECT COUNT(*) FROM weigh_in WHERE id_user = %s AND source = 'manual' AND health_uuid IS NOT NULL)" % (zak, zak))[0]
    ok("séances et pesées saisies par Zak puis écrites dans Santé (health_uuid)", int(r[0]) > 0 and int(r[1]) > 0, " / ".join(r))
    r = lire("SELECT (SELECT COUNT(*) FROM meal m JOIN `user` u USING (id_user) WHERE m.created_at < u.created_at OR m.eaten_on > '%s'), "
             "(SELECT COUNT(*) FROM activity a JOIN `user` u USING (id_user) WHERE a.created_at < u.created_at OR a.performed_at > a.created_at), "
             "(SELECT COUNT(*) FROM weigh_in w JOIN `user` u USING (id_user) WHERE w.created_at < u.created_at OR w.weighed_on > '%s'), "
             "(SELECT COUNT(*) FROM login_event l JOIN `user` u USING (id_user) WHERE l.logged_in_at < u.created_at), "
             "(SELECT COUNT(*) FROM login_event l JOIN `user` u USING (id_user) WHERE u.status <> 'active' AND l.logged_in_at > u.updated_at)"
             % (ref, ref))[0]
    ok("dates : rien avant l'inscription ni après la référence, aucune connexion après un blocage", r == ["0"] * 5, " / ".join(r))
    n = lire("SELECT COUNT(*) FROM meal m JOIN meal_item mi ON mi.id_meal = m.id_meal JOIN food_allergen fa ON fa.id_food = mi.id_food "
             "JOIN health_profile p ON p.id_user = m.id_user JOIN health_profile_allergen hpa "
             "ON hpa.id_health_profile = p.id_health_profile AND hpa.id_allergen = fa.id_allergen")[0][0]
    ok("aucun aliment contenant un allergène déclaré dans les repas de son utilisateur", n == "0", "%s ligne(s)" % n)
    rep = {}
    for nom, sql in (
            ("sexe", "SELECT p.sex, COUNT(*) FROM health_profile p JOIN health_consent c ON c.id_user = p.id_user "
                     "AND c.withdrawn_at IS NULL WHERE p.sex IS NOT NULL GROUP BY p.sex"),
            ("orientation", "SELECT p.goal_orientation, COUNT(*) FROM health_profile p JOIN health_consent c ON c.id_user = p.id_user "
                            "AND c.withdrawn_at IS NULL WHERE p.goal_orientation IS NOT NULL GROUP BY 1"),
            ("âge", "SELECT CASE WHEN %d - birth_year < 30 THEN '18-29' WHEN %d - birth_year < 45 THEN '30-44' ELSE '45+' END AS t, "
                    "COUNT(*) FROM health_profile WHERE birth_year IS NOT NULL GROUP BY t" % (jeu.ref.year, jeu.ref.year))):
        groupes = {k: int(v) for k, v in lire(sql)}
        rep[nom] = groupes
        ok("répartition par %s, au moins 5 par groupe (RG47)" % nom,
           groupes == jeu.attendu[nom] and min(groupes.values()) >= 5, str(dict(sorted(groupes.items()))))
    r = lire("SELECT (SELECT COUNT(*) FROM `user` WHERE role = 'user'), (SELECT COUNT(*) FROM `user` WHERE role = 'admin'), "
             "(SELECT COUNT(*) FROM `user` WHERE status = 'blocked' AND blocked_until IS NOT NULL), "
             "(SELECT COUNT(*) FROM `user` WHERE status = 'suspended'), "
             "(SELECT COUNT(*) FROM `user` u WHERE role = 'user' AND NOT EXISTS (SELECT 1 FROM health_consent c "
             "WHERE c.id_user = u.id_user AND c.withdrawn_at IS NULL))")[0]
    ok("comptes : utilisateurs, administrateurs, bloqués avec date de fin, suspendus, sans consentement actif",
       r[1:4] == ["1", "1", "1"] and int(r[4]) >= 2, " / ".join(r))
    if erreurs:
        sys.exit("%d contrôle(s) en échec" % len(erreurs))
    print("Tous les contrôles passent.")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--date-reference", default=DATE_REFERENCE, help="dernier jour de l'historique (AAAA-MM-JJ)")
    parser.add_argument("--sortie", default=SORTIE)
    parser.add_argument("--htpasswd", default=HTPASSWD)
    parser.add_argument("--verifier", metavar="COMMANDE", help="contrôle une base déjà chargée, sans rien écrire")
    args = parser.parse_args()
    jeu = Jeu(dt.date.fromisoformat(args.date_reference)).generer()
    if args.verifier:
        verifier(jeu, args.verifier)
        return
    mot_de_passe = os.environ.get("DEMO_PASSWORD", "")
    verifier_mot_de_passe(mot_de_passe)
    empreintes = {p["cle"]: empreinte(mot_de_passe, args.htpasswd) for p in [ZAK] + AUTRES + [ADMIN]}
    open(args.sortie, "w", encoding="utf-8").write(jeu.sql(empreintes))
    print("Écrit : %s (date de référence %s)" % (os.path.relpath(args.sortie, CONCEPTION), jeu.ref))
    for table, lignes in jeu.t.items():
        print("  %-24s %6d" % (table, len(lignes)))
    k = jeu.attendu["jour_zak"]
    print("Zak, %s : %s kcal, P %s g, G %s g, L %s g" % (jeu.ref, *k))


if __name__ == "__main__":
    main()
