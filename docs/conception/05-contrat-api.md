# ZakFit — contrat d'API

Version 1 du 27/11/2026. Le contrat complet, qui fait foi, est le fichier OpenAPI 3.1 [`api/openapi.yaml`](api/openapi.yaml) : 51 chemins, 78 opérations, 126 schémas, des exemples sur les opérations principales. Vapor le sert sous forme de page Swagger. Ce document en est la synthèse, pour la relecture.

Sources : [`01-analyse-fonctionnelle.md`](01-analyse-fonctionnelle.md) (UC, US, RG01 à RG53), [`02-formules.md`](02-formules.md), [`03-dictionnaire.md`](03-dictionnaire.md), [`04-mcd-mld-mpd.md`](04-mcd-mld-mpd.md) et [`sql/01-schema.sql`](sql/01-schema.sql). Les conventions de code et de nommage reprennent celles du projet LineUp (contrôleurs `appios` et `backoffice`, DTO, enum d'erreurs `AbortError`).

## 1. Conventions

### Préfixes, rôles et sécurité

| Préfixe | Accès | Contrôle |
|---|---|---|
| `/auth` | Public | `register` et `login` seulement |
| `/appios` | Tout compte connecté | `JWTMiddleware` (jeton valide), puis `AccountStatusMiddleware` (compte relu en base, statut contrôlé, compte rangé dans la requête) |
| `/backoffice` | Rôle `admin` | Les deux mêmes, puis `AdminMiddleware`, qui lit le rôle du compte relu en base, jamais celui du jeton (RG44) |

- **Jeton** : JWT signé, envoyé dans `Authorization: Bearer <jeton>`. Il ne contient que l'identifiant de l'utilisateur et expire 7 jours après la connexion (RG05). Contrairement au `StaffMiddleware` de LineUp, aucun contrôle ne lit le rôle dans le jeton : il vient du compte relu en base. La réponse de connexion donne `token` et `expiresAt`.
- **À chaque requête protégée**, l'API relit le compte : un compte bloqué ou suspendu reçoit 403, même avec un jeton valide, et un blocage dont la date de fin est passée est levé à cette requête (RG06). Un rôle retiré prend effet à la requête suivante.
- **Pas de déconnexion côté serveur** : l'app efface le jeton du Trousseau (RG08).
- **Données de l'utilisateur** : l'identifiant vient toujours du jeton, jamais de l'URL. La ressource d'un autre utilisateur répond 404, comme si elle n'existait pas (RG09).
- **Consentement santé** : les routes qui lisent ou écrivent une donnée de santé (profil de santé, pesées, imports de Santé, objectif calculé) répondent 409 sans consentement actif (RG10).
- **Back-office** : il appelle aussi les référentiels de `/appios` (allergènes, groupes, catégories, groupes musculaires), puisqu'un administrateur est un compte connecté. Aucune route du back-office ne renvoie de donnée de santé individuelle (RG45).

### Nommage

- **Chemins** : anglais, kebab-case, ressources au pluriel (`/appios/favorite-meals`, `/backoffice/activity-types`). Exceptions assumées : les ressources uniques de l'utilisateur connecté restent au singulier (`profile`, `health-profile`, `calorie-goal`, `dashboard`, `history`, `export`). Une action qui n'est ni un ajout ni une suppression est un sous-chemin en `PATCH`, comme `cancel` dans LineUp : `/appios/health-consents/withdraw`, `/backoffice/users/{userID}/status`.
- **Paramètres de chemin** : `{mealID}`, `{foodID}`… comme `:reservationID` dans LineUp.
- **Champs JSON** : camelCase anglais tiré du nom de la colonne. `kcal_100g` donne `kcal100g`, `protein_g_target` donne `proteinGTarget`, `eaten_on` donne `eatenOn`. L'identifiant propre d'une ressource s'appelle `id`. Une clé étrangère prend le suffixe `ID`, comme `categoryID` dans LineUp : `id_food` donne `foodID`, `health_uuid` donne `healthUUID`. Les valeurs calculées, qui n'ont pas de colonne, ont un nom descriptif (`totals`, `effectiveKcal`, `burned`).
- **Listes de valeurs** : les valeurs des `ENUM` du schéma SQL, telles quelles (`breakfast`, `computed`, `very_active`…).

### Formats

| Donnée | Format | Exemple |
|---|---|---|
| Identifiant | UUID en chaîne | `"1574251b-58e4-5550-8303-43da54e6be07"` |
| Instant (`DATETIME(6)` UTC) | ISO 8601 UTC | `"2026-11-27T11:30:00Z"` |
| Jour local (`DATE`) | `AAAA-MM-JJ`, dans le fuseau du profil | `"2026-11-27"` (repas, pesées, énergie active, validité des objectifs) |
| Heure locale (`TIME`) | `hh:mm` | `"18:00"` (rappels) |
| Grammes et kcal (`DECIMAL`) | Nombre JSON, 2 décimales au plus | `290.50` |

- Le fuseau (nom IANA) est enregistré dans le profil : l'app l'envoie à la connexion et quand il change (RG23). Il sert aux jours locaux, aux semaines ISO (lundi au dimanche) et aux mois civils (RG38). Le jour local d'un repas (`eatenOn`) et d'une séance (`performedOn`) est figé à l'enregistrement : changer de fuseau ne déplace pas les jours passés (RG38). `performedOn` est calculé par l'API depuis `performedAt` et le fuseau du profil ; il est en lecture seule, le client ne l'envoie pas.
- Les calculs se font en décimal, sans arrondi intermédiaire. L'API renvoie 2 décimales ; l'arrondi d'affichage (kcal à l'unité, macros à 0,1 g, 0,5 vers le haut) est fait par le client (`02-formules.md` §5).
- Les alertes et recommandations du tableau de bord sont des **codes avec des valeurs** (`macro_low`, `missingG: 36.23`) : l'app compose le texte en français ou en anglais (RG49). Seuls les messages d'erreur sont rédigés en français par l'API.
- Le client n'envoie jamais de valeur nutritionnelle pour un repas : seulement l'aliment, la quantité en grammes ou l'unité et le nombre d'unités. L'API calcule et fige les valeurs (RG24, RG25).

