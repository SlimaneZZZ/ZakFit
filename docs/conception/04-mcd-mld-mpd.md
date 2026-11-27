# ZakFit — MCD, MLD et MPD

Généré par `modele/generer.py` depuis `modele/modele.py`. Ne pas modifier à la main.
Schémas : `diagrammes/modelisation.drawio` (pages dictionnaire, MCD, MLD). Script : `sql/`.

## 1. MCD : entités

Notation du cours : entité en majuscules, identifiant souligné (ici en premier), propriétés ensuite.

- **USER** (<u>id_user</u>, last_name, first_name, email, password_hash, role, status, blocked_until, adult_declared_at, time_zone, created_at, updated_at) : un compte ZakFit, utilisateur ou administrateur
- **HEALTH_PROFILE** (<u>id_health_profile</u>, birth_year, sex, height_cm, activity_level, goal_orientation, meat_preference, is_vegetarian, is_vegan, updated_at) : le profil de santé d'un utilisateur qui a donné son consentement
- **HEALTH_CONSENT** (<u>id_health_consent</u>, text_version, granted_at, withdrawn_at) : un consentement santé donné à une date, éventuellement retiré ensuite
- **ALLERGEN** (<u>id_allergen</u>, code, name_fr, name_en) : un des 14 allergènes réglementaires
- **FOOD_GROUP** (<u>id_food_group</u>, ciqual_group_code, name_fr, name_en) : un groupe d'aliments de CIQUAL (catégorie, p. 22 du cahier)
- **FOOD** (<u>id_food</u>, ciqual_code, name_fr, name_en, kcal_100g, protein_100g, carbs_100g, fat_100g, fiber_100g, alcohol_100g, contains_meat, contains_pork, contains_animal_product, contains_alcohol, labels_verified, is_archived, created_at) : un aliment, de base (CIQUAL ou ajouté par un administrateur) ou personnalisé
- **FOOD_PORTION** (<u>id_food_portion</u>, label_fr, label_en, grams, provenance) : une unité de mesure d'un aliment, avec son poids (« 1 œuf moyen = 50 g »)
- **MEAL** (<u>id_meal</u>, meal_type, eaten_on, origin, created_at, updated_at) : un repas d'un utilisateur, un jour donné
- **MEAL_ITEM** (<u>id_meal_item</u>, quantity_g, portion_count, kcal, protein_g, carbs_g, fat_g, estimated_g) : une ligne d'un repas : un aliment et sa quantité, avec ses valeurs figées
- **FAVORITE_MEAL** (<u>id_favorite_meal</u>, name, created_at) : un repas favori, réutilisable, d'un utilisateur
- **FAVORITE_ITEM** (<u>id_favorite_item</u>, quantity_g, portion_count) : un aliment d'un repas favori, avec sa quantité
- **ACTIVITY_CATEGORY** (<u>id_activity_category</u>, code, name_fr, name_en) : une catégorie d'activité (cardio, musculation…)
- **ACTIVITY_TYPE** (<u>id_activity_type</u>, compendium_code, name_fr, name_en, met, difficulty, instructions_fr, instructions_en, is_archived) : un type d'activité du Compendium 2024, avec son MET
- **ACTIVITY** (<u>id_activity</u>, performed_at, performed_on, duration_min, kcal, kcal_status, source, health_uuid, is_ignored, created_at, updated_at) : une séance d'activité physique d'un utilisateur
- **DAILY_ACTIVE_ENERGY** (<u>id_daily_active_energy</u>, day, kcal, imported_at) : l'énergie active d'un jour, importée de l'app Santé
- **WEIGH_IN** (<u>id_weigh_in</u>, weighed_on, weight_kg, source, health_uuid, is_ignored, created_at) : une pesée d'un utilisateur, un jour donné
- **CALORIE_GOAL** (<u>id_calorie_goal</u>, mode, manual_kcal, protein_g_target, carbs_g_target, fat_g_target, macros_custom, updated_at) : l'objectif calorique et la répartition des macros d'un utilisateur
- **ACTIVITY_GOAL** (<u>id_activity_goal</u>, metric, period, target_value, valid_from, valid_to, created_at) : un objectif d'activité d'un utilisateur
- **REMINDER_SETTING** (<u>id_reminder_setting</u>, kind, is_enabled, send_time) : le réglage d'un type de rappel ou de message pour un utilisateur
- **ADMIN_ACTION** (<u>id_admin_action</u>, action, target_kind, target_id, performed_at) : une action d'administration journalisée
- **CALORIE_TARGET_HISTORY** (<u>id_calorie_target_history</u>, effective_from, kcal_target, protein_g_target, carbs_g_target, fat_g_target, mode) : l'objectif calorique et les macros qui s'appliquent à partir d'un jour donné, figés
- **MUSCLE_GROUP** (<u>id_muscle_group</u>, code, name_fr, name_en) : un groupe musculaire sollicité par des exercices
- **LOGIN_EVENT** (<u>id_login_event</u>, logged_in_at) : une connexion réussie d'un utilisateur, datée

