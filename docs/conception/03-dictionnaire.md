# ZakFit — dictionnaire des données

Généré par `modele/generer.py` depuis `modele/modele.py`. Ne pas modifier à la main.

Les 7 colonnes sont celles du cours : nom, description, type, format, contraintes, origine, fréquence de mise à jour.
Les clés étrangères ne figurent pas ici : elles naissent des associations du MCD (voir `04-mcd-mld-mpd.md`).
Une entité marquée ★ porte des données de santé (article 9 du RGPD), effacées au retrait du consentement. Le retrait efface aussi les séances importées de Santé et les kcal estimées des séances, et vide les associations de HEALTH_PROFILE (RG11).

## Compte

### USER

Une occurrence : un compte ZakFit, utilisateur ou administrateur.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_user` | Identifiant du compte | Identifiant | UUID (16 octets) | Clé primaire | Système | À l'ajout |
| `last_name` | Nom de famille | Alphanumérique | 1 à 50 caractères | Obligatoire | Utilisateur | À l'ajout et à la modification |
| `first_name` | Prénom | Alphanumérique | 1 à 50 caractères | Obligatoire | Utilisateur | À l'ajout et à la modification |
| `email` | Adresse email, enregistrée en minuscules | Alphanumérique | 254 caractères au plus | Obligatoire, format email, unique (RG01) | Utilisateur | À l'ajout et à la modification |
| `password_hash` | Empreinte bcrypt du mot de passe, jamais le mot de passe en clair | Alphanumérique | 60 caractères | Obligatoire, jamais renvoyée par l'API (RG02, RG03) | Calcul interne (bcrypt) | À l'ajout et au changement de mot de passe |
| `role` | Rôle du compte | Liste | user, admin | Obligatoire, user par défaut ; admin seulement par script (RG07) | Système | Par un administrateur |
| `status` | Statut du compte | Liste | active, blocked, suspended | Obligatoire, active par défaut (RG06) | Administrateur | Par un administrateur |
| `blocked_until` | Fin d'un blocage temporaire | Date et heure | UTC, à la microseconde | Facultatif ; seulement si status = blocked (RG06) | Administrateur | Par un administrateur |
| `adult_declared_at` | Moment où la case « J'ai 18 ans ou plus » a été cochée | Date et heure | UTC | Obligatoire (RG12) | Utilisateur | À l'ajout |
| `time_zone` | Fuseau horaire de l'utilisateur | Alphanumérique | Nom IANA, 64 caractères au plus (ex. Europe/Paris) | Obligatoire, Europe/Paris par défaut (RG23, RG38) | Appareil | À la connexion et quand il change |
| `created_at` | Date d'inscription | Date et heure | UTC | Obligatoire | Système | À l'ajout |
| `updated_at` | Dernière modification du compte | Date et heure | UTC | Obligatoire | Système | À chaque modification |

### ADMIN_ACTION

Une occurrence : une action d'administration journalisée.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_admin_action` | Identifiant de l'action | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `action` | Action réalisée | Liste | block, suspend, reactivate, delete_user, create, update, archive, delete | Obligatoire (RG48) | Système | À l'ajout |
| `target_kind` | Type de la cible | Liste | user, food, activity_type | Obligatoire (RG48) | Système | À l'ajout |
| `target_id` | Identifiant de la cible, sans clé étrangère : la cible peut être supprimée | Identifiant | UUID | Obligatoire ; ni nom ni email (RG48) | Système | À l'ajout |
| `performed_at` | Moment de l'action | Date et heure | UTC | Obligatoire | Système | À l'ajout |

### LOGIN_EVENT

Une occurrence : une connexion réussie d'un utilisateur, datée.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_login_event` | Identifiant de la connexion | Identifiant | UUID | Clé primaire | Système | À la connexion |
| `logged_in_at` | Moment de la connexion | Date et heure | UTC | Obligatoire ; ni adresse IP ni appareil (minimisation, RG53) | Système | À chaque connexion réussie |

## Santé

### HEALTH_PROFILE ★