### Erreurs

Format de Vapor (`AbortError`), comme l'enum `ReservationsError` de LineUp :

```json
{ "error": true, "reason": "Repas introuvable." }
```

| Code | Quand |
|---|---|
| 400 | Validation : corps ou paramètre mal formé, identifiant qui n'est pas un UUID, valeur hors bornes, règle de gestion non respectée, plage dont la fin précède le début. Aussi un mot de passe actuel incorrect (changement de mot de passe, suppression du compte) |
| 401 | Jeton absent, invalide ou expiré ; identifiants de connexion invalides, avec un message unique (RG04) |
| 403 | Compte bloqué ou suspendu (RG06), rôle insuffisant (RG44), aliment de base modifié depuis l'app |
| 404 | Ressource absente, ou appartenant à un autre utilisateur (RG09). Aussi un identifiant du corps qui ne désigne rien (aliment, unité, type, catégorie, allergène), comme `noWorkshop` dans LineUp |
| 409 | Conflit d'état ou d'unicité : email ou nom de favori déjà pris, consentement absent ou déjà actif, objectif d'activité déjà en cours, pesée du jour existante, élément archivé, unité utilisée, code du Compendium existant, action d'un administrateur sur son propre compte |

### Pagination

Format de Vapor (`.paginate(for: req)`), comme l'index du back-office de LineUp :

```json
{ "items": [ ... ], "metadata": { "page": 1, "per": 10, "total": 42 } }
```

Paramètres `page` (1 par défaut) et `per` (10 par défaut, 100 au plus). Les listes paginées : recherche d'aliments, activités, utilisateurs, aliments de base, types d'activité, journal d'administration. Les autres listes sont bornées par une plage de dates (366 jours au plus) ou par nature (référentiels, favoris, réglages).

### Suppression et archivage

`DELETE` sur un aliment ou un type d'activité supprime l'élément s'il n'a jamais été utilisé, et l'archive sinon (RG22, RG46). La réponse 200 dit ce qui a été fait : `{ "id": "…", "outcome": "deleted" }` ou `"archived"`. Une séance ou une pesée importée de Santé n'est pas supprimée mais marquée ignorée (`is_ignored`) : elle n'est plus renvoyée, n'entre plus dans les calculs et ne revient pas au prochain import (RG33, RG39). Une séance ou une pesée saisie est supprimée. Un objectif d'activité est clos, pas effacé (RG37), sauf s'il a commencé le jour même : sa ligne est alors supprimée, car la clore donnerait `valid_to` avant `valid_from`.

## 2. Tableau des routes

Rôle « Utilisateur » : tout compte connecté, sous `/appios`. Les erreurs 401 et 403 valent pour toutes les routes protégées.

### Authentification

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| POST | `/auth/register` | Public | Créer un compte utilisateur | UC01 | RG01, RG02, RG03, RG07, RG12, RG23, RG42 | 201 | 400, 409 |
| POST | `/auth/login` | Public | Se connecter (app iOS et back-office) | UC02, UC30 | RG04, RG05, RG06, RG08, RG23, RG44, RG53 | 200 | 400, 401, 403 |

### Profil

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/profile` | Utilisateur | Lire son profil | UC03, UC05 | RG03, RG09 | 200 | 401, 403 |
| PATCH | `/appios/profile` | Utilisateur | Modifier son nom, son prénom ou son email | UC05 | RG01 | 200 | 400, 401, 403, 409 |
| DELETE | `/appios/profile` | Utilisateur | Supprimer son compte | UC07 | RG07, RG43, RG48 | 204 | 400, 401, 403, 409 |
| PATCH | `/appios/profile/password` | Utilisateur | Changer de mot de passe | UC05 | RG02, RG03, RG08 | 204 | 400, 401, 403 |
| PATCH | `/appios/profile/time-zone` | Utilisateur | Enregistrer le fuseau horaire de l'appareil | UC05 | RG23, RG38 | 200 | 400, 401, 403 |

### Consentement santé

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/health-consents` | Utilisateur | Lire l'historique de ses consentements | UC04, UC28 | RG10, RG11 | 200 | 401, 403 |
| POST | `/appios/health-consents` | Utilisateur | Donner son consentement santé | UC04 | RG10 | 201 | 400, 401, 403, 409 |
| PATCH | `/appios/health-consents/withdraw` | Utilisateur | Retirer son consentement santé | UC28 | RG11, RG52 | 200 | 401, 403, 409 |

