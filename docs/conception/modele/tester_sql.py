"""Rejoue les cas permis et interdits sur une base d'essai chargée avec sql/01-schema.sql et sql/02-referentiels.sql.

Usage : python3 -I modele/tester_sql.py "<commande mariadb complète, base comprise>"
Exemple : python3 -I modele/tester_sql.py "mariadb -u root zakfit_essai"
La base doit être une base d'essai : le script y crée puis supprime des données.
"""
import shlex
import subprocess
import sys

CMD = shlex.split(sys.argv[1])
U1 = "UNHEX('11111111111111111111111111111111')"
U2 = "UNHEX('22222222222222222222222222222222')"
ADMIN = "UNHEX('33333333333333333333333333333333')"
NOW = "'2026-11-25 10:00:00'"


def run(sql):
    r = subprocess.run(CMD + ["-N", "-e", sql], capture_output=True, text=True)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def user(uid, email, extra_cols="", extra_vals=""):
    return ("INSERT INTO `user` (id_user, last_name, first_name, email, password_hash, adult_declared_at, created_at, updated_at%s) "
            "VALUES (%s, 'Essai', 'Zak', '%s', REPEAT('x', 60), %s, %s, %s%s)" % (extra_cols, uid, email, NOW, NOW, NOW, extra_vals))


FOOD_BASE = "(SELECT id_food FROM food WHERE ciqual_code = '36018')"
TYPE_COURSE = "(SELECT id_activity_type FROM activity_type WHERE compendium_code = '12050')"
CAT_CARDIO = "(SELECT id_activity_category FROM activity_category WHERE code = 'cardio')"