Une occurrence : le profil de santé d'un utilisateur qui a donné son consentement.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_health_profile` | Identifiant du profil de santé | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `birth_year` | Année de naissance, sans le jour ni le mois (minimisation) | Numérique | Entier, AAAA | Facultatif tant que non saisi ; âge d'au moins 18 ans (RG12) | Utilisateur | Questionnaire de démarrage, profil |
| `sex` | Sexe, utilisé seulement par la formule de Mifflin-St Jeor | Liste | female, male | Facultatif tant que non saisi (RG13) | Utilisateur | Questionnaire de démarrage, profil |
| `height_cm` | Taille | Numérique | Entier, en cm | 100 à 250 (RG13) | Utilisateur | Questionnaire de démarrage, profil |
| `activity_level` | Niveau d'activité (PAL EFSA 1,4 / 1,6 / 1,8 / 2,0) | Liste | low, moderate, active, very_active | Facultatif tant que non saisi (RG14) | Utilisateur | Questionnaire de démarrage, profil |
| `goal_orientation` | Orientation : perte, maintien ou prise de masse | Liste | lose, maintain, gain | Facultatif tant que non saisi (RG15) | Utilisateur | Questionnaire de démarrage, profil |
| `meat_preference` | Préférence pour la viande | Liste | standard, halal, kosher, no_pork | Vide si l'utilisateur est végétarien (RG16) | Utilisateur | Questionnaire de démarrage, profil |
| `is_vegetarian` | L'utilisateur est végétarien | Booléen | Vrai ou faux | Obligatoire, faux par défaut (RG16) | Utilisateur | Questionnaire de démarrage, profil |
| `is_vegan` | L'utilisateur est végan | Booléen | Vrai ou faux | Obligatoire ; végan implique végétarien (RG16) | Utilisateur | Questionnaire de démarrage, profil |
| `updated_at` | Dernière modification du profil | Date et heure | UTC | Obligatoire | Système | À chaque modification |

### HEALTH_CONSENT

Une occurrence : un consentement santé donné à une date, éventuellement retiré ensuite.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_health_consent` | Identifiant du consentement | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `text_version` | Version du texte de consentement affiché | Alphanumérique | 20 caractères au plus (ex. 2026-11-v1) | Obligatoire (RG10) | Système | À l'ajout |
| `granted_at` | Moment du consentement | Date et heure | UTC | Obligatoire | Utilisateur | À l'ajout |
| `withdrawn_at` | Moment du retrait | Date et heure | UTC | Vide tant que le consentement est actif ; postérieur à granted_at ; un seul consentement actif par utilisateur (RG10, RG11) | Utilisateur | Au retrait |

### DAILY_ACTIVE_ENERGY ★

Une occurrence : l'énergie active d'un jour, importée de l'app Santé.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_daily_active_energy` | Identifiant de la valeur journalière | Identifiant | UUID | Clé primaire | Système | À l'import |
| `day` | Date locale | Date | AAAA-MM-JJ | Obligatoire ; unique pour un même utilisateur (RG40) | Santé | À l'import |
| `kcal` | Énergie active du jour (hors repos) | Numérique | Décimal, 2 décimales | Obligatoire, 0 à 10 000 ; affichée seulement, jamais additionnée (RG40) | Santé | À chaque import du jour |
| `imported_at` | Moment du dernier import | Date et heure | UTC | Obligatoire | Système | À chaque import |

### WEIGH_IN ★

Une occurrence : une pesée d'un utilisateur, un jour donné.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_weigh_in` | Identifiant de la pesée | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `weighed_on` | Date locale de la pesée | Date | AAAA-MM-JJ | Obligatoire ; une pesée par jour et par utilisateur (RG39) | Utilisateur ou Santé | À l'ajout |
| `weight_kg` | Poids | Numérique | Décimal, 2 décimales, en kg | Obligatoire, 30 à 300 (RG13) ; effacé quand la pesée importée est ignorée (minimisation, RG39) | Utilisateur ou Santé | À l'ajout et à la modification |
| `source` | Origine de la pesée | Liste | manual, health | Obligatoire ; une saisie l'emporte sur Santé le même jour (RG39) | Système | À l'ajout |
| `health_uuid` | Identifiant de l'objet dans l'app Santé | Identifiant | UUID | Facultatif ; obligatoire si source = health | Santé | À l'import ou à l'écriture dans Santé |
| `is_ignored` | Pesée importée supprimée par l'utilisateur, à ne pas réimporter | Booléen | Vrai ou faux | Obligatoire, faux par défaut ; seulement pour une pesée importée, dont le poids est alors effacé (RG39) | Utilisateur | À la suppression d'une pesée importée |
| `created_at` | Date d'enregistrement | Date et heure | UTC | Obligatoire | Système | À l'ajout |