### Profil de santé

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/health-profile` | Utilisateur | Lire son profil de santé | UC05 | RG10, RG34, RG39 | 200 | 401, 403, 409 |
| PATCH | `/appios/health-profile` | Utilisateur | Mettre à jour son profil de santé, ses régimes et ses allergènes | UC03, UC05 | RG12, RG13, RG16, RG17, RG34, RG52 | 200 | 400, 401, 403, 404, 409 |

### Référentiels

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/allergens` | Utilisateur | Lister les 14 allergènes réglementaires | UC05, UC12 | RG17, RG21, RG49 | 200 | 401, 403 |
| GET | `/appios/food-groups` | Utilisateur | Lister les groupes d'aliments de CIQUAL | UC12, UC13, UC34 | RG19, RG49 | 200 | 401, 403 |
| GET | `/appios/activity-categories` | Utilisateur | Lister les catégories d'activité avec leurs types | UC08 | RG29 | 200 | 401, 403 |
| GET | `/appios/activity-types` | Utilisateur | Lister les types d'activité | UC08, UC10 | RG29 | 200 | 400, 401, 403 |
| GET | `/appios/muscle-groups` | Utilisateur | Lister les groupes musculaires | UC08, UC35 | RG29 | 200 | 401, 403 |

### Aliments

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/foods` | Utilisateur | Rechercher un aliment | UC12 | RG19, RG21, RG22, RG46, RG51 | 200 | 400, 401, 403 |
| POST | `/appios/foods` | Utilisateur | Créer un aliment personnalisé | UC13 | RG18, RG19, RG20, RG21, RG49 | 201 | 400, 401, 403, 404 |
| GET | `/appios/foods/{foodID}` | Utilisateur | Lire le détail d'un aliment | UC12, UC14 | RG09, RG19, RG20, RG21, RG22 | 200 | 400, 401, 403, 404 |
| PATCH | `/appios/foods/{foodID}` | Utilisateur | Modifier un aliment personnalisé | UC13 | RG18, RG19, RG21, RG25 | 200 | 400, 401, 403, 404, 409 |
| DELETE | `/appios/foods/{foodID}` | Utilisateur | Supprimer ou archiver un aliment personnalisé | UC13 | RG22 | 200 | 400, 401, 403, 404 |
| POST | `/appios/foods/{foodID}/portions` | Utilisateur | Ajouter une unité à un aliment personnalisé | UC13 | RG20, RG49 | 201 | 400, 401, 403, 404, 409 |
| DELETE | `/appios/foods/{foodID}/portions/{foodPortionID}` | Utilisateur | Supprimer une unité d'un aliment personnalisé | UC13 | RG20 | 204 | 400, 401, 403, 404, 409 |

### Repas

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/meals` | Utilisateur | Lister ses repas d'un jour ou d'une plage | UC18 | RG23, RG26 | 200 | 400, 401, 403 |
| POST | `/appios/meals` | Utilisateur | Ajouter un repas, à la main, depuis un favori ou depuis une photo | UC14, UC15, UC16 | RG19, RG20, RG23, RG24, RG25, RG27, RG28 | 201 | 400, 401, 403, 404, 409 |
| GET | `/appios/meals/{mealID}` | Utilisateur | Lire un repas | UC18, UC19 | RG09, RG26 | 200 | 400, 401, 403, 404 |
| PUT | `/appios/meals/{mealID}` | Utilisateur | Modifier un repas | UC19 | RG22, RG23, RG24, RG25, RG26 | 200 | 400, 401, 403, 404, 409 |
| DELETE | `/appios/meals/{mealID}` | Utilisateur | Supprimer un repas | UC19 | RG09 | 204 | 400, 401, 403, 404 |