PREPARATION = [
    user(U1, "zak.essai@example.test"),
    user(U2, "autre.essai@example.test"),
    user(ADMIN, "admin.essai@example.test", ", role", ", 'admin'"),
    "INSERT INTO health_profile (id_health_profile, birth_year, sex, height_cm, activity_level, goal_orientation, is_vegetarian, is_vegan, updated_at, id_user) "
    "VALUES (UNHEX(REPLACE(UUID(),'-','')), 1995, 'male', 178, 'moderate', 'maintain', FALSE, FALSE, %s, %s)" % (NOW, U1),
    "INSERT INTO health_consent (id_health_consent, text_version, granted_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-v1', %s, %s)" % (NOW, U1),
    "INSERT INTO food (id_food, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, created_at, id_user) "
    "VALUES (UNHEX('44444444444444444444444444444444'), 'Gâteau de mamie', 380, 5, 50, 18, %s, %s)" % (NOW, U1),
    "INSERT INTO food_portion (id_food_portion, label_fr, grams, id_food) VALUES (UNHEX('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'), '1 part', 90, UNHEX('44444444444444444444444444444444'))",
    "INSERT INTO meal (id_meal, meal_type, eaten_on, created_at, updated_at, id_user) VALUES (UNHEX('55555555555555555555555555555555'), 'lunch', '2026-11-25', %s, %s, %s)" % (NOW, NOW, U1),
    "INSERT INTO meal_item (id_meal_item, quantity_g, kcal, protein_g, carbs_g, fat_g, id_meal, id_food) "
    "VALUES (UNHEX(REPLACE(UUID(),'-','')), 150, 247.5, 46.5, 0, 5.4, UNHEX('55555555555555555555555555555555'), %s)" % FOOD_BASE,
    "INSERT INTO meal_item (id_meal_item, quantity_g, portion_count, kcal, protein_g, carbs_g, fat_g, id_meal, id_food, id_food_portion) "
    "VALUES (UNHEX(REPLACE(UUID(),'-','')), 90, 1, 342, 4.5, 45, 16.2, UNHEX('55555555555555555555555555555555'), UNHEX('44444444444444444444444444444444'), UNHEX('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'))",
    "INSERT INTO activity (id_activity, performed_at, duration_min, kcal, kcal_status, created_at, updated_at, id_user, id_activity_type) "
    "VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, 30, NULL, 'unknown', %s, %s, %s, %s)" % (NOW, NOW, NOW, U1, TYPE_COURSE),
    "INSERT INTO weigh_in (id_weigh_in, weighed_on, weight_kg, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-25', 72.4, %s, %s)" % (NOW, U1),
    "INSERT INTO weigh_in (id_weigh_in, weighed_on, weight_kg, source, health_uuid, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-20', 73.0, 'health', UNHEX('99999999999999999999999999999999'), %s, %s)" % (NOW, U1),
    "INSERT INTO activity (id_activity, performed_at, duration_min, kcal, kcal_status, created_at, updated_at, id_user, id_activity_type) "
    "VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, 45, 291, 'estimated', %s, %s, %s, %s)" % (NOW, NOW, NOW, U1, TYPE_COURSE),
    "INSERT INTO activity (id_activity, performed_at, duration_min, kcal, kcal_status, source, health_uuid, created_at, updated_at, id_user, id_activity_type) "
    "VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, 40, 350, 'entered', 'health', UNHEX('88888888888888888888888888888888'), %s, %s, %s, %s)" % (NOW, NOW, NOW, U1, TYPE_COURSE),
    "INSERT INTO daily_active_energy (id_daily_active_energy, day, kcal, imported_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-25', 620, %s, %s)" % (NOW, U1),
    "INSERT INTO food_allergen (id_food, id_allergen) SELECT UNHEX('44444444444444444444444444444444'), id_allergen FROM allergen WHERE code = 'oeufs'",
    "INSERT INTO calorie_goal (id_calorie_goal, mode, protein_g_target, carbs_g_target, fat_g_target, updated_at, id_user) VALUES (UNHEX('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'), 'computed', 94, 299, 102, %s, %s)" % (NOW, U1),
    "INSERT INTO calorie_target_history (id_calorie_target_history, effective_from, kcal_target, protein_g_target, carbs_g_target, fat_g_target, mode, id_calorie_goal) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-01', 2500, 94, 299, 102, 'computed', UNHEX('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'))",
    "INSERT INTO calorie_target_history (id_calorie_target_history, effective_from, kcal_target, protein_g_target, carbs_g_target, fat_g_target, mode, id_calorie_goal) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-20', 2400, 90, 290, 98, 'manual', UNHEX('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'))",
    "INSERT INTO login_event (id_login_event, logged_in_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, %s)" % (NOW, U1),
    "INSERT INTO activity_goal (id_activity_goal, metric, period, target_value, valid_from, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'sessions', 'week', 3, '2026-11-01', %s, %s)" % (NOW, U1),
    "INSERT INTO activity_goal (id_activity_goal, metric, period, target_value, valid_from, created_at, id_user, id_activity_category) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'sessions', 'week', 2, '2026-11-01', %s, %s, %s)" % (NOW, U1, CAT_CARDIO),
    "INSERT INTO reminder_setting (id_reminder_setting, kind, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'motivation', %s)" % U1,
    "INSERT INTO favorite_meal (id_favorite_meal, name, created_at, id_user) VALUES (UNHEX('66666666666666666666666666666666'), 'Midi habituel', %s, %s)" % (NOW, U1),
    "INSERT INTO favorite_item (id_favorite_item, quantity_g, id_favorite_meal, id_food) VALUES (UNHEX(REPLACE(UUID(),'-','')), 120, UNHEX('66666666666666666666666666666666'), UNHEX('44444444444444444444444444444444'))",
    "INSERT INTO health_profile_allergen (id_health_profile, id_allergen) SELECT hp.id_health_profile, a.id_allergen FROM health_profile hp, allergen a WHERE hp.id_user = %s AND a.code = 'arachides'" % U1,
    "INSERT INTO admin_action (id_admin_action, action, target_kind, target_id, performed_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'block', 'user', %s, %s, %s)" % (U2, NOW, ADMIN),
]