## Objectifs

### CALORIE_GOAL

Une occurrence : l'objectif calorique et la répartition des macros d'un utilisateur.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_calorie_goal` | Identifiant de l'objectif | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `mode` | Mode de l'objectif | Liste | computed, manual | Obligatoire ; computed exige un profil de santé complet (RG34, RG35) | Utilisateur | À la modification |
| `manual_kcal` | Objectif saisi. En mode calculé, la valeur n'est pas stockée : elle se calcule (02-formules.md §3) | Numérique | Entier, en kcal | Obligatoire en mode manual, 1 200 à 6 000 ; vide en mode computed (RG35) | Utilisateur, ou dernière valeur calculée au retrait du consentement (RG11) | À la modification |
| `protein_g_target` | Objectif quotidien de protéines | Numérique | Entier, en g | Obligatoire, 0 à 1 000 ; proposé à 15 % de l'objectif calorique (RG36) | Calcul interne ou utilisateur | À la modification de l'objectif |
| `carbs_g_target` | Objectif quotidien de glucides | Numérique | Entier, en g | Obligatoire, 0 à 1 000 ; proposé à 48 % de l'objectif calorique (RG36) | Calcul interne ou utilisateur | À la modification de l'objectif |
| `fat_g_target` | Objectif quotidien de lipides | Numérique | Entier, en g | Obligatoire, 0 à 1 000 ; proposé à 37 % de l'objectif calorique (RG36) | Calcul interne ou utilisateur | À la modification de l'objectif |
| `macros_custom` | Les objectifs de macros ont été choisis par l'utilisateur | Booléen | Vrai ou faux | Obligatoire, faux par défaut ; s'il est faux, l'API recalcule les grammes quand l'objectif calorique change (RG36) | Système | À la modification des macros |
| `updated_at` | Dernière modification | Date et heure | UTC | Obligatoire | Système | À chaque modification |

### ACTIVITY_GOAL

Une occurrence : un objectif d'activité d'un utilisateur.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_activity_goal` | Identifiant de l'objectif d'activité | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `metric` | Mesure suivie | Liste | sessions, minutes, kcal | Obligatoire (RG37) | Utilisateur | À l'ajout et à la modification |
| `period` | Période | Liste | day, week, session | Obligatoire ; session seulement pour kcal (RG37) | Utilisateur | À l'ajout et à la modification |
| `target_value` | Valeur visée | Numérique | Entier | Obligatoire, plus de 0 (RG37) | Utilisateur | À l'ajout |
| `valid_from` | Premier jour où l'objectif s'applique | Date | AAAA-MM-JJ | Obligatoire (RG37) | Système | À l'ajout |
| `valid_to` | Dernier jour où l'objectif s'applique | Date | AAAA-MM-JJ | Vide tant que l'objectif est en cours ; une modification clôt la ligne et en crée une nouvelle ; un seul objectif en cours par mesure, période et catégorie (RG37) | Système | À la modification ou à la suppression |
| `created_at` | Date de création | Date et heure | UTC | Obligatoire | Système | À l'ajout |

### REMINDER_SETTING

Une occurrence : le réglage d'un type de rappel ou de message pour un utilisateur.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_reminder_setting` | Identifiant du réglage | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `kind` | Type de notification | Liste | workout_reminder, weigh_in_reminder, motivation, evening_encouragement | Obligatoire ; un réglage par type et par utilisateur (RG42) | Système | À l'ajout |
| `is_enabled` | Notification activée | Booléen | Vrai ou faux | Obligatoire, vrai par défaut (RG42) | Utilisateur | À la modification |
| `send_time` | Heure locale d'envoi | Heure | hh:mm | Obligatoire, 18:00 par défaut (RG42) | Utilisateur | À la modification |

### CALORIE_TARGET_HISTORY