### Favoris

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/favorite-meals` | Utilisateur | Lister ses repas favoris | UC15, UC17 | RG27 | 200 | 401, 403 |
| POST | `/appios/favorite-meals` | Utilisateur | Enregistrer un repas favori | UC17 | RG20, RG27 | 201 | 400, 401, 403, 404, 409 |
| GET | `/appios/favorite-meals/{favoriteMealID}` | Utilisateur | Lire un favori pour préremplir un repas | UC15 | RG27 | 200 | 400, 401, 403, 404 |
| PATCH | `/appios/favorite-meals/{favoriteMealID}` | Utilisateur | Renommer un favori ou remplacer ses lignes | UC17 | RG27 | 200 | 400, 401, 403, 404, 409 |
| DELETE | `/appios/favorite-meals/{favoriteMealID}` | Utilisateur | Supprimer un favori | UC17 | RG09, RG27 | 204 | 400, 401, 403, 404 |

### Activités

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/activities` | Utilisateur | Lister, filtrer et trier ses séances | UC10 | RG31, RG32, RG33, RG38 | 200 | 400, 401, 403 |
| POST | `/appios/activities` | Utilisateur | Ajouter une séance | UC08, UC09 | RG29, RG30, RG31, RG33, RG38 | 201 | 400, 401, 403, 404, 409 |
| POST | `/appios/activities/estimate` | Utilisateur | Estimer les calories d'une séance avant de l'enregistrer | UC09 | RG10, RG12, RG31 | 200 | 400, 401, 403, 404 |
| POST | `/appios/activities/import` | Utilisateur | Importer un lot de séances depuis Santé | UC26 | RG10, RG30, RG31, RG33, RG38, RG40 | 200 | 400, 401, 403, 409 |
| GET | `/appios/activities/{activityID}` | Utilisateur | Lire une séance | UC10, UC11 | RG09 | 200 | 400, 401, 403, 404 |
| PATCH | `/appios/activities/{activityID}` | Utilisateur | Modifier une séance | UC11 | RG29, RG30, RG31, RG33, RG38 | 200 | 400, 401, 403, 404, 409 |
| DELETE | `/appios/activities/{activityID}` | Utilisateur | Supprimer une séance | UC11 | RG33 | 204 | 400, 401, 403, 404 |

### Pesées

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/weigh-ins` | Utilisateur | Lister ses pesées pour la courbe | UC22, UC29 | RG39 | 200 | 400, 401, 403, 409 |
| POST | `/appios/weigh-ins` | Utilisateur | Enregistrer une pesée | UC22 | RG10, RG13, RG33, RG34, RG39, RG52 | 200, 201 | 400, 401, 403, 409 |
| POST | `/appios/weigh-ins/import` | Utilisateur | Importer un lot de pesées depuis Santé | UC26 | RG10, RG13, RG33, RG34, RG39, RG52 | 200 | 400, 401, 403, 409 |
| DELETE | `/appios/weigh-ins/{weighInID}` | Utilisateur | Supprimer une pesée | UC22 | RG09, RG33, RG34, RG39, RG52 | 204 | 400, 401, 403, 404 |

### Énergie active

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/active-energy-days` | Utilisateur | Lire l'énergie active importée de Santé | UC26 | RG40 | 200 | 400, 401, 403, 409 |
| POST | `/appios/active-energy-days/import` | Utilisateur | Importer un lot d'énergie active depuis Santé | UC26 | RG10, RG33, RG40 | 200 | 400, 401, 403, 409 |

### Objectifs

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/calorie-goal` | Utilisateur | Lire son objectif calorique, avec la cible effective | UC20 | RG12, RG34, RG35, RG36 | 200 | 401, 403, 404 |
| PUT | `/appios/calorie-goal` | Utilisateur | Définir ou modifier le mode, la valeur saisie et les macros | UC20 | RG34, RG35, RG36, RG52 | 200 | 400, 401, 403, 409 |
| GET | `/appios/calorie-goal/history` | Utilisateur | Lire l'historique des versions de l'objectif calorique | UC20, UC24 | RG11, RG52 | 200 | 400, 401, 403 |
| GET | `/appios/activity-goals` | Utilisateur | Lister ses objectifs d'activité | UC21 | RG37 | 200 | 401, 403 |
| POST | `/appios/activity-goals` | Utilisateur | Créer un objectif d'activité | UC21 | RG37 | 201 | 400, 401, 403, 404, 409 |
| PATCH | `/appios/activity-goals/{activityGoalID}` | Utilisateur | Modifier la valeur d'un objectif d'activité (nouvelle version) | UC21 | RG37 | 200 | 400, 401, 403, 404, 409 |
| DELETE | `/appios/activity-goals/{activityGoalID}` | Utilisateur | Supprimer un objectif d'activité | UC21 | RG37 | 204 | 400, 401, 403, 404, 409 |

### Tableau de bord

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/dashboard` | Utilisateur | Lire le tableau de bord d'un jour | UC23 | RG26, RG31, RG37, RG38, RG40, RG41, RG49, RG52 | 200 | 400, 401, 403 |

### Historique

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/history` | Utilisateur | Lire les résumés par jour, par semaine ou par mois | UC24 | RG26, RG31, RG38, RG40, RG52 | 200 | 400, 401, 403 |
| GET | `/appios/history/days/{date}` | Utilisateur | Lire le détail d'un jour | UC24 | RG26, RG40, RG52 | 200 | 400, 401, 403 |

### Rappels

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/reminder-settings` | Utilisateur | Lire ses réglages de rappels et de messages | UC25 | RG42 | 200 | 401, 403 |
| PATCH | `/appios/reminder-settings/{kind}` | Utilisateur | Modifier un réglage de rappel | UC25 | RG42 | 200 | 400, 401, 403 |

