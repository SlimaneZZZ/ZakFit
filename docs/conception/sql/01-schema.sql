-- ZakFit : schéma MariaDB 10.4. Généré par docs/conception/modele/generer.py, ne pas modifier à la main.
-- À exécuter dans une base vide : mariadb -u <compte> <base> < 01-schema.sql
SET NAMES utf8mb4;

CREATE TABLE `user` (
  id_user VARBINARY(16) NOT NULL,
  last_name VARCHAR(50) NOT NULL,
  first_name VARCHAR(50) NOT NULL,
  email VARCHAR(254) NOT NULL,
  password_hash CHAR(60) NOT NULL,
  role ENUM('user','admin') NOT NULL DEFAULT 'user',
  status ENUM('active','blocked','suspended') NOT NULL DEFAULT 'active',
  blocked_until DATETIME(6) NULL,
  adult_declared_at DATETIME(6) NOT NULL,
  time_zone VARCHAR(64) NOT NULL DEFAULT 'Europe/Paris',
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  CONSTRAINT pk_user PRIMARY KEY (id_user),
  CONSTRAINT uq_user_email UNIQUE (email),
  CONSTRAINT ck_user_blocked_until CHECK (status = 'blocked' OR blocked_until IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `health_profile` (
  id_health_profile VARBINARY(16) NOT NULL,
  birth_year SMALLINT NULL,
  sex ENUM('female','male') NULL,
  height_cm SMALLINT NULL,
  activity_level ENUM('low','moderate','active','very_active') NULL,
  goal_orientation ENUM('lose','maintain','gain') NULL,
  meat_preference ENUM('standard','halal','kosher','no_pork') NULL,
  is_vegetarian BOOLEAN NOT NULL DEFAULT FALSE,
  is_vegan BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_health_profile PRIMARY KEY (id_health_profile),
  CONSTRAINT fk_health_profile_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT uq_health_profile_id_user UNIQUE (id_user),
  CONSTRAINT ck_health_profile_height CHECK (height_cm IS NULL OR height_cm BETWEEN 100 AND 250),
  CONSTRAINT ck_health_profile_birth_year CHECK (birth_year IS NULL OR birth_year >= 1900),
  CONSTRAINT ck_health_profile_vegan CHECK (is_vegan = FALSE OR is_vegetarian = TRUE),
  CONSTRAINT ck_health_profile_meat CHECK (is_vegetarian = FALSE OR meat_preference IS NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `health_consent` (
  id_health_consent VARBINARY(16) NOT NULL,
  text_version VARCHAR(20) NOT NULL,
  granted_at DATETIME(6) NOT NULL,
  withdrawn_at DATETIME(6) NULL,
  id_user VARBINARY(16) NOT NULL,
  active_flag TINYINT AS (IF(withdrawn_at IS NULL, 1, NULL)) PERSISTENT,
  CONSTRAINT pk_health_consent PRIMARY KEY (id_health_consent),
  CONSTRAINT fk_health_consent_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT ck_health_consent_dates CHECK (withdrawn_at IS NULL OR withdrawn_at >= granted_at),
  CONSTRAINT uq_health_consent_active UNIQUE (id_user, active_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `allergen` (
  id_allergen VARBINARY(16) NOT NULL,
  code VARCHAR(30) NOT NULL,
  name_fr VARCHAR(120) NOT NULL,
  name_en VARCHAR(120) NOT NULL,
  CONSTRAINT pk_allergen PRIMARY KEY (id_allergen),
  CONSTRAINT uq_allergen_code UNIQUE (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `food_group` (
  id_food_group VARBINARY(16) NOT NULL,
  ciqual_group_code CHAR(2) NOT NULL,
  name_fr VARCHAR(120) NOT NULL,
  name_en VARCHAR(120) NOT NULL,
  CONSTRAINT pk_food_group PRIMARY KEY (id_food_group),
  CONSTRAINT uq_food_group_code UNIQUE (ciqual_group_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `food` (
  id_food VARBINARY(16) NOT NULL,
  ciqual_code VARCHAR(10) NULL,
  name_fr VARCHAR(150) NOT NULL,
  name_en VARCHAR(150) NULL,
  kcal_100g DECIMAL(6,2) NOT NULL,
  protein_100g DECIMAL(5,2) NOT NULL,
  carbs_100g DECIMAL(5,2) NOT NULL,
  fat_100g DECIMAL(5,2) NOT NULL,
  fiber_100g DECIMAL(5,2) NULL,
  alcohol_100g DECIMAL(5,2) NULL,
  contains_meat BOOLEAN NOT NULL DEFAULT FALSE,
  contains_pork BOOLEAN NOT NULL DEFAULT FALSE,
  contains_animal_product BOOLEAN NOT NULL DEFAULT FALSE,
  contains_alcohol BOOLEAN NOT NULL DEFAULT FALSE,
  labels_verified BOOLEAN NOT NULL DEFAULT FALSE,
  is_archived BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME(6) NOT NULL,
  id_food_group VARBINARY(16) NULL,
  id_user VARBINARY(16) NULL,
  CONSTRAINT pk_food PRIMARY KEY (id_food),
  CONSTRAINT fk_food_food_group FOREIGN KEY (id_food_group) REFERENCES `food_group` (id_food_group) ON DELETE RESTRICT,
  CONSTRAINT fk_food_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT uq_food_ciqual UNIQUE (ciqual_code),
  CONSTRAINT ck_food_kcal CHECK (kcal_100g BETWEEN 0 AND 900),
  CONSTRAINT ck_food_macros CHECK (protein_100g BETWEEN 0 AND 100 AND carbs_100g BETWEEN 0 AND 100 AND fat_100g BETWEEN 0 AND 100 AND protein_100g + carbs_100g + fat_100g <= IF(id_user IS NULL, 100.5, 100)),
  CONSTRAINT ck_food_labels CHECK ((contains_pork = FALSE OR contains_meat = TRUE) AND (contains_meat = FALSE OR contains_animal_product = TRUE) AND (alcohol_100g IS NULL OR alcohol_100g < 0.5 OR contains_alcohol = TRUE)),
  CONSTRAINT ck_food_group CHECK (id_user IS NOT NULL OR id_food_group IS NOT NULL),
  CONSTRAINT ck_food_others CHECK ((fiber_100g IS NULL OR fiber_100g BETWEEN 0 AND 100) AND (alcohol_100g IS NULL OR alcohol_100g BETWEEN 0 AND 100)),
  CONSTRAINT ck_food_custom_no_ciqual CHECK (id_user IS NULL OR ciqual_code IS NULL),
  CONSTRAINT ck_food_base_name_en CHECK (id_user IS NOT NULL OR name_en IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `food_portion` (
  id_food_portion VARBINARY(16) NOT NULL,
  label_fr VARCHAR(120) NOT NULL,
  label_en VARCHAR(120) NULL,
  grams DECIMAL(6,1) NOT NULL,
  provenance VARCHAR(200) NULL,
  id_food VARBINARY(16) NOT NULL,
  CONSTRAINT pk_food_portion PRIMARY KEY (id_food_portion),
  CONSTRAINT fk_food_portion_food FOREIGN KEY (id_food) REFERENCES `food` (id_food) ON DELETE CASCADE,
  CONSTRAINT ck_food_portion_grams CHECK (grams > 0 AND grams <= 2000),
  CONSTRAINT uq_food_portion_food UNIQUE (id_food_portion, id_food)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `meal` (
  id_meal VARBINARY(16) NOT NULL,
  meal_type ENUM('breakfast','lunch','dinner','snack') NOT NULL,
  eaten_on DATE NOT NULL,
  origin ENUM('manual','favorite','photo') NOT NULL DEFAULT 'manual',
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_meal PRIMARY KEY (id_meal),
  CONSTRAINT fk_meal_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `meal_item` (
  id_meal_item VARBINARY(16) NOT NULL,
  quantity_g DECIMAL(7,2) NOT NULL,
  portion_count DECIMAL(6,2) NULL,
  kcal DECIMAL(8,2) NOT NULL,
  protein_g DECIMAL(7,2) NOT NULL,
  carbs_g DECIMAL(7,2) NOT NULL,
  fat_g DECIMAL(7,2) NOT NULL,
  estimated_g DECIMAL(7,2) NULL,
  id_meal VARBINARY(16) NOT NULL,
  id_food VARBINARY(16) NOT NULL,
  id_food_portion VARBINARY(16) NULL,
  CONSTRAINT pk_meal_item PRIMARY KEY (id_meal_item),
  CONSTRAINT fk_meal_item_meal FOREIGN KEY (id_meal) REFERENCES `meal` (id_meal) ON DELETE CASCADE,
  CONSTRAINT fk_meal_item_food FOREIGN KEY (id_food) REFERENCES `food` (id_food) ON DELETE RESTRICT,
  CONSTRAINT fk_meal_item_food_portion FOREIGN KEY (id_food_portion) REFERENCES `food_portion` (id_food_portion) ON DELETE RESTRICT,
  CONSTRAINT ck_meal_item_quantity CHECK (quantity_g BETWEEN 1 AND 5000),
  CONSTRAINT ck_meal_item_portion CHECK ((id_food_portion IS NULL) = (portion_count IS NULL) AND (portion_count IS NULL OR portion_count > 0)),
  CONSTRAINT ck_meal_item_values CHECK (kcal >= 0 AND protein_g >= 0 AND carbs_g >= 0 AND fat_g >= 0),
  CONSTRAINT fk_meal_item_portion_food FOREIGN KEY (id_food_portion, id_food) REFERENCES food_portion (id_food_portion, id_food) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `favorite_meal` (
  id_favorite_meal VARBINARY(16) NOT NULL,
  name VARCHAR(80) NOT NULL,
  created_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_favorite_meal PRIMARY KEY (id_favorite_meal),
  CONSTRAINT fk_favorite_meal_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT uq_favorite_meal_name UNIQUE (id_user, name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `favorite_item` (
  id_favorite_item VARBINARY(16) NOT NULL,
  quantity_g DECIMAL(7,2) NOT NULL,
  portion_count DECIMAL(6,2) NULL,
  id_favorite_meal VARBINARY(16) NOT NULL,
  id_food VARBINARY(16) NOT NULL,
  id_food_portion VARBINARY(16) NULL,
  CONSTRAINT pk_favorite_item PRIMARY KEY (id_favorite_item),
  CONSTRAINT fk_favorite_item_favorite_meal FOREIGN KEY (id_favorite_meal) REFERENCES `favorite_meal` (id_favorite_meal) ON DELETE CASCADE,
  CONSTRAINT fk_favorite_item_food FOREIGN KEY (id_food) REFERENCES `food` (id_food) ON DELETE RESTRICT,
  CONSTRAINT fk_favorite_item_food_portion FOREIGN KEY (id_food_portion) REFERENCES `food_portion` (id_food_portion) ON DELETE RESTRICT,
  CONSTRAINT ck_favorite_item_quantity CHECK (quantity_g BETWEEN 1 AND 5000),
  CONSTRAINT ck_favorite_item_portion CHECK ((id_food_portion IS NULL) = (portion_count IS NULL) AND (portion_count IS NULL OR portion_count > 0)),
  CONSTRAINT fk_favorite_item_portion_food FOREIGN KEY (id_food_portion, id_food) REFERENCES food_portion (id_food_portion, id_food) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `activity_category` (
  id_activity_category VARBINARY(16) NOT NULL,
  code VARCHAR(30) NOT NULL,
  name_fr VARCHAR(60) NOT NULL,
  name_en VARCHAR(60) NOT NULL,
  CONSTRAINT pk_activity_category PRIMARY KEY (id_activity_category),
  CONSTRAINT uq_activity_category_code UNIQUE (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `activity_type` (
  id_activity_type VARBINARY(16) NOT NULL,
  compendium_code CHAR(5) NOT NULL,
  name_fr VARCHAR(80) NOT NULL,
  name_en VARCHAR(80) NOT NULL,
  met DECIMAL(4,1) NOT NULL,
  difficulty ENUM('easy','moderate','hard') NOT NULL,
  instructions_fr VARCHAR(2000) NULL,
  instructions_en VARCHAR(2000) NULL,
  is_archived BOOLEAN NOT NULL DEFAULT FALSE,
  id_activity_category VARBINARY(16) NOT NULL,
  CONSTRAINT pk_activity_type PRIMARY KEY (id_activity_type),
  CONSTRAINT fk_activity_type_activity_category FOREIGN KEY (id_activity_category) REFERENCES `activity_category` (id_activity_category) ON DELETE RESTRICT,
  CONSTRAINT uq_activity_type_code UNIQUE (compendium_code),
  CONSTRAINT ck_activity_type_met CHECK (met >= 1)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `activity` (
  id_activity VARBINARY(16) NOT NULL,
  performed_at DATETIME(6) NOT NULL,
  duration_min SMALLINT NOT NULL,
  kcal DECIMAL(7,2) NULL,
  kcal_status ENUM('entered','estimated','unknown') NOT NULL,
  source ENUM('manual','health') NOT NULL DEFAULT 'manual',
  health_uuid VARBINARY(16) NULL,
  is_ignored BOOLEAN NOT NULL DEFAULT FALSE,
  created_at DATETIME(6) NOT NULL,
  updated_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  id_activity_type VARBINARY(16) NOT NULL,
  CONSTRAINT pk_activity PRIMARY KEY (id_activity),
  CONSTRAINT fk_activity_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT fk_activity_activity_type FOREIGN KEY (id_activity_type) REFERENCES `activity_type` (id_activity_type) ON DELETE RESTRICT,
  CONSTRAINT uq_activity_health UNIQUE (id_user, health_uuid),
  CONSTRAINT ck_activity_duration CHECK (duration_min BETWEEN 1 AND 600),
  CONSTRAINT ck_activity_kcal CHECK (kcal IS NULL OR kcal BETWEEN 0 AND 5000),
  CONSTRAINT ck_activity_kcal_status CHECK ((kcal_status = 'unknown') = (kcal IS NULL)),
  CONSTRAINT ck_activity_health_uuid CHECK (source = 'manual' OR health_uuid IS NOT NULL),
  CONSTRAINT ck_activity_ignored CHECK (is_ignored = FALSE OR source = 'health')
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `daily_active_energy` (
  id_daily_active_energy VARBINARY(16) NOT NULL,
  day DATE NOT NULL,
  kcal DECIMAL(7,2) NOT NULL,
  imported_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_daily_active_energy PRIMARY KEY (id_daily_active_energy),
  CONSTRAINT fk_daily_active_energy_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT uq_daily_active_energy UNIQUE (id_user, day),
  CONSTRAINT ck_daily_active_energy_kcal CHECK (kcal BETWEEN 0 AND 10000)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `weigh_in` (
  id_weigh_in VARBINARY(16) NOT NULL,
  weighed_on DATE NOT NULL,
  weight_kg DECIMAL(5,2) NOT NULL,
  source ENUM('manual','health') NOT NULL DEFAULT 'manual',
  health_uuid VARBINARY(16) NULL,
  created_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_weigh_in PRIMARY KEY (id_weigh_in),
  CONSTRAINT fk_weigh_in_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT uq_weigh_in_day UNIQUE (id_user, weighed_on),
  CONSTRAINT ck_weigh_in_weight CHECK (weight_kg BETWEEN 30 AND 300),
  CONSTRAINT ck_weigh_in_health_uuid CHECK (source = 'manual' OR health_uuid IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `calorie_goal` (
  id_calorie_goal VARBINARY(16) NOT NULL,
  mode ENUM('computed','manual') NOT NULL,
  manual_kcal SMALLINT NULL,
  protein_g_target SMALLINT NOT NULL,
  carbs_g_target SMALLINT NOT NULL,
  fat_g_target SMALLINT NOT NULL,
  macros_custom BOOLEAN NOT NULL DEFAULT FALSE,
  updated_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_calorie_goal PRIMARY KEY (id_calorie_goal),
  CONSTRAINT fk_calorie_goal_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT uq_calorie_goal_id_user UNIQUE (id_user),
  CONSTRAINT ck_calorie_goal_mode CHECK ((mode = 'computed' AND manual_kcal IS NULL) OR (mode = 'manual' AND manual_kcal IS NOT NULL AND manual_kcal BETWEEN 1200 AND 6000)),
  CONSTRAINT ck_calorie_goal_grams CHECK (protein_g_target BETWEEN 0 AND 1000 AND carbs_g_target BETWEEN 0 AND 1000 AND fat_g_target BETWEEN 0 AND 1000)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `activity_goal` (
  id_activity_goal VARBINARY(16) NOT NULL,
  metric ENUM('sessions','minutes','kcal') NOT NULL,
  period ENUM('day','week','session') NOT NULL,
  target_value INT NOT NULL,
  valid_from DATE NOT NULL,
  valid_to DATE NULL,
  created_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  id_activity_category VARBINARY(16) NULL,
  category_key VARBINARY(16) AS (IFNULL(id_activity_category, 0x00)) PERSISTENT,
  current_flag TINYINT AS (IF(valid_to IS NULL, 1, NULL)) PERSISTENT,
  CONSTRAINT pk_activity_goal PRIMARY KEY (id_activity_goal),
  CONSTRAINT fk_activity_goal_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT fk_activity_goal_activity_category FOREIGN KEY (id_activity_category) REFERENCES `activity_category` (id_activity_category) ON DELETE RESTRICT,
  CONSTRAINT ck_activity_goal_target CHECK (target_value > 0),
  CONSTRAINT ck_activity_goal_session CHECK (period <> 'session' OR metric = 'kcal'),
  CONSTRAINT ck_activity_goal_dates CHECK (valid_to IS NULL OR valid_to >= valid_from),
  CONSTRAINT uq_activity_goal UNIQUE (id_user, metric, period, category_key, current_flag)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `reminder_setting` (
  id_reminder_setting VARBINARY(16) NOT NULL,
  kind ENUM('workout_reminder','weigh_in_reminder','motivation','evening_encouragement') NOT NULL,
  is_enabled BOOLEAN NOT NULL DEFAULT TRUE,
  send_time TIME NOT NULL DEFAULT '18:00:00',
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_reminder_setting PRIMARY KEY (id_reminder_setting),
  CONSTRAINT fk_reminder_setting_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE,
  CONSTRAINT uq_reminder_setting UNIQUE (id_user, kind)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `admin_action` (
  id_admin_action VARBINARY(16) NOT NULL,
  action ENUM('block','suspend','reactivate','delete_user','create','update','archive','delete') NOT NULL,
  target_kind ENUM('user','food','activity_type') NOT NULL,
  target_id VARBINARY(16) NOT NULL,
  performed_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_admin_action PRIMARY KEY (id_admin_action),
  CONSTRAINT fk_admin_action_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `calorie_target_history` (
  id_calorie_target_history VARBINARY(16) NOT NULL,
  effective_from DATE NOT NULL,
  kcal_target SMALLINT NOT NULL,
  protein_g_target SMALLINT NOT NULL,
  carbs_g_target SMALLINT NOT NULL,
  fat_g_target SMALLINT NOT NULL,
  mode ENUM('computed','manual') NOT NULL,
  id_calorie_goal VARBINARY(16) NOT NULL,
  CONSTRAINT pk_calorie_target_history PRIMARY KEY (id_calorie_target_history),
  CONSTRAINT fk_calorie_target_history_calorie_goal FOREIGN KEY (id_calorie_goal) REFERENCES `calorie_goal` (id_calorie_goal) ON DELETE CASCADE,
  CONSTRAINT uq_calorie_target_history_day UNIQUE (id_calorie_goal, effective_from),
  CONSTRAINT ck_calorie_target_history_kcal CHECK (kcal_target BETWEEN 1200 AND 6000),
  CONSTRAINT ck_calorie_target_history_grams CHECK (protein_g_target BETWEEN 0 AND 1000 AND carbs_g_target BETWEEN 0 AND 1000 AND fat_g_target BETWEEN 0 AND 1000)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `muscle_group` (
  id_muscle_group VARBINARY(16) NOT NULL,
  code VARCHAR(30) NOT NULL,
  name_fr VARCHAR(60) NOT NULL,
  name_en VARCHAR(60) NOT NULL,
  CONSTRAINT pk_muscle_group PRIMARY KEY (id_muscle_group),
  CONSTRAINT uq_muscle_group_code UNIQUE (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `login_event` (
  id_login_event VARBINARY(16) NOT NULL,
  logged_in_at DATETIME(6) NOT NULL,
  id_user VARBINARY(16) NOT NULL,
  CONSTRAINT pk_login_event PRIMARY KEY (id_login_event),
  CONSTRAINT fk_login_event_user FOREIGN KEY (id_user) REFERENCES `user` (id_user) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `health_profile_allergen` (
  id_health_profile VARBINARY(16) NOT NULL,
  id_allergen VARBINARY(16) NOT NULL,
  CONSTRAINT pk_health_profile_allergen PRIMARY KEY (id_health_profile, id_allergen),
  CONSTRAINT fk_health_profile_allergen_health_profile FOREIGN KEY (id_health_profile) REFERENCES `health_profile` (id_health_profile) ON DELETE CASCADE,
  CONSTRAINT fk_health_profile_allergen_allergen FOREIGN KEY (id_allergen) REFERENCES `allergen` (id_allergen) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `food_allergen` (
  id_food VARBINARY(16) NOT NULL,
  id_allergen VARBINARY(16) NOT NULL,
  CONSTRAINT pk_food_allergen PRIMARY KEY (id_food, id_allergen),
  CONSTRAINT fk_food_allergen_food FOREIGN KEY (id_food) REFERENCES `food` (id_food) ON DELETE CASCADE,
  CONSTRAINT fk_food_allergen_allergen FOREIGN KEY (id_allergen) REFERENCES `allergen` (id_allergen) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `activity_type_muscle_group` (
  id_activity_type VARBINARY(16) NOT NULL,
  id_muscle_group VARBINARY(16) NOT NULL,
  CONSTRAINT pk_activity_type_muscle_group PRIMARY KEY (id_activity_type, id_muscle_group),
  CONSTRAINT fk_activity_type_muscle_group_activity_type FOREIGN KEY (id_activity_type) REFERENCES `activity_type` (id_activity_type) ON DELETE CASCADE,
  CONSTRAINT fk_activity_type_muscle_group_muscle_group FOREIGN KEY (id_muscle_group) REFERENCES `muscle_group` (id_muscle_group) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE INDEX ix_meal_user_day ON `meal` (id_user, eaten_on);
CREATE INDEX ix_meal_day_type ON `meal` (eaten_on, meal_type);
CREATE INDEX ix_activity_date ON `activity` (performed_at);
CREATE INDEX ix_user_created ON `user` (created_at);
CREATE INDEX ix_login_event_user_date ON `login_event` (id_user, logged_in_at);
CREATE INDEX ix_activity_user_date ON `activity` (id_user, performed_at);
CREATE INDEX ix_weigh_in_user_day ON `weigh_in` (id_user, weighed_on);
CREATE INDEX ix_food_name_fr ON `food` (name_fr);
CREATE INDEX ix_food_name_en ON `food` (name_en);