Une occurrence : l'objectif calorique et les macros qui s'appliquent à partir d'un jour donné, figés.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_calorie_target_history` | Identifiant de la version | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `effective_from` | Premier jour où cette version s'applique | Date | AAAA-MM-JJ | Obligatoire ; une version par jour et par objectif ; s'applique jusqu'à la version suivante (RG52) | Système | À chaque changement de la cible |
| `kcal_target` | Objectif calorique figé | Numérique | Entier, en kcal | Obligatoire, 1 200 à 6 000 (RG34, RG35) | Calcul interne ou utilisateur | À chaque changement de la cible |
| `protein_g_target` | Objectif de protéines figé | Numérique | Entier, en g | Obligatoire, 0 à 1 000 | Calcul interne ou utilisateur | À chaque changement de la cible |
| `carbs_g_target` | Objectif de glucides figé | Numérique | Entier, en g | Obligatoire, 0 à 1 000 | Calcul interne ou utilisateur | À chaque changement de la cible |
| `fat_g_target` | Objectif de lipides figé | Numérique | Entier, en g | Obligatoire, 0 à 1 000 | Calcul interne ou utilisateur | À chaque changement de la cible |
| `mode` | Mode de l'objectif à cette date | Liste | computed, manual | Obligatoire ; les versions calculées sont effacées au retrait du consentement (RG11) | Système | À chaque changement de la cible |

## Alimentation

### FOOD_GROUP

Une occurrence : un groupe d'aliments de CIQUAL (catégorie, p. 22 du cahier).

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_food_group` | Identifiant du groupe | Identifiant | UUID | Clé primaire | Système | Au chargement du référentiel |
| `ciqual_group_code` | Code du groupe dans CIQUAL | Alphanumérique | 2 caractères (ex. 04) | Obligatoire, unique | CIQUAL 2025 | Au chargement du référentiel |
| `name_fr` | Nom français du groupe | Alphanumérique | 120 caractères au plus | Obligatoire | CIQUAL 2025 | Au chargement du référentiel |
| `name_en` | Nom anglais du groupe | Alphanumérique | 120 caractères au plus | Obligatoire (RG49) | Traduction ZakFit | Au chargement du référentiel |

### FOOD

Une occurrence : un aliment, de base (CIQUAL ou ajouté par un administrateur) ou personnalisé.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_food` | Identifiant de l'aliment | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `ciqual_code` | Code CIQUAL de l'aliment | Alphanumérique | 10 caractères au plus | Unique ; vide pour un aliment personnalisé ou ajouté par un administrateur (RG19) | CIQUAL 2025 | Au chargement du référentiel |
| `name_fr` | Nom français | Alphanumérique | 150 caractères au plus | Obligatoire | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `name_en` | Nom anglais | Alphanumérique | 150 caractères au plus | Obligatoire pour un aliment de base, facultatif pour un aliment personnalisé (RG49) | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `kcal_100g` | Énergie pour 100 g (règlement UE 1169/2011) | Numérique | Décimal, 3 décimales (précision de CIQUAL) | Obligatoire, 0 à 900 ; cohérente avec les macros (RG18) | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `protein_100g` | Protéines pour 100 g | Numérique | Décimal, 4 décimales, en g | Obligatoire, 0 à 100 (RG18) | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `carbs_100g` | Glucides pour 100 g | Numérique | Décimal, 4 décimales, en g | Obligatoire, 0 à 100 (RG18) | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `fat_100g` | Lipides pour 100 g | Numérique | Décimal, 4 décimales, en g | Obligatoire, 0 à 100 ; P + G + L ≤ 100 g, ou 100,5 g pour un aliment de base (RG18) | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `fiber_100g` | Fibres pour 100 g | Numérique | Décimal, 4 décimales, en g | Facultatif (inconnu) ; 0 à 100 | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `alcohol_100g` | Alcool (éthanol) pour 100 g | Numérique | Décimal, 4 décimales, en g | Facultatif (inconnu) ; 0 à 100 | CIQUAL 2025, administrateur ou utilisateur | À l'ajout et à la modification |
| `contains_meat` | Contient de la viande ou de la gélatine | Booléen | Vrai ou faux | Obligatoire ; implique contains_animal_product (RG21) | Étiquetage ZakFit ou utilisateur | À l'ajout et à la modification |
| `contains_pork` | Contient ou peut contenir du porc | Booléen | Vrai ou faux | Obligatoire ; implique contains_meat (RG21) | Étiquetage ZakFit ou utilisateur | À l'ajout et à la modification |
| `contains_animal_product` | Contient un produit animal (exclu du régime végan) | Booléen | Vrai ou faux | Obligatoire (RG21) | Étiquetage ZakFit ou utilisateur | À l'ajout et à la modification |
| `contains_alcohol` | Contient de l'alcool (0,5 g pour 100 g ou plus, ou cuisiné à l'alcool) | Booléen | Vrai ou faux | Obligatoire ; vrai dès que alcohol_100g ≥ 0,5 (RG21) | Étiquetage ZakFit ou utilisateur | À l'ajout et à la modification |
| `labels_verified` | Les étiquettes et allergènes ont été vérifiés | Booléen | Vrai ou faux | Obligatoire ; faux = « allergènes non renseignés » (RG21) | Étiquetage ZakFit ou utilisateur | À l'ajout et à la modification |
| `is_archived` | Aliment archivé : absent de la recherche, gardé pour l'historique | Booléen | Vrai ou faux | Obligatoire, faux par défaut (RG22, RG46) | Administrateur ou utilisateur | À l'archivage |
| `created_at` | Date de création | Date et heure | UTC | Obligatoire | Système | À l'ajout |