INTERDITS = [
    ("RG01 email en double", user("UNHEX('77777777777777777777777777777777')", "zak.essai@example.test")),
    ("RG06 fin de blocage sur un compte actif", "UPDATE `user` SET blocked_until = %s WHERE id_user = %s" % (NOW, U2)),
    ("R4 second profil de santé", "INSERT INTO health_profile (id_health_profile, updated_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, %s)" % (NOW, U1)),
    ("RG16 végan sans être végétarien", "UPDATE health_profile SET is_vegan = TRUE WHERE id_user = %s" % U1),
    ("RG16 végétarien avec préférence de viande", "UPDATE health_profile SET is_vegetarian = TRUE, meat_preference = 'halal' WHERE id_user = %s" % U1),
    ("RG13 taille de 90 cm", "UPDATE health_profile SET height_cm = 90 WHERE id_user = %s" % U1),
    ("RG10 second consentement actif", "INSERT INTO health_consent (id_health_consent, text_version, granted_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-v1', %s, %s)" % (NOW, U1)),
    ("RG11 retrait avant le consentement", "UPDATE health_consent SET withdrawn_at = '2026-01-01 00:00:00' WHERE id_user = %s" % U1),
    ("RG18 aliment à 950 kcal", "INSERT INTO food (id_food, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'X', 950, 0, 0, 100, %s, %s)" % (NOW, U1)),
    ("RG18 macros au-delà de 100,5 g", "INSERT INTO food (id_food, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'X', 500, 40, 40, 30, %s, %s)" % (NOW, U1)),
    ("RG19 aliment personnalisé avec code CIQUAL", "INSERT INTO food (id_food, ciqual_code, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '99999', 'X', 100, 1, 1, 1, %s, %s)" % (NOW, U1)),
    ("RG49 aliment de base sans nom anglais", "INSERT INTO food (id_food, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, created_at) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'X', 100, 1, 1, 1, %s)" % NOW),
    ("RG24 ligne de 0 g", "INSERT INTO meal_item (id_meal_item, quantity_g, kcal, protein_g, carbs_g, fat_g, id_meal, id_food) VALUES (UNHEX(REPLACE(UUID(),'-','')), 0, 0, 0, 0, 0, UNHEX('55555555555555555555555555555555'), %s)" % FOOD_BASE),
    ("R1 ligne vers un aliment inconnu", "INSERT INTO meal_item (id_meal_item, quantity_g, kcal, protein_g, carbs_g, fat_g, id_meal, id_food) VALUES (UNHEX(REPLACE(UUID(),'-','')), 10, 0, 0, 0, 0, UNHEX('55555555555555555555555555555555'), UNHEX('00000000000000000000000000000000'))"),
    ("RG30 séance de 0 min", "INSERT INTO activity (id_activity, performed_at, duration_min, kcal, kcal_status, created_at, updated_at, id_user, id_activity_type) VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, 0, 10, 'entered', %s, %s, %s, %s)" % (NOW, NOW, NOW, U1, TYPE_COURSE)),
    ("RG31 kcal vides mais état « saisies »", "INSERT INTO activity (id_activity, performed_at, duration_min, kcal, kcal_status, created_at, updated_at, id_user, id_activity_type) VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, 20, NULL, 'entered', %s, %s, %s, %s)" % (NOW, NOW, NOW, U1, TYPE_COURSE)),
    ("RG33 séance importée sans identifiant Santé", "INSERT INTO activity (id_activity, performed_at, duration_min, kcal, kcal_status, source, created_at, updated_at, id_user, id_activity_type) VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, 20, 100, 'entered', 'health', %s, %s, %s, %s)" % (NOW, NOW, NOW, U1, TYPE_COURSE)),
    ("RG39 deux pesées le même jour", "INSERT INTO weigh_in (id_weigh_in, weighed_on, weight_kg, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-25', 72.0, %s, %s)" % (NOW, U1)),
    ("RG13 pesée de 25 kg", "INSERT INTO weigh_in (id_weigh_in, weighed_on, weight_kg, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-24', 25, %s, %s)" % (NOW, U1)),
    ("RG36 objectif de protéines négatif", "UPDATE calorie_goal SET protein_g_target = -5 WHERE id_user = %s" % U1),
    ("RG35 objectif saisi de 1 000 kcal", "UPDATE calorie_goal SET mode = 'manual', manual_kcal = 1000 WHERE id_user = %s" % U1),
    ("R4 second objectif calorique", "INSERT INTO calorie_goal (id_calorie_goal, mode, protein_g_target, carbs_g_target, fat_g_target, updated_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'computed', 94, 299, 102, %s, %s)" % (NOW, U1)),
    ("RG37 objectif en double, catégorie vide", "INSERT INTO activity_goal (id_activity_goal, metric, period, target_value, valid_from, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'sessions', 'week', 4, '2026-11-01', %s, %s)" % (NOW, U1)),
    ("RG37 période « séance » pour des minutes", "INSERT INTO activity_goal (id_activity_goal, metric, period, target_value, valid_from, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'minutes', 'session', 30, '2026-11-01', %s, %s)" % (NOW, U1)),
    ("RG42 deux réglages du même type", "INSERT INTO reminder_setting (id_reminder_setting, kind, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'motivation', %s)" % U1),
    ("RG27 deux favoris du même nom", "INSERT INTO favorite_meal (id_favorite_meal, name, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'Midi habituel', %s, %s)" % (NOW, U1)),
    ("RG46 supprimer un aliment de base utilisé", "DELETE FROM food WHERE ciqual_code = '36018'"),
    ("RG22 supprimer un aliment personnalisé utilisé", "DELETE FROM food WHERE id_food = UNHEX('44444444444444444444444444444444')"),
    ("RG19 aliment de base sans groupe", "INSERT INTO food (id_food, name_fr, name_en, kcal_100g, protein_100g, carbs_100g, fat_100g, created_at) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'X', 'X', 100, 1, 1, 1, %s)" % NOW),
    ("RG18 aliment personnalisé à 100,3 g de macros", "INSERT INTO food (id_food, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'X', 900, 0, 0.3, 100, %s, %s)" % (NOW, U1)),
    ("RG21 porc sans viande", "INSERT INTO food (id_food, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, contains_pork, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'X', 100, 1, 1, 1, TRUE, %s, %s)" % (NOW, U1)),
    ("RG21 alcool mesuré sans étiquette", "INSERT INTO food (id_food, name_fr, kcal_100g, protein_100g, carbs_100g, fat_100g, alcohol_100g, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'X', 70, 0, 1, 0, 9, %s, %s)" % (NOW, U1)),
    ("RG20 unité d'un autre aliment", "INSERT INTO meal_item (id_meal_item, quantity_g, portion_count, kcal, protein_g, carbs_g, fat_g, id_meal, id_food, id_food_portion) VALUES (UNHEX(REPLACE(UUID(),'-','')), 90, 1, 1, 1, 1, 1, UNHEX('55555555555555555555555555555555'), %s, UNHEX('aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa'))" % FOOD_BASE),
    ("RG20 nombre d'unités sans unité", "INSERT INTO meal_item (id_meal_item, quantity_g, portion_count, kcal, protein_g, carbs_g, fat_g, id_meal, id_food) VALUES (UNHEX(REPLACE(UUID(),'-','')), 90, 2, 1, 1, 1, 1, UNHEX('55555555555555555555555555555555'), %s)" % FOOD_BASE),
    ("G08 mode saisi sans valeur", "UPDATE calorie_goal SET mode = 'manual', manual_kcal = NULL WHERE id_user = %s" % U1),
    ("RG52 deux versions le même jour", "INSERT INTO calorie_target_history (id_calorie_target_history, effective_from, kcal_target, protein_g_target, carbs_g_target, fat_g_target, mode, id_calorie_goal) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-20', 2300, 90, 280, 95, 'manual', UNHEX('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'))"),
    ("RG52 version à 900 kcal", "INSERT INTO calorie_target_history (id_calorie_target_history, effective_from, kcal_target, protein_g_target, carbs_g_target, fat_g_target, mode, id_calorie_goal) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-21', 900, 50, 100, 30, 'manual', UNHEX('bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb'))"),
    ("RG37 fin de validité avant le début", "UPDATE activity_goal SET valid_to = '2026-10-01' WHERE id_user = %s AND id_activity_category IS NULL" % U1),
    ("RG29 groupe musculaire en double sur un type", "INSERT INTO activity_type_muscle_group (id_activity_type, id_muscle_group) SELECT t.id_activity_type, m.id_muscle_group FROM activity_type t, muscle_group m WHERE t.compendium_code = '12050' AND m.code = 'legs'"),
    ("RG29 difficulté inconnue", "UPDATE activity_type SET difficulty = 'extreme' WHERE compendium_code = '12050'"),
    ("RG35 valeur saisie gardée en mode calculé", "UPDATE calorie_goal SET manual_kcal = 2000 WHERE id_user = %s" % U1),
    ("RG33 même séance de Santé importée deux fois", "INSERT INTO activity (id_activity, performed_at, duration_min, kcal, kcal_status, source, health_uuid, created_at, updated_at, id_user, id_activity_type) VALUES (UNHEX(REPLACE(UUID(),'-','')), %s, 40, 350, 'entered', 'health', UNHEX('88888888888888888888888888888888'), %s, %s, %s, %s)" % (NOW, NOW, NOW, U1, TYPE_COURSE)),
    ("RG33 séance saisie marquée ignorée", "UPDATE activity SET is_ignored = TRUE WHERE id_user = %s AND source = 'manual'" % U1),
    ("RG40 deux valeurs d'énergie active le même jour", "INSERT INTO daily_active_energy (id_daily_active_energy, day, kcal, imported_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-25', 100, %s, %s)" % (NOW, U1)),
    ("RG39 pesée importée sans identifiant Santé", "INSERT INTO weigh_in (id_weigh_in, weighed_on, weight_kg, source, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-19', 73, 'health', %s, %s)" % (NOW, U1)),
    ("RG46 supprimer un type d'activité utilisé", "DELETE FROM activity_type WHERE compendium_code = '12050'"),
    ("RG48 supprimer un administrateur qui a des actions journalisées", "DELETE FROM `user` WHERE id_user = %s" % ADMIN),
]