## 2. MCD : associations

Chaque cardinalité se lit depuis l'entité, et se justifie par deux phrases. La règle de passage au MLD est celle du cours (R1 à R5) ; « Hors cours » désigne le cas 0,1 face à 0,n, traité par une clé étrangère facultative (Roy p. 155 et 161, Baptiste PDF 44).

| Verbe | Patte A | Patte B | Phrases | Règle | Traduction au MLD |
|---|---|---|---|---|---|
| POSSÉDER | USER 0,1 | HEALTH_PROFILE 1,1 | Un utilisateur possède 0 ou 1 profil de santé (aucun sans consentement). Un profil de santé appartient à exactement 1 utilisateur. | R4 | `health_profile.#id_user` obligatoire, UNIQUE, ON DELETE CASCADE |
| DONNER | USER 0,n | HEALTH_CONSENT 1,1 | Un utilisateur donne 0 à n consentements au fil du temps (donner, retirer, redonner). Un consentement est donné par exactement 1 utilisateur. | R1 | `health_consent.#id_user` obligatoire, ON DELETE CASCADE |
| DÉCLARER | HEALTH_PROFILE 0,n | ALLERGEN 0,n | Un profil de santé déclare 0 à n allergènes. Un allergène est déclaré dans 0 à n profils de santé. | R2 | Table de liaison `health_profile_allergen(#id_health_profile, #id_allergen)` |
| CLASSER | FOOD_GROUP 0,n | FOOD 0,1 | Un groupe classe 0 à n aliments. Un aliment est classé dans 0 ou 1 groupe (obligatoire pour un aliment de base, facultatif pour un aliment personnalisé). | Hors cours | `food.#id_food_group` facultative (NULL), ON DELETE RESTRICT |
| PERSONNALISER | USER 0,n | FOOD 0,1 | Un utilisateur personnalise 0 à n aliments, qui lui sont privés. Un aliment appartient en propre à 0 ou 1 utilisateur (aucun pour un aliment de base, même ajouté par un administrateur). | Hors cours | `food.#id_user` facultative (NULL), ON DELETE CASCADE |
| CONTENIR | FOOD 0,n | ALLERGEN 0,n | Un aliment contient 0 à n allergènes. Un allergène est contenu dans 0 à n aliments. | R2 | Table de liaison `food_allergen(#id_food, #id_allergen)` |
| MESURER | FOOD 0,n | FOOD_PORTION 1,1 | Un aliment se mesure en 0 à n unités. Une unité mesure exactement 1 aliment. | R1 | `food_portion.#id_food` obligatoire, ON DELETE CASCADE |
| ENREGISTRER | USER 0,n | MEAL 1,1 | Un utilisateur enregistre 0 à n repas. Un repas est enregistré par exactement 1 utilisateur. | R1 | `meal.#id_user` obligatoire, ON DELETE CASCADE |
| COMPOSER | MEAL 1,n | MEAL_ITEM 1,1 | Un repas est composé de 1 à n lignes. Une ligne compose exactement 1 repas. Le minimum 1 côté repas n'est pas garanti par la clé étrangère : l'API refuse un repas sans ligne (RG24). MEAL_ITEM est une entité plutôt qu'une association porteuse (R2, exemple LIGNE_DE_COMMANDE du cours) : un même aliment peut figurer deux fois dans un repas (test d'unicité, Pham p. 41-43), et la ligne est reliée à une unité. | R1 | `meal_item.#id_meal` obligatoire, ON DELETE CASCADE |
| RÉFÉRENCER | FOOD 0,n | MEAL_ITEM 1,1 | Un aliment est référencé par 0 à n lignes de repas. Une ligne de repas référence exactement 1 aliment. | R1 | `meal_item.#id_food` obligatoire, ON DELETE RESTRICT |
| EXPRIMER | FOOD_PORTION 0,n | MEAL_ITEM 0,1 | Une unité exprime 0 à n lignes de repas. Une ligne de repas est exprimée en 0 ou 1 unité (aucune si saisie en grammes). Une clé étrangère composée (id_food_portion, id_food) garantit que l'unité appartient à l'aliment de la ligne. | Hors cours | `meal_item.#id_food_portion` facultative (NULL), ON DELETE RESTRICT |
| MÉMORISER | USER 0,n | FAVORITE_MEAL 1,1 | Un utilisateur mémorise 0 à n repas favoris. Un favori est mémorisé par exactement 1 utilisateur. | R1 | `favorite_meal.#id_user` obligatoire, ON DELETE CASCADE |
| REGROUPER | FAVORITE_MEAL 1,n | FAVORITE_ITEM 1,1 | Un favori regroupe 1 à n lignes. Une ligne de favori est regroupée dans exactement 1 favori. Minimum 1 côté favori garanti par l'API. FAVORITE_ITEM est une entité pour les mêmes raisons que MEAL_ITEM. | R1 | `favorite_item.#id_favorite_meal` obligatoire, ON DELETE CASCADE |
| DÉSIGNER | FOOD 0,n | FAVORITE_ITEM 1,1 | Un aliment est désigné par 0 à n lignes de favoris. Une ligne de favori désigne exactement 1 aliment. | R1 | `favorite_item.#id_food` obligatoire, ON DELETE RESTRICT |
| DOSER | FOOD_PORTION 0,n | FAVORITE_ITEM 0,1 | Une unité dose 0 à n lignes de favoris. Une ligne de favori est dosée en 0 ou 1 unité. Même clé composée que pour une ligne de repas. | Hors cours | `favorite_item.#id_food_portion` facultative (NULL), ON DELETE RESTRICT |
| APPARTENIR | ACTIVITY_CATEGORY 1,n | ACTIVITY_TYPE 1,1 | Une catégorie regroupe 1 à n types d'activité. Un type d'activité appartient à exactement 1 catégorie. Minimum 1 côté catégorie garanti par le référentiel chargé : chaque catégorie a au moins un type. | R1 | `activity_type.#id_activity_category` obligatoire, ON DELETE RESTRICT |
| PRATIQUER | USER 0,n | ACTIVITY 1,1 | Un utilisateur pratique 0 à n séances. Une séance est pratiquée par exactement 1 utilisateur. | R1 | `activity.#id_user` obligatoire, ON DELETE CASCADE |
| CORRESPONDRE | ACTIVITY_TYPE 0,n | ACTIVITY 1,1 | Un type d'activité correspond à 0 à n séances. Une séance correspond à exactement 1 type d'activité. | R1 | `activity.#id_activity_type` obligatoire, ON DELETE RESTRICT |
| IMPORTER | USER 0,n | DAILY_ACTIVE_ENERGY 1,1 | Un utilisateur importe 0 à n valeurs journalières d'énergie active. Une valeur journalière est importée pour exactement 1 utilisateur. | R1 | `daily_active_energy.#id_user` obligatoire, ON DELETE CASCADE |
| PESER | USER 0,n | WEIGH_IN 1,1 | Un utilisateur se pèse 0 à n fois. Une pesée concerne exactement 1 utilisateur. | R1 | `weigh_in.#id_user` obligatoire, ON DELETE CASCADE |
| VISER | USER 0,1 | CALORIE_GOAL 1,1 | Un utilisateur vise 0 ou 1 objectif calorique (aucun avant le questionnaire). Un objectif calorique est visé par exactement 1 utilisateur. | R4 | `calorie_goal.#id_user` obligatoire, UNIQUE, ON DELETE CASCADE |
| FIXER | USER 0,n | ACTIVITY_GOAL 1,1 | Un utilisateur fixe 0 à n objectifs d'activité. Un objectif d'activité est fixé par exactement 1 utilisateur. | R1 | `activity_goal.#id_user` obligatoire, ON DELETE CASCADE |
| CIBLER | ACTIVITY_CATEGORY 0,n | ACTIVITY_GOAL 0,1 | Une catégorie est ciblée par 0 à n objectifs d'activité. Un objectif d'activité cible 0 ou 1 catégorie (aucune : toutes les activités). | Hors cours | `activity_goal.#id_activity_category` facultative (NULL), ON DELETE RESTRICT |
| RÉGLER | USER 0,n | REMINDER_SETTING 1,1 | Un utilisateur règle 0 à n types de notification. Un réglage appartient à exactement 1 utilisateur. | R1 | `reminder_setting.#id_user` obligatoire, ON DELETE CASCADE |
| EFFECTUER | USER 0,n | ADMIN_ACTION 1,1 | Un administrateur effectue 0 à n actions journalisées. Une action est effectuée par exactement 1 administrateur. RESTRICT : le compte d'un administrateur qui a des actions journalisées ne se supprime pas ; on le suspend (RG48). | R1 | `admin_action.#id_user` obligatoire, ON DELETE RESTRICT |
| HISTORISER | CALORIE_GOAL 0,n | CALORIE_TARGET_HISTORY 1,1 | Un objectif calorique est historisé en 0 à n versions datées. Une version appartient à exactement 1 objectif calorique. Les valeurs d'une version sont figées, comme celles d'une ligne de repas (RG25) : un bilan passé se compare à l'objectif qui s'appliquait ce jour-là (RG52). | R1 | `calorie_target_history.#id_calorie_goal` obligatoire, ON DELETE CASCADE |
| SOLLICITER | ACTIVITY_TYPE 0,n | MUSCLE_GROUP 0,n | Un type d'activité sollicite 0 à n groupes musculaires. Un groupe musculaire est sollicité par 0 à n types d'activité. | R2 | Table de liaison `activity_type_muscle_group(#id_activity_type, #id_muscle_group)` |
| CONNECTER | USER 0,n | LOGIN_EVENT 1,1 | Un utilisateur se connecte 0 à n fois. Une connexion est celle d'exactement 1 utilisateur. | R1 | `login_event.#id_user` obligatoire, ON DELETE CASCADE |