### FOOD_PORTION

Une occurrence : une unité de mesure d'un aliment, avec son poids (« 1 œuf moyen = 50 g »).

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_food_portion` | Identifiant de la portion | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `label_fr` | Libellé français de l'unité | Alphanumérique | 120 caractères au plus | Obligatoire (RG20) | USDA SR Legacy adapté, ou estimation | À l'ajout et à la modification |
| `label_en` | Libellé anglais de l'unité | Alphanumérique | 120 caractères au plus | Obligatoire pour un aliment de base ; pour un aliment personnalisé, l'API recopie label_fr (RG49) | USDA SR Legacy adapté, estimation ou utilisateur | À l'ajout et à la modification |
| `grams` | Poids d'une unité | Numérique | Décimal, 2 décimales, en g | Obligatoire, plus de 0 et 2 000 au plus (RG20) | USDA SR Legacy adapté, ou estimation | À l'ajout et à la modification |
| `provenance` | Provenance du poids de l'unité | Alphanumérique | 200 caractères au plus (ex. USDA SR Legacy fdc_id=171287) | Facultatif | Système | À l'ajout |

### MEAL

Une occurrence : un repas d'un utilisateur, un jour donné.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_meal` | Identifiant du repas | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `meal_type` | Type de repas | Liste | breakfast, lunch, dinner, snack | Obligatoire (RG23) | Utilisateur | À l'ajout et à la modification |
| `eaten_on` | Date locale du repas | Date | AAAA-MM-JJ | Obligatoire ; pas dans le futur (RG23) | Utilisateur | À l'ajout et à la modification |
| `origin` | Façon dont le repas a été saisi | Liste | manual, favorite, photo | Obligatoire (RG28) | Système | À l'ajout |
| `created_at` | Date de création | Date et heure | UTC | Obligatoire | Système | À l'ajout |
| `updated_at` | Dernière modification | Date et heure | UTC | Obligatoire | Système | À chaque modification |

### MEAL_ITEM