RETRAIT_RG11 = [
    "START TRANSACTION",
    "DELETE FROM health_profile WHERE id_user = %s" % U1,
    "DELETE FROM weigh_in WHERE id_user = %s" % U1,
    "DELETE FROM daily_active_energy WHERE id_user = %s" % U1,
    "DELETE FROM activity WHERE id_user = %s AND source = 'health'" % U1,
    "UPDATE activity SET kcal = NULL, kcal_status = 'unknown' WHERE id_user = %s AND kcal_status = 'estimated'" % U1,
    "DELETE h FROM calorie_target_history h JOIN calorie_goal g ON g.id_calorie_goal = h.id_calorie_goal WHERE g.id_user = %s AND h.mode = 'computed'" % U1,
    "UPDATE calorie_goal SET mode = 'manual', manual_kcal = LEAST(GREATEST(2490, 1200), 6000) WHERE id_user = %s" % U1,
    "UPDATE health_consent SET withdrawn_at = '2026-11-25 11:00:00' WHERE id_user = %s AND withdrawn_at IS NULL" % U1,
    "COMMIT",
]
CONTROLE_RG11 = (
    "SELECT (SELECT COUNT(*) FROM health_profile WHERE id_user = %s) + (SELECT COUNT(*) FROM weigh_in WHERE id_user = %s) + "
    "(SELECT COUNT(*) FROM daily_active_energy WHERE id_user = %s) + (SELECT COUNT(*) FROM activity WHERE id_user = %s AND (source = 'health' OR kcal_status = 'estimated')) + "
    "(SELECT COUNT(*) FROM health_profile_allergen) + (SELECT COUNT(*) FROM calorie_goal WHERE id_user = %s AND mode <> 'manual') + "
    "(SELECT COUNT(*) FROM calorie_target_history WHERE mode = 'computed') + "
    "(SELECT COUNT(*) FROM health_consent WHERE id_user = %s AND withdrawn_at IS NULL)" % ((U1,) * 6)
)