### Export

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/appios/export` | Utilisateur | Exporter une période en CSV (bonus) | UC27 | RG31, RG33, RG38 | 200 | 400, 401, 403 |

### Back-office utilisateurs

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/backoffice/users` | Admin | Lister, rechercher et filtrer les utilisateurs | UC31 | RG44, RG45, RG53 | 200 | 400, 401, 403 |
| GET | `/backoffice/users/{userID}` | Admin | Lire la fiche d'un utilisateur | UC31 | RG45 | 200 | 400, 401, 403, 404 |
| DELETE | `/backoffice/users/{userID}` | Admin | Supprimer un utilisateur | UC33 | RG07, RG43, RG48 | 204 | 400, 401, 403, 404, 409 |
| PATCH | `/backoffice/users/{userID}/status` | Admin | Bloquer, suspendre ou réactiver un utilisateur | UC32 | RG06, RG07, RG48 | 200 | 400, 401, 403, 404, 409 |

### Back-office aliments

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/backoffice/foods` | Admin | Lister les aliments de base | UC34 | RG19, RG46 | 200 | 400, 401, 403 |
| POST | `/backoffice/foods` | Admin | Ajouter un aliment de base | UC34 | RG18, RG19, RG20, RG21, RG46, RG48, RG49 | 201 | 400, 401, 403, 404 |
| GET | `/backoffice/foods/{foodID}` | Admin | Lire un aliment de base | UC34 | RG19 | 200 | 400, 401, 403, 404 |
| PATCH | `/backoffice/foods/{foodID}` | Admin | Modifier ou désarchiver un aliment de base | UC34 | RG18, RG21, RG25, RG46, RG48 | 200 | 400, 401, 403, 404 |
| DELETE | `/backoffice/foods/{foodID}` | Admin | Supprimer ou archiver un aliment de base | UC34 | RG46, RG48 | 200 | 400, 401, 403, 404 |
| POST | `/backoffice/foods/{foodID}/portions` | Admin | Ajouter une unité à un aliment de base | UC34 | RG20, RG48, RG49 | 201 | 400, 401, 403, 404 |
| DELETE | `/backoffice/foods/{foodID}/portions/{foodPortionID}` | Admin | Supprimer une unité d'un aliment de base | UC34 | RG20, RG48 | 204 | 400, 401, 403, 404, 409 |

### Back-office types d'activité

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/backoffice/activity-types` | Admin | Lister les types d'activité | UC35 | RG29, RG46 | 200 | 400, 401, 403 |
| POST | `/backoffice/activity-types` | Admin | Créer un type d'activité du Compendium | UC35 | RG29, RG48 | 201 | 400, 401, 403, 404, 409 |
| GET | `/backoffice/activity-types/{activityTypeID}` | Admin | Lire un type d'activité | UC35 | RG29 | 200 | 400, 401, 403, 404 |
| PATCH | `/backoffice/activity-types/{activityTypeID}` | Admin | Modifier ou désarchiver un type d'activité | UC35 | RG29, RG46, RG48 | 200 | 400, 401, 403, 404 |
| DELETE | `/backoffice/activity-types/{activityTypeID}` | Admin | Supprimer ou archiver un type d'activité | UC35 | RG46, RG48 | 200 | 400, 401, 403, 404 |