## 3. MLD

Notation du cours : `TABLE(clé_primaire, attribut, #clé_étrangère)`. Les clés primaires sont les premiers champs.

- `user`(<u>id_user</u>, last_name, first_name, email, password_hash, role, status, blocked_until, adult_declared_at, time_zone, created_at, updated_at)
- `health_profile`(<u>id_health_profile</u>, birth_year, sex, height_cm, activity_level, goal_orientation, meat_preference, is_vegetarian, is_vegan, updated_at, #id_user)
- `health_consent`(<u>id_health_consent</u>, text_version, granted_at, withdrawn_at, #id_user)
- `allergen`(<u>id_allergen</u>, code, name_fr, name_en)
- `food_group`(<u>id_food_group</u>, ciqual_group_code, name_fr, name_en)
- `food`(<u>id_food</u>, ciqual_code, name_fr, name_en, kcal_100g, protein_100g, carbs_100g, fat_100g, fiber_100g, alcohol_100g, contains_meat, contains_pork, contains_animal_product, contains_alcohol, labels_verified, is_archived, created_at, #id_food_group, #id_user)
- `food_portion`(<u>id_food_portion</u>, label_fr, label_en, grams, provenance, #id_food)
- `meal`(<u>id_meal</u>, meal_type, eaten_on, origin, created_at, updated_at, #id_user)
- `meal_item`(<u>id_meal_item</u>, quantity_g, portion_count, kcal, protein_g, carbs_g, fat_g, estimated_g, #id_meal, #id_food, #id_food_portion)
- `favorite_meal`(<u>id_favorite_meal</u>, name, created_at, #id_user)
- `favorite_item`(<u>id_favorite_item</u>, quantity_g, portion_count, #id_favorite_meal, #id_food, #id_food_portion)
- `activity_category`(<u>id_activity_category</u>, code, name_fr, name_en)
- `activity_type`(<u>id_activity_type</u>, compendium_code, name_fr, name_en, met, difficulty, instructions_fr, instructions_en, is_archived, #id_activity_category)
- `activity`(<u>id_activity</u>, performed_at, performed_on, duration_min, kcal, kcal_status, source, health_uuid, is_ignored, created_at, updated_at, #id_user, #id_activity_type)
- `daily_active_energy`(<u>id_daily_active_energy</u>, day, kcal, imported_at, #id_user)
- `weigh_in`(<u>id_weigh_in</u>, weighed_on, weight_kg, source, health_uuid, is_ignored, created_at, #id_user)
- `calorie_goal`(<u>id_calorie_goal</u>, mode, manual_kcal, protein_g_target, carbs_g_target, fat_g_target, macros_custom, updated_at, #id_user)
- `activity_goal`(<u>id_activity_goal</u>, metric, period, target_value, valid_from, valid_to, created_at, #id_user, #id_activity_category)
- `reminder_setting`(<u>id_reminder_setting</u>, kind, is_enabled, send_time, #id_user)
- `admin_action`(<u>id_admin_action</u>, action, target_kind, target_id, performed_at, #id_user)
- `calorie_target_history`(<u>id_calorie_target_history</u>, effective_from, kcal_target, protein_g_target, carbs_g_target, fat_g_target, mode, #id_calorie_goal)
- `muscle_group`(<u>id_muscle_group</u>, code, name_fr, name_en)
- `login_event`(<u>id_login_event</u>, logged_in_at, #id_user)
- `health_profile_allergen`(<u>#id_health_profile</u>, <u>#id_allergen</u>)
- `food_allergen`(<u>#id_food</u>, <u>#id_allergen</u>)
- `activity_type_muscle_group`(<u>#id_activity_type</u>, <u>#id_muscle_group</u>)

## 4. MPD : choix physiques (MariaDB 10.4)

- **Identifiants :** UUID stockés en `VARBINARY(16)`, comme le fait Fluent avec le pilote MySQL. Les données de référence ont des UUID stables (version 5), pour que le script se rejoue à l'identique.
- **Listes de valeurs :** type `ENUM`, contrôlé par MariaDB.
- **Dates :** `DATETIME(6)` en UTC pour les instants ; `DATE` pour les jours locaux (repas, pesées, énergie active), calculés dans le fuseau de l'utilisateur (RG23, RG38).
- **Nombres :** `DECIMAL` pour les grammes et les kcal (pas d'erreur d'arrondi binaire, 02-formules.md §5).
- **Suppressions :** ON DELETE CASCADE pour les données d'un utilisateur (RG43) ; RESTRICT pour les référentiels, qu'on archive au lieu de supprimer (RG22, RG46), et pour l'unité d'une ligne, protégée par la clé composée (id_food_portion, id_food).
- **Suppression d'un compte (RG43) :** les lignes de repas et de favoris protègent leur aliment (RESTRICT), y compris un aliment personnalisé. Le service supprime donc, dans une transaction : les repas, puis les favoris, puis le compte, dont la cascade efface le reste. La base refuse l'ordre inverse. Le test `modele/tester_sql.py` vérifie les deux cas.
- **Contraintes de plusieurs lignes**, posées avec une colonne générée PERSISTENT et un index unique :
  - un seul consentement actif par utilisateur (`health_consent.active_flag`) ;
  - un seul objectif d'activité par mesure, période et catégorie, catégorie vide comprise (`activity_goal.category_key`), car un index unique ordinaire accepte plusieurs NULL.
- **Règles vérifiées par l'API, pas par la base** (elles demandent la date du jour, un calcul ou le contexte de la requête) :
  - âge d'au moins 18 ans (RG12), dates non futures (RG23, RG30), cohérence de l'énergie d'un aliment (RG18) ;
  - au moins une ligne par repas et par favori ; priorité d'une pesée saisie sur Santé (RG39) ;
  - aucune donnée de santé sans consentement actif (RG10), et le service de retrait du consentement (RG11) ;
  - un aliment personnalisé n'est lu et utilisé que par son créateur (RG19, RG09). Sans ce contrôle, un repas d'un autre utilisateur pourrait le référencer, et la suppression du compte du créateur échouerait (RESTRICT) ;
  - calcul de l'objectif en mode computed (RG34) ; MET d'un type jamais modifié (RG29) ; rôle et protection de l'administrateur contre lui-même (RG07) ;
  - correspondance des types de séance de Santé avec le référentiel (RG33).
- **Valeurs dérivées :** aucune n'est stockée (totaux, objectif calculé, kcal brûlées du jour), sauf quatre valeurs figées volontairement : les valeurs d'une ligne de repas (RG25), les kcal estimées d'une séance (qui dépendent du poids au jour de la séance), le jour local d'une séance (`performed_on`, pour regrouper par jour en SQL sans tables de fuseaux et garder le jour vécu) et les versions de l'objectif calorique (RG52), pour qu'un bilan passé ne change pas quand l'objectif change.
- **Chiffrement au repos (p. 25) :** toutes les tables InnoDB sont chiffrées par MariaDB (`innodb_encrypt_tables = ON`, plugin `file_key_management`, clé hors du dépôt). C'est un réglage du serveur, sans effet sur le script ni sur le code. Mise en place prévue avec le socle Vapor (30/11), avec une preuve conservée sans secret : plugin chargé, variables actives, tables chiffrées (`information_schema.INNODB_TABLESPACES_ENCRYPTION`).
- **Conservation :** pas de purge automatique en version 1. Les données d'un compte vivent tant que le compte existe ; l'utilisateur les efface lui-même (RG11, RG43). Une durée de conservation des comptes inactifs reste à décider avant toute mise en ligne (article 5.1.e du RGPD).
- **Index de lecture :** `meal(id_user, eaten_on)`, `meal(eaten_on, meal_type)`, `activity(performed_on)`, `user(created_at)`, `login_event(id_user, logged_in_at)`, `activity(id_user, performed_on)`, `weigh_in(id_user, weighed_on)`, `food(name_fr)`, `food(name_en)`.