PERMIS_APRES = [
    ("RG37 modifier un objectif : clôture puis nouvelle version", "UPDATE activity_goal SET valid_to = '2026-11-24' WHERE id_user = %s AND id_activity_category IS NULL; INSERT INTO activity_goal (id_activity_goal, metric, period, target_value, valid_from, created_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'sessions', 'week', 4, '2026-11-25', %s, %s)" % (U1, NOW, U1)),
    ("RG37 même mesure et période, autre catégorie", "INSERT INTO activity_goal (id_activity_goal, metric, period, target_value, valid_from, created_at, id_user, id_activity_category) VALUES (UNHEX(REPLACE(UUID(),'-','')), 'sessions', 'week', 1, '2026-11-01', %s, %s, (SELECT id_activity_category FROM activity_category WHERE code = 'yoga'))" % (NOW, U1)),
    ("RG10 nouveau consentement après un retrait", "INSERT INTO health_consent (id_health_consent, text_version, granted_at, id_user) VALUES (UNHEX(REPLACE(UUID(),'-','')), '2026-11-v1', '2026-11-25 12:00:00', %s)" % U1),
    ("RG43 supprimer directement le compte est refusé (les lignes protègent leurs aliments)", None),
    ("RG43 service de suppression : repas et favoris, puis le compte, en une transaction",
     "START TRANSACTION; DELETE FROM meal WHERE id_user = %s; DELETE FROM favorite_meal WHERE id_user = %s; DELETE FROM `user` WHERE id_user = %s; COMMIT" % (U1, U1, U1)),
]