Une occurrence : une ligne d'un repas : un aliment et sa quantité, avec ses valeurs figées.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_meal_item` | Identifiant de la ligne | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `quantity_g` | Quantité consommée | Numérique | Décimal, 2 décimales, en g | Obligatoire, 1 à 5 000 (RG24) | Utilisateur ou calcul (unités × poids) | À l'ajout et à la modification |
| `portion_count` | Nombre d'unités, si la quantité a été saisie en unités | Numérique | Décimal, 2 décimales | Présent si et seulement si une unité est choisie ; plus de 0 ; l'unité appartient à l'aliment de la ligne (RG20) | Utilisateur | À l'ajout et à la modification |
| `kcal` | Énergie de la ligne, figée à l'enregistrement | Numérique | Décimal, 2 décimales | Obligatoire ; calculée par l'API (RG24, RG25) | Calcul interne : kcal_100g × quantity_g / 100 | À l'ajout et quand la quantité change |
| `protein_g` | Protéines de la ligne, figées | Numérique | Décimal, 2 décimales, en g | Obligatoire (RG24, RG25) | Calcul interne | À l'ajout et quand la quantité change |
| `carbs_g` | Glucides de la ligne, figés | Numérique | Décimal, 2 décimales, en g | Obligatoire (RG24, RG25) | Calcul interne | À l'ajout et quand la quantité change |
| `fat_g` | Lipides de la ligne, figés | Numérique | Décimal, 2 décimales, en g | Obligatoire (RG24, RG25) | Calcul interne | À l'ajout et quand la quantité change |
| `estimated_g` | Quantité estimée par l'analyse photo, avant correction | Numérique | Décimal, 2 décimales, en g | Facultatif ; seulement pour un repas d'origine photo (RG28) | Modèle d'Apple sur l'appareil | À l'ajout |

### FAVORITE_MEAL

Une occurrence : un repas favori, réutilisable, d'un utilisateur.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_favorite_meal` | Identifiant du favori | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `name` | Nom donné au favori | Alphanumérique | 1 à 80 caractères | Obligatoire ; unique pour un même utilisateur (RG27) | Utilisateur | À l'ajout et à la modification |
| `created_at` | Date de création | Date et heure | UTC | Obligatoire | Système | À l'ajout |

### FAVORITE_ITEM

Une occurrence : un aliment d'un repas favori, avec sa quantité.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_favorite_item` | Identifiant de la ligne du favori | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `quantity_g` | Quantité | Numérique | Décimal, 2 décimales, en g | Obligatoire, 1 à 5 000 (RG27) | Utilisateur | À l'ajout et à la modification |
| `portion_count` | Nombre d'unités, si saisi en unités | Numérique | Décimal, 2 décimales | Présent si et seulement si une unité est choisie ; plus de 0 ; l'unité appartient à l'aliment (RG20) | Utilisateur | À l'ajout et à la modification |

## Activité

### ACTIVITY

Une occurrence : une séance d'activité physique d'un utilisateur.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_activity` | Identifiant de la séance | Identifiant | UUID | Clé primaire | Système | À l'ajout |
| `performed_at` | Début de la séance | Date et heure | UTC | Obligatoire ; pas dans le futur (RG30) | Utilisateur ou Santé | À l'ajout et à la modification |
| `performed_on` | Jour local de la séance, figé à l'enregistrement dans le fuseau de l'utilisateur | Date | AAAA-MM-JJ | Obligatoire ; calculé par l'API depuis performed_at et time_zone (RG38) | Calcul interne | À l'ajout et quand performed_at change |
| `duration_min` | Durée | Numérique | Entier, en minutes | Obligatoire, 1 à 600 (RG30) | Utilisateur ou Santé | À l'ajout et à la modification |
| `kcal` | Calories brûlées par la séance | Numérique | Décimal, 2 décimales | Facultatif, 0 à 5 000 ; vide si non renseignées (RG31) | Utilisateur, Santé ou calcul interne (MET net) | À l'ajout et à la modification |
| `kcal_status` | État des calories | Liste | entered, estimated, unknown | Obligatoire ; unknown si et seulement si kcal est vide (RG31) | Système | À l'ajout et à la modification |
| `source` | Origine de la séance | Liste | manual, health | Obligatoire (RG33) | Système | À l'ajout |
| `health_uuid` | Identifiant de l'objet dans l'app Santé (importé ou écrit par ZakFit) | Identifiant | UUID | Facultatif ; obligatoire si source = health ; unique pour un même utilisateur (RG33) | Santé | À l'import ou à l'écriture dans Santé |
| `is_ignored` | Séance importée supprimée par l'utilisateur, à ne pas réimporter | Booléen | Vrai ou faux | Obligatoire, faux par défaut ; seulement pour une séance importée, dont les kcal sont alors effacées (RG33) | Utilisateur | À la suppression d'une séance importée |
| `created_at` | Date de création | Date et heure | UTC | Obligatoire | Système | À l'ajout |
| `updated_at` | Dernière modification | Date et heure | UTC | Obligatoire | Système | À chaque modification |

## Référentiels

### ALLERGEN

Une occurrence : un des 14 allergènes réglementaires.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_allergen` | Identifiant de l'allergène | Identifiant | UUID | Clé primaire | Système | Au chargement du référentiel |
| `code` | Code stable de l'allergène | Alphanumérique | 30 caractères au plus (ex. gluten, lait) | Obligatoire, unique, liste du règlement UE 1169/2011 annexe II (RG17) | Système | Au chargement du référentiel |
| `name_fr` | Nom français | Alphanumérique | 120 caractères au plus | Obligatoire | Système | Au chargement du référentiel |
| `name_en` | Nom anglais | Alphanumérique | 120 caractères au plus | Obligatoire (RG49) | Système | Au chargement du référentiel |