### Back-office statistiques

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/backoffice/stats` | Admin | Lire le tableau de bord global | UC36 | RG38, RG45, RG47, RG52, RG53 | 200 | 400, 401, 403 |

### Back-office journal

| Méthode | Chemin | Rôle | Objet | UC | RG | Succès | Erreurs |
|---|---|---|---|---|---|---|---|
| GET | `/backoffice/admin-actions` | Admin | Lire le journal des actions d'administration | UC32, UC33, UC34, UC35 | RG48 | 200 | 400, 401, 403 |

## 3. Correspondance entre routes et tables

Les 26 tables du MLD sont toutes servies par au moins une route.

| Routes | Tables lues | Tables écrites |
|---|---|---|
| `POST /auth/register` | `user` (unicité de l'email) | `user`, `reminder_setting` (4 réglages par défaut) |
| `POST /auth/login` | `user` | `user` (fuseau, blocage levé), `login_event` |
| `/appios/profile`, `password`, `time-zone` | `user`, `health_consent`, `calorie_goal` | `user` |
| `DELETE /appios/profile` | `user`, `admin_action` | `meal` puis `favorite_meal`, puis `user`, dont la cascade efface `meal_item`, `favorite_item`, `food`, `food_portion`, `food_allergen`, `activity`, `weigh_in`, `daily_active_energy`, `health_profile`, `health_profile_allergen`, `health_consent`, `calorie_goal`, `calorie_target_history`, `activity_goal`, `reminder_setting`, `login_event` (RG43, `04-mcd-mld-mpd.md` §4) |
| `/appios/health-consents` | `health_consent` | `health_consent`, `health_profile` (créé vide au consentement) |
| `PATCH /appios/health-consents/withdraw` | `health_consent`, `calorie_goal`, `calorie_target_history` | `health_consent`, `health_profile` et `health_profile_allergen` (effacés), `weigh_in`, `activity` (séances importées effacées, kcal estimées vidées), `daily_active_energy`, `calorie_goal`, `calorie_target_history` (RG11) |
| `/appios/health-profile` | `health_profile`, `health_profile_allergen`, `allergen`, `weigh_in` | `health_profile`, `health_profile_allergen`, `calorie_goal`, `calorie_target_history` |
| Référentiels `/appios/allergens`, `food-groups`, `activity-categories`, `activity-types`, `muscle-groups` | `allergen`, `food_group`, `activity_category`, `activity_type`, `activity_type_muscle_group`, `muscle_group` | — |
| `/appios/foods…` | `food`, `food_group`, `food_allergen`, `food_portion`, `allergen`, `health_profile`, `health_profile_allergen` (compatibilité), `meal_item`, `favorite_item` (utilisation) | `food`, `food_allergen`, `food_portion` |
| `/appios/meals…` | `meal`, `meal_item`, `food`, `food_portion` | `meal`, `meal_item` |
| `/appios/favorite-meals…` | `favorite_meal`, `favorite_item`, `food`, `food_portion` | `favorite_meal`, `favorite_item` |
| `/appios/activities…` | `activity`, `activity_type`, `activity_category`, `weigh_in`, `health_consent`, `health_profile` (âge), `user` (fuseau pour `performed_on`) | `activity` (avec `performed_on` calculé, ou `is_ignored` pour une séance importée supprimée) |
| `/appios/weigh-ins…` | `weigh_in` (hors pesées ignorées), `health_consent` | `weigh_in` (suppression, ou `is_ignored` pour une pesée importée), `calorie_goal` (macros non personnalisées), `calorie_target_history` |
| `/appios/active-energy-days…` | `daily_active_energy`, `health_consent` | `daily_active_energy` |
| `/appios/calorie-goal…` | `calorie_goal`, `calorie_target_history`, `health_profile`, `weigh_in`, `health_consent` | `calorie_goal`, `calorie_target_history` |
| `/appios/activity-goals…` | `activity_goal`, `activity_category` | `activity_goal` |
| `GET /appios/dashboard` | `meal`, `meal_item`, `calorie_target_history`, `activity`, `activity_type`, `daily_active_energy`, `activity_goal`, `weigh_in` | — |
| `/appios/history…` | les mêmes, plus `food`, `food_portion` (détail des repas) | — |
| `/appios/reminder-settings…` | `reminder_setting` | `reminder_setting` |
| `GET /appios/export` | `meal`, `meal_item`, `food`, `food_portion`, `activity`, `activity_type`, `activity_category` | — |
| `/backoffice/users…` | `user`, `activity`, `calorie_goal`, `activity_goal`, `activity_category`, `login_event`, `meal`, `favorite_meal`, `food` | `user` (statut), suppression comme RG43, `admin_action` |
| `/backoffice/foods…` | `food`, `food_group`, `food_allergen`, `food_portion`, `meal_item`, `favorite_item` | `food`, `food_allergen`, `food_portion`, `admin_action` |
| `/backoffice/activity-types…` | `activity_type`, `activity_category`, `activity_type_muscle_group`, `muscle_group`, `activity` | `activity_type`, `activity_type_muscle_group`, `admin_action` |
| `GET /backoffice/stats` | `user`, `login_event`, `meal`, `meal_item`, `activity`, `activity_type`, `activity_category`, `calorie_goal`, `calorie_target_history`, `activity_goal`, `health_profile`, `health_consent` | — |
| `GET /backoffice/admin-actions` | `admin_action`, `user` (nom de l'administrateur) | — |

## 4. Requêtes SQL écrites à la main

Le reste passe par Fluent. Ces requêtes sont des agrégats que Fluent exprime mal ; elles sont écrites en SQL brut (`SQLDatabase.raw`) avec des paramètres liés, jamais par concaténation. Les colonnes de tri viennent d'une liste blanche.

**Fuseau horaire** : toutes les dates de regroupement sont des jours locaux déjà stockés : `meal.eaten_on`, `activity.performed_on`, `weigh_in.weighed_on` et `daily_active_energy.day`. L'API calcule `performed_on` en Swift, à l'enregistrement, depuis `performed_at` et `user.time_zone`, comme `eaten_on`. Le SQL groupe et filtre donc sur ces colonnes, sans `CONVERT_TZ` ni tables de fuseaux dans MariaDB (index `activity(id_user, performed_on)`).

### App iOS

| Route | Requête |
|---|---|
| `GET /appios/history` | Somme des lignes de repas par période (jour, semaine ISO avec `eaten_on - INTERVAL WEEKDAY(eaten_on) DAY`, ou mois), jointe à la somme des kcal, séances et minutes des activités non ignorées groupées par `performed_on` sur la même période, et à la cible de chaque jour prise par sous-requête dans `calorie_target_history` (dernière version dont `effective_from` ≤ jour, RG52) |
| `GET /appios/dashboard` | Progression des objectifs d'activité du jour : pour chaque objectif valable ce jour-là, somme des séances, minutes ou kcal des activités dont `performed_on` tombe dans sa période, pour sa catégorie (toutes si vide), en excluant les séances ignorées et, pour les kcal, les non renseignées (RG40) |
| `GET /appios/dashboard` | Activité la plus pratiquée de l'utilisateur, pour la suggestion de RG41 : `GROUP BY id_activity_type ORDER BY COUNT(*) DESC LIMIT 1`, et la marche rapide (17200) si le résultat est vide |
| `GET /appios/foods` | Recherche d'aliments compatibles : nom en `LIKE` avec la collation insensible à la casse et aux accents, tri `CASE WHEN nom LIKE 'texte%'`, et exclusion des incompatibles par `NOT EXISTS` sur `food_allergen` joint à `health_profile_allergen`, plus les conditions sur les booléens de régime (`contains_meat`, `contains_animal_product`, `contains_pork`) |
| `GET /appios/export` | `UNION ALL` des lignes de repas (jointes à l'aliment et à l'unité) et des séances (jointes au type et à la catégorie) de la plage, triées par date |

### Back-office

| Route | Requête |
|---|---|
| `GET /backoffice/users` | Liste des comptes jointe au nombre d'activités non ignorées et aux connexions des 30 derniers jours (sous-requêtes groupées par `id_user`), filtre « objectif atteint » par `EXISTS` sur les objectifs d'activité de la dernière semaine ISO complète, tri sur une colonne de la liste blanche, `LIMIT`/`OFFSET`, et `COUNT(*)` pour `metadata.total` |
| `GET /backoffice/stats` | Inscriptions par période : `COUNT(*)` de `user` groupé par jour, semaine ou mois de `created_at` |
| `GET /backoffice/stats` | Connexions par période : `COUNT(*)` et `COUNT(DISTINCT id_user)` de `login_event`, qui donnent la fréquence des connexions et les utilisateurs actifs (RG53) |
| `GET /backoffice/stats` | Repas par type et séances par catégorie sur la plage (`eaten_on` et `performed_on`), avec la somme des minutes, groupés par `meal_type` et par catégorie |
| `GET /backoffice/stats` | Modes de l'objectif calorique : `COUNT(*)` de `calorie_goal` groupé par `mode` |
| `GET /backoffice/stats` | Objectifs d'activité atteints : pour chaque objectif et chaque période close (jour ou semaine) de la plage où il était valable, comparaison de la somme réalisée à `target_value` |
| `GET /backoffice/stats` | Jours où la cible calorique n'est pas dépassée : somme des kcal par utilisateur et par jour, jointe à la version de `calorie_target_history` qui s'appliquait ce jour-là (RG52) |
| `GET /backoffice/stats` | Répartitions par tranche d'âge (année en cours moins `birth_year`, tranches `18-29`, `30-44` et `45+`), par sexe et par orientation, comptées sur `health_profile` des comptes au consentement actif, avec le masquage des groupes de moins de 5 appliqué ensuite par l'API (RG47) |

## 5. Choix et interprétations

| Sujet | Choix | Raison |
|---|---|---|
| Noms des clés étrangères | `foodID` plutôt que `idFood` | Convention de LineUp (`categoryID`), plus lisible en Swift |
| Mot de passe actuel incorrect | 400, et non 401 | L'app traite 401 comme une session expirée et renverrait vers la connexion |
| Identifiant inconnu dans le corps | 404 | Comme `noWorkshop` dans LineUp |
| Aliment de base modifié depuis l'app | 403 | Il est visible, donc pas « absent » ; seule l'administration le modifie |
| `DELETE` d'un aliment ou d'un type | Supprime ou archive selon l'usage, et le dit | Applique RG22 et RG46 en un seul appel |
| Repas depuis un favori | L'app lit le favori, préremplit, puis crée le repas avec `origin = favorite` | US14 veut un repas modifiable avant l'enregistrement. Un aliment archivé du favori est refusé (409) et signalé par `foodIsArchived` |
| Modification d'un repas | `PUT` de la liste complète ; une ligne avec `id` et quantité inchangée garde ses valeurs figées | RG25 distingue les lignes inchangées des lignes modifiées |
| Estimation sans consentement ni poids | 200 avec `kcal: null` et la raison | Même comportement que l'enregistrement, qui stocke `unknown` (RG31) |
| Imports de Santé | Un élément invalide est compté dans `rejected` et ne fait pas échouer le lot | Une séance de 11 h ne doit pas bloquer tout l'historique |
| Source des imports | L'app exclut aussi les échantillons dont la source est ZakFit (`HKSource.default()`), en plus du contrôle par `healthUUID` | Une séance écrite dans Santé dont le `healthUUID` s'est perdu ne revient pas en double (RG33, RG40) |
| Ordre des contrôles à la connexion | Mot de passe d'abord, statut ensuite | Un 403 ne doit pas révéler qu'un email existe (RG04) |
| Repas contenant un aliment archivé depuis | Une ligne existante reste modifiable, recalculée avec les valeurs actuelles ; seule une nouvelle ligne est refusée | Sinon un repas passé ne se corrige plus (US16, RG22) |
| Schémas de modification | Aucune valeur par défaut dans `FoodValues`, partagé par la création et la modification | Un champ absent d'un `PATCH` reste inchangé |
| Invariants des entrées | `oneOf` pour une ligne (grammes ou unités) et `if`/`then` pour l'objectif calorique (`manualKcal` selon le mode, grammes si `macrosCustom`) | L'état impossible est refusé par le schéma, pas seulement par le texte |
| Pesée du jour existante | 409, sauf `replaceExisting: true` ; une pesée importée ignorée ne compte pas | RG39 demande une confirmation avant de remplacer |
| Import d'une pesée sur un jour ignoré | Écartée (`skippedIgnored`) | La pesée supprimée par l'utilisateur ne doit pas revenir (RG39) |
| Objectif d'activité modifié le jour de sa création | Modifié sur place | Clore la ligne donnerait `valid_to` avant `valid_from`, refusé par la base |
| Objectif « par séance » | Progression = meilleure séance du jour | RG37 ne précise pas l'agrégat |
| Suggestion pour un objectif en séances | Une séance de la durée moyenne de l'activité suggérée, 30 minutes sans historique | RG41 ne donne la formule que pour les kcal et les minutes |
| Filtre admin « objectif atteint » | Au moins un objectif d'activité atteint sur la dernière semaine ISO complète | Le filtre sur l'objectif calorique dériverait de données de santé (RG45) |
| Statistique « objectif calorique atteint » | Jour saisi dont le consommé ne dépasse pas la cible du jour | Cohérent avec l'alerte « objectif dépassé » de RG41 |
| Tranches d'âge (RG47) | Trois tranches : `18-29`, `30-44`, `45+` (45 ans ou plus), toujours renvoyées dans cet ordre | Décision de l'orchestrateur, identique au générateur de démo ; des tranches plus fines seraient souvent masquées avec peu de comptes |
| Masquage RG47 | Groupe vide (0) affiché ; groupe de 1 à 4 masqué ; si un seul l'est, le plus petit des autres groupes non vides aussi ; total sous 5 : répartition masquée | Un 0 ne désigne personne ; sans le masquage secondaire, le groupe masqué se déduit par soustraction du total |
| Utilisateur actif (admin) | Au moins une connexion dans la plage | Seule mesure prévue par RG53 |
| Dates d'inscription (filtres admin) | Jours UTC | L'administrateur n'a pas de fuseau dans le modèle |
| Alcool | Mention `contains_alcohol`, pas une incompatibilité | Aucune règle ne lie l'alcool à un régime (RG21) |
| Réglages de rappel | Créés à l'inscription, activés à 18:00 | Un réglage par type et par utilisateur (RG42), toujours présent |
| Référentiels pour le back-office | Lus sous `/appios` | Évite de dupliquer des routes en lecture seule |

## 6. Table de correspondance des séances de Santé (proposition)

RG33 demande une table fixe dans l'API, qui associe un type de séance de Santé (`HKWorkoutActivityType`) à un code du Compendium du référentiel. **Proposition, à valider par Slimane** :

| Santé | Code | Type ZakFit |
|---|---|---|
| `walking` | 17190 | Marche modérée |
| `hiking` | 17080 | Randonnée |
| `running` | 12050 | Course modérée |
| `cycling` | 01010 | Vélo loisir |
| `swimming` | 18240 | Natation |
| `rowing` | 02071 | Rameur |
| `elliptical` | 02048 | Elliptique |
| `highIntensityIntervalTraining` | 02214 | HIIT |
| `jumpRope` | 15551 | Corde à sauter |
| `traditionalStrengthTraining`, `functionalStrengthTraining` | 02054 | Musculation |
| `crossTraining` | 02035 | Circuit training |
| `yoga` | 02175 | Yoga |
| `pilates` | 02105 | Pilates |
| `soccer` | 15610 | Football |
| `basketball` | 15055 | Basket |
| `tennis` | 15675 | Tennis |
| `socialDance`, `cardioDance` | 03025 | Danse |
| `boxing` | 15110 | Boxe (sac) |

Tout autre type est écarté et compté dans `skippedUnmapped`.

## 7. Points à valider et limites

- **Table de Santé** : la correspondance de la section 6 est une proposition, à valider par Slimane. Elle ramène la course, le vélo et la marche à une seule intensité, et écarte des types fréquents (`coreTraining`, `flexibility`, `stairClimbing`, `mixedCardio`) ; choisir l'intensité d'après la vitesse moyenne reste possible.
- **Statistique « objectif calorique atteint »** : la définition actuelle (consommé qui ne dépasse pas la cible) compte comme réussis un jour très partiel ou un jour sous la cible en prise de masse. Un intervalle, par exemple de 90 à 110 % de la cible, serait plus juste. Décision à prendre, puis à reporter dans le générateur de démo.
- **Limite de RG47** : les répartitions sont calculées sur les comptes au consentement actif, à l'instant de la requête. Avec peu de comptes, un administrateur qui compare deux appels, avant et après le consentement d'une personne qu'il voit dans la liste, peut déduire sa tranche d'âge, son sexe et son orientation (attaque par différence). Le masquage ne l'empêche pas. Parade possible : calculer les répartitions sur un instantané hebdomadaire.