CONTROLES_FINAUX = (
    "SELECT (SELECT COUNT(*) FROM meal) + (SELECT COUNT(*) FROM meal_item) + (SELECT COUNT(*) FROM activity) + "
    "(SELECT COUNT(*) FROM weigh_in) + (SELECT COUNT(*) FROM health_profile) + (SELECT COUNT(*) FROM health_consent) + "
    "(SELECT COUNT(*) FROM health_profile_allergen) + (SELECT COUNT(*) FROM calorie_goal) + (SELECT COUNT(*) FROM activity_goal) + "
    "(SELECT COUNT(*) FROM reminder_setting) + (SELECT COUNT(*) FROM favorite_meal) + (SELECT COUNT(*) FROM favorite_item) + "
    "(SELECT COUNT(*) FROM food WHERE id_user IS NOT NULL) + (SELECT COUNT(*) FROM daily_active_energy) + "
    "(SELECT COUNT(*) FROM calorie_target_history) + (SELECT COUNT(*) FROM login_event) + "
    "(SELECT COUNT(*) FROM food_portion WHERE label_fr = '1 part') + "
    "(SELECT COUNT(*) FROM food_allergen WHERE id_food = UNHEX('44444444444444444444444444444444'))"
)


def nettoyer():
    essai = "(SELECT id_user FROM `user` WHERE email LIKE '%.essai@example.test')"
    run("DELETE FROM admin_action WHERE id_user IN %s; DELETE FROM meal WHERE id_user IN %s; DELETE FROM favorite_meal WHERE id_user IN %s; "
        "DELETE FROM `user` WHERE email LIKE '%%.essai@example.test'" % (essai, essai, essai))


def main():
    echecs = 0
    nettoyer()
    for sql in PREPARATION:
        ok, msg = run(sql)
        if not ok:
            print("PRÉPARATION EN ÉCHEC :", msg)
            sys.exit(1)
    print("Préparation : %d insertions permises acceptées" % len(PREPARATION))
    for nom, sql in INTERDITS:
        ok, msg = run(sql)
        statut = "refusé" if not ok else "ACCEPTÉ À TORT"
        echecs += ok
        print("  [%s] %s%s" % (statut, nom, "" if ok else " (%s)" % msg.split(" at line")[0][:90]))
    ok, msg = run("; ".join(RETRAIT_RG11))
    ok2, reste11 = run(CONTROLE_RG11)
    succes = ok and ok2 and reste11 == "0"
    echecs += not succes
    print("  [%s] RG11 retrait du consentement : données de santé effacées, kcal estimées vidées, objectif en mode saisi%s" % (
        "accepté" if succes else "ÉCHEC", "" if succes else " : " + msg + " / reste " + reste11))
    for nom, sql in PERMIS_APRES:
        if sql is None:
            ok, msg = run("DELETE FROM `user` WHERE id_user = %s" % U1)
            echecs += ok
            print("  [%s] %s" % ("refusé" if not ok else "ACCEPTÉ À TORT", nom))
            continue
        ok, msg = run(sql)
        echecs += not ok
        print("  [%s] %s%s" % ("accepté" if ok else "REFUSÉ À TORT", nom, "" if ok else " : " + msg))
    ok, msg = run(CONTROLES_FINAUX)
    reste = int(msg) if ok and msg.isdigit() else -1
    print("  Lignes restantes de l'utilisateur supprimé : %s" % reste)
    echecs += reste != 0
    nettoyer()
    print("RÉSULTAT : %s" % ("tous les contrôles passent" if echecs == 0 else "%d contrôle(s) en échec" % echecs))
    sys.exit(1 if echecs else 0)


if __name__ == "__main__":
    main()