### ACTIVITY_CATEGORY

Une occurrence : une catégorie d'activité (cardio, musculation…).

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_activity_category` | Identifiant de la catégorie | Identifiant | UUID | Clé primaire | Système | Au chargement du référentiel |
| `code` | Code stable de la catégorie | Alphanumérique | 30 caractères au plus (ex. cardio) | Obligatoire, unique (RG29) | Système | Au chargement du référentiel |
| `name_fr` | Nom français | Alphanumérique | 60 caractères au plus | Obligatoire | Système | Au chargement du référentiel |
| `name_en` | Nom anglais | Alphanumérique | 60 caractères au plus | Obligatoire (RG49) | Système | Au chargement du référentiel |

### ACTIVITY_TYPE

Une occurrence : un type d'activité du Compendium 2024, avec son MET.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_activity_type` | Identifiant du type d'activité | Identifiant | UUID | Clé primaire | Système | Au chargement du référentiel |
| `compendium_code` | Code de l'activité dans le Compendium 2024 | Alphanumérique | 5 chiffres (ex. 12050) | Obligatoire, unique (RG29) | Compendium 2024 | Au chargement du référentiel ou à la création par un administrateur |
| `name_fr` | Nom français | Alphanumérique | 80 caractères au plus | Obligatoire | Traduction ZakFit | À l'ajout et à la modification |
| `name_en` | Nom anglais | Alphanumérique | 80 caractères au plus | Obligatoire (RG49) | Traduction ZakFit | À l'ajout et à la modification |
| `met` | Équivalent métabolique (MET brut du Compendium) | Numérique | Décimal, 1 décimale | Obligatoire, 1 ou plus ; jamais modifié (RG29) | Compendium 2024 | À l'ajout |
| `difficulty` | Niveau de difficulté, tiré de la classe d'intensité du Compendium : léger, modéré, vigoureux | Liste | easy, moderate, hard | Obligatoire ; easy si MET < 3, moderate de 3 à 5,9, hard à partir de 6 (RG29) | Calcul interne au chargement, modifiable par l'administrateur | À l'ajout et à la modification |
| `instructions_fr` | Instructions ou conseils de pratique, en français | Alphanumérique | Texte, 2 000 caractères au plus | Facultatif (p. 22) | Administrateur | À la modification |
| `instructions_en` | Instructions ou conseils de pratique, en anglais | Alphanumérique | Texte, 2 000 caractères au plus | Facultatif (RG49) | Administrateur | À la modification |
| `is_archived` | Type archivé : non proposé, gardé pour l'historique | Booléen | Vrai ou faux | Obligatoire, faux par défaut (RG46) | Administrateur | À l'archivage |

### MUSCLE_GROUP

Une occurrence : un groupe musculaire sollicité par des exercices.

| Nom | Description | Type | Format | Contraintes | Origine | Mise à jour |
|---|---|---|---|---|---|---|
| `id_muscle_group` | Identifiant du groupe musculaire | Identifiant | UUID | Clé primaire | Système | Au chargement du référentiel |
| `code` | Code stable du groupe musculaire | Alphanumérique | 30 caractères au plus (ex. legs) | Obligatoire, unique (RG29) | Système | Au chargement du référentiel |
| `name_fr` | Nom français | Alphanumérique | 60 caractères au plus | Obligatoire | Système | Au chargement du référentiel |
| `name_en` | Nom anglais | Alphanumérique | 60 caractères au plus | Obligatoire (RG49) | Système | Au chargement du référentiel |
