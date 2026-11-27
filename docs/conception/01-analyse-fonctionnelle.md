# ZakFit — analyse fonctionnelle

Version 1 du 23/11/2026. Source : cahier des charges de ZakFit (les numéros de page renvoient au cahier), complété par les décisions de cadrage du projet.

**Priorités :**
- **I** (indispensable) : exigé par le cahier ou nécessaire au rendu.
- **M** (important) : optionnel dans le cahier, mais retenu.
- **B** (bonus) : réalisé seulement si le temps le permet.

## 1. Acteurs

| Acteur | Type | Rôle |
|---|---|---|
| Visiteur | Principal, humain | Personne sans compte, ou non connectée. Elle peut s'inscrire et se connecter |
| Utilisateur | Principal, humain | Personne connectée à l'app iOS. Elle suit ses repas, ses activités, ses pesées et ses objectifs |
| Administrateur | Principal, humain | Gère les utilisateurs, les aliments et les types d'activité depuis le back-office web, et consulte les statistiques globales |
| Santé (Apple HealthKit) | Secondaire, système | Fournit les séances d'entraînement, l'énergie active et le poids. Reçoit les séances et les pesées saisies dans ZakFit |
| Modèle d'Apple (Foundation Models) | Secondaire, système sur l'appareil | Reconnaît les aliments d'une photo de plat et estime leur poids (bonus) |

Le Visiteur devient Utilisateur en se connectant. L'Administrateur est un compte distinct, créé par le script de données et non par l'inscription publique.

## 2. Cas d'utilisation

Le diagramme `diagrammes/cas-utilisation.drawio` suit la méthode vue en cours : un seul diagramme, des cas d'utilisation larges et sans code, un cas « S'authentifier » inclus par tous ceux qui demandent d'être connecté. Les tableaux ci-dessous détaillent ces cas en cas plus fins, numérotés pour la traçabilité avec les user stories et les règles.

| Cas du diagramme | Cas détaillés |
|---|---|
| S'inscrire | UC01 |
| S'authentifier | UC02 (connexion), UC06 (déconnexion), UC30 (connexion au back-office) |
| Compléter le questionnaire de démarrage | UC03 |
| Donner son consentement santé | UC04 |
| Gérer son profil | UC05 |
| Retirer son consentement santé | UC28 |
| Supprimer son compte | UC07 |
| Gérer ses activités | UC08, UC10, UC11 |
| Estimer les calories d'une activité | UC09 |
| Synchroniser avec Santé | UC26 |
| Gérer ses repas | UC14, UC18, UC19 |
| Rechercher un aliment | UC12 |
| Créer un aliment personnalisé | UC13 |
| Gérer ses repas favoris | UC15, UC17 |
| Analyser la photo d'un plat | UC16 |
| Gérer ses objectifs | UC20, UC21 |
| Suivre son poids | UC22, UC29 |
| Consulter le tableau de bord | UC23 |
| Consulter l'historique | UC24 |
| Exporter l'historique en CSV | UC27 |
| Régler ses rappels et messages | UC25 |
| Gérer les utilisateurs | UC31, UC32, UC33 |
| Gérer les aliments de base | UC34 |
| Gérer les types d'activité | UC35 |
| Consulter les statistiques globales | UC36 |

### App iOS

| Id | Cas d'utilisation | Acteurs | Relations | Priorité | Cahier |
|---|---|---|---|---|---|
| UC01 | S'inscrire | Visiteur | — | I | p. 5 |
| UC02 | Se connecter | Visiteur | — | I | p. 6 |
| UC03 | Compléter le questionnaire de démarrage | Utilisateur | inclut UC04 | I | p. 6, 15 |
| UC04 | Donner son consentement santé | Utilisateur | inclus par UC03 | I | RGPD art. 9 (décision 03-reponses, Santé 4) |
| UC28 | Retirer son consentement santé | Utilisateur | — | I | RGPD art. 7 et 9 (décision 03-reponses, Santé 4) |
| UC05 | Gérer son profil (identité, email, mot de passe, mensurations, orientation, régimes, allergènes) | Utilisateur | — | I | p. 6-7 |
| UC06 | Se déconnecter | Utilisateur | — | I | p. 7 |
| UC07 | Supprimer son compte | Utilisateur | — | I | RGPD, p. 21 |
| UC08 | Ajouter une activité | Utilisateur | étendu par UC09 | I | p. 8 |
| UC09 | Estimer les calories d'une activité | Utilisateur (via UC08) | étend UC08, si les calories sont vides et le poids connu | M | p. 8 |
| UC10 | Consulter, filtrer et trier ses activités | Utilisateur | — | I | p. 9 |
| UC11 | Modifier ou supprimer une activité | Utilisateur | — | I | — |
| UC12 | Rechercher un aliment | Utilisateur | — | I | p. 12 |
| UC13 | Créer un aliment personnalisé | Utilisateur (via UC12) | étend UC12, si l'aliment est introuvable | I | p. 12 |
| UC14 | Ajouter un repas | Utilisateur | inclut UC12 (cas nominal : chaque ligne vient d'une recherche) ; étendu par UC15 et UC16 | I | p. 12-13 |
| UC15 | Partir d'un repas favori | Utilisateur (via UC14) | étend UC14, si l'utilisateur choisit un favori | M | décision du 23/11 |
| UC16 | Analyser la photo d'un plat | Utilisateur (via UC14), Modèle d'Apple | étend UC14, sur iOS 27 et sur un appareil compatible | B | décision du 23/11 |
| UC17 | Gérer ses repas favoris | Utilisateur | — | M | décision du 23/11 |
| UC18 | Consulter les repas d'une journée et les filtrer | Utilisateur | — | I | p. 13 |
| UC19 | Modifier ou supprimer un repas | Utilisateur | — | I | — |
| UC20 | Définir son objectif calorique et ses macros | Utilisateur | — | I | p. 14-16 |
| UC21 | Définir ses objectifs d'activité | Utilisateur | — | I | p. 16 |
| UC22 | Enregistrer une pesée | Utilisateur | — | I | p. 6 (poids du profil) |
| UC29 | Voir la courbe des pesées | Utilisateur | — | M | p. 16 |
| UC23 | Consulter le tableau de bord (totaux, objectifs, graphiques, alertes) | Utilisateur | — | I | p. 14, 10, 19 |
| UC24 | Consulter l'historique (semaine, mois, date, plage, détail d'un jour) | Utilisateur | — | I | p. 18 |
| UC25 | Recevoir et régler ses rappels et messages | Utilisateur | — | I | p. 17 (notifications internes, non optionnelles) |
| UC26 | Synchroniser avec Santé | Utilisateur, Santé | — | M | décision du 23/11 |
| UC27 | Exporter son historique en CSV | Utilisateur | — | B | p. 20 |

### Back-office web

| Id | Cas d'utilisation | Acteurs | Priorité | Cahier |
|---|---|---|---|---|
| UC30 | Se connecter au back-office | Administrateur | B | p. 21 |
| UC31 | Consulter, rechercher et filtrer les utilisateurs | Administrateur | B | p. 21 |
| UC32 | Bloquer, suspendre ou réactiver un utilisateur | Administrateur | B | p. 21 |
| UC33 | Supprimer un utilisateur | Administrateur | B | p. 21 |
| UC34 | Gérer les aliments de la base | Administrateur | B | p. 22 |
| UC35 | Gérer les types d'activité | Administrateur | B | p. 22 |
| UC36 | Consulter le tableau de bord global | Administrateur | B | p. 23 |

Les routes d'administration de l'API sont prévues dès la semaine 2. La priorité B ne concerne que l'interface web.

## 3. User stories

Format : « En tant que…, je veux…, afin de… », suivi des critères d'acceptation. Chaque critère est vérifiable par un test.

### Compte

**US01 — Inscription (UC01, I).** En tant que visiteur, je veux créer un compte avec mon nom, mon prénom, mon email et un mot de passe, afin d'accéder à l'app.
- La case « J'ai 18 ans ou plus » est obligatoire (RG12).
- Un email au mauvais format, un mot de passe hors règles (RG02) ou une confirmation différente bloquent l'envoi, avec un message sous le champ concerné.
- Un email déjà utilisé, sans tenir compte de la casse, renvoie une erreur 409 et le message « Cet email est déjà utilisé ».
- En cas de succès, le compte est créé avec le statut actif et le rôle utilisateur, et l'écran de connexion s'affiche.
- Le mot de passe n'est jamais stocké ni renvoyé en clair.

**US02 — Connexion (UC02, I).** En tant que visiteur, je veux me connecter avec mon email et mon mot de passe, afin de retrouver mes données sur n'importe quel appareil.
- Avant l'envoi, l'app vérifie que l'email a un format valide et que le mot de passe n'est pas vide (p. 6).
- Avec des identifiants valides, l'API renvoie un jeton valable 7 jours, que l'app range dans le Trousseau.
- Avec des identifiants invalides, le message est le même que l'email existe ou non (RG04).
- Un compte bloqué ou suspendu reçoit un refus explicite (RG06).
- Au lancement suivant, un jeton encore valide ouvre directement l'app ; un jeton expiré ramène à la connexion.

**US03 — Questionnaire de démarrage (UC03, UC04, I).** En tant que nouvel utilisateur, je veux indiquer mon profil en quelques écrans, afin d'obtenir un objectif calorique adapté sans réglage manuel.
- Le premier écran explique pourquoi les données de santé sont demandées, rappelle que ZakFit ne remplace pas un avis médical (RG50), puis recueille le consentement (RG10).
- Avec le consentement, on saisit l'année de naissance, le sexe pour le calcul, la taille, le poids, le niveau d'activité, l'orientation, les régimes et les allergènes, puis on voit l'objectif calculé.
- Sans le consentement, on passe ces étapes et on saisit soi-même l'objectif calorique.
- On peut quitter et reprendre le questionnaire, et le terminer plus tard depuis le profil.

**US04 — Profil (UC05, I).** En tant qu'utilisateur, je veux modifier mes informations, afin que mes calculs restent justes.
- Changer l'email vérifie qu'il est unique (RG01).
- Changer le mot de passe demande l'ancien et respecte RG02.
- Changer la taille, l'année de naissance, le sexe, le niveau d'activité ou l'orientation recalcule l'objectif s'il est en mode calculé (RG34).
- Le poids affiché est celui de la dernière pesée (RG39).

**US05 — Consentement (UC28, I).** En tant qu'utilisateur, je veux pouvoir retirer mon consentement santé, afin de garder la maîtrise de mes données.
- Le retrait demande une confirmation, qui liste les données effacées (RG11).
- Après le retrait, ces données ont disparu de la base et l'objectif calorique passe en mode saisi.

**US06 — Déconnexion (UC06, I).** En tant qu'utilisateur, je veux me déconnecter, afin de protéger mon compte sur un appareil partagé.
- Le jeton est effacé du Trousseau et l'écran de connexion s'affiche.

**US07 — Suppression du compte (UC07, I).** En tant qu'utilisateur, je veux supprimer mon compte, afin d'exercer mon droit à l'effacement.
- La suppression demande la saisie du mot de passe et une confirmation qui explique que c'est irréversible.
- Toutes les données du compte sont effacées (RG43). Ce qui est dans l'app Santé n'est pas touché.

### Activités

**US08 — Ajouter une activité (UC08, UC09, I/M).** En tant qu'utilisateur, je veux enregistrer une séance (type, date, durée, calories facultatives), afin de suivre mon activité.
- Le type se choisit dans la liste de référence, groupée par catégorie (RG29).
- Une durée hors de 1 à 600 minutes, ou une date dans le futur, est refusée côté client et côté API (RG30).
- Si les calories sont laissées vides et que le poids est connu, l'API les estime et l'app affiche « estimé » (RG31).
- La séance apparaît aussitôt dans l'historique et dans le tableau de bord.

**US09 — Historique des activités (UC10, I).** En tant qu'utilisateur, je veux filtrer et trier mes séances, afin de retrouver mes efforts.
- Filtres combinables : type ou catégorie, durée minimale, semaine, mois ou plage de dates.
- Tri par date (croissante ou décroissante), par type ou par durée.
- Le filtrage et le tri sont faits par l'API, qui ne renvoie que les résultats demandés (p. 9).

**US10 — Corriger une activité (UC11, I).** En tant qu'utilisateur, je veux modifier ou supprimer une séance, afin de corriger une erreur.
- La modification rejoue les contrôles de RG30 et RG31. Si la durée ou le type change et que les calories étaient estimées, elles sont estimées de nouveau.
- La suppression demande une confirmation. L'historique et le tableau de bord se mettent à jour.
- Une séance importée de Santé peut être supprimée dans ZakFit sans être effacée de Santé. Elle n'est pas réimportée (RG33).

### Aliments et repas

**US11 — Rechercher un aliment (UC12, I).** En tant qu'utilisateur, je veux trouver un aliment par son nom, afin de l'ajouter à un repas.
- La recherche ne tient compte ni de la casse ni des accents, et donne des résultats dès 2 caractères.
- Les aliments incompatibles avec mes régimes ou mes allergènes sont masqués par défaut. Une option les affiche avec un badge d'avertissement (RG21).
- Un avertissement permanent rappelle que les informations sur les allergènes et les régimes sont indicatives (RG51).
- Chaque résultat montre ses kcal et ses macros pour 100 g.

**US12 — Aliment personnalisé (UC13, I).** En tant qu'utilisateur, je veux créer un aliment absent de la base, afin de saisir mon vrai repas.
- Je saisis un nom, des valeurs pour 100 g, et éventuellement des unités et des étiquettes.
- Des valeurs incohérentes sont refusées, avec une explication (RG18).
- L'aliment n'est visible que par moi (RG19).

**US13 — Ajouter un repas (UC14, I).** En tant qu'utilisateur, je veux enregistrer un repas de plusieurs aliments, en grammes ou en unités, afin de connaître mes apports.
- Je choisis le type de repas, la date et les lignes ; les totaux se mettent à jour à chaque modification.
- L'API recalcule chaque ligne à partir de la base et ignore toute valeur nutritionnelle envoyée par le client (RG24).
- L'API répond avec le repas et ses totaux (p. 13), et le tableau de bord se met à jour.

**US14 — Repas favoris (UC15, UC17, M).** En tant qu'utilisateur, je veux enregistrer un repas habituel comme favori, afin de le saisir de nouveau en un geste.
- « Ajouter aux favoris » demande un nom.
- Partir d'un favori préremplit un repas modifiable, calculé avec les valeurs actuelles de la base.
- Je peux renommer ou supprimer un favori.

**US15 — Repas d'une journée (UC18, I).** En tant qu'utilisateur, je veux voir mes repas d'un jour, afin de contrôler mes apports.
- Les repas sont groupés par type, chacun avec ses aliments, ses quantités, ses kcal et ses macros, puis le total du jour.
- On peut filtrer par type de repas ou par seuil de calories, par exemple « plus de 500 kcal » (p. 13).

**US16 — Corriger un repas (UC19, I).** En tant qu'utilisateur, je veux modifier ou supprimer un repas, afin de corriger une erreur.
- La modification rejoue les contrôles de RG23 et RG24.
- Une ligne ajoutée ou dont la quantité change est recalculée avec les valeurs actuelles de l'aliment. Une ligne inchangée garde ses valeurs figées (RG25).
- La suppression demande une confirmation.
- Les totaux du repas et du jour, le tableau de bord et l'historique se mettent à jour.

**US17 — Photo d'un plat (UC16, B).** En tant qu'utilisateur, je veux photographier mon assiette, afin d'obtenir une proposition de repas à valider.
- Le bouton n'apparaît que sur iOS 27 et sur un appareil compatible.
- La proposition est une liste d'aliments de la base avec leurs grammes. Chaque ligne est modifiable ou supprimable, et l'utilisateur peut en ajouter.
- Rien n'est enregistré sans validation. La photo ne quitte pas l'appareil et n'est pas conservée (RG28).

### Objectifs, pesées, tableau de bord

**US18 — Objectif calorique (UC20, I).** En tant qu'utilisateur, je veux un objectif calorique calculé ou saisi, et des objectifs de macros, afin de savoir quoi viser.
- En mode calculé, l'objectif suit la formule de `02-formules.md` et se met à jour quand le profil change.
- En mode saisi, une valeur sous la dépense de repos estimée affiche un avertissement, et une valeur hors de 1 200 à 6 000 kcal est refusée (RG35).
- Les objectifs de macros sont en grammes, comme dans le cahier (p. 14). L'app les propose à partir de la répartition de l'ANSES, et l'utilisateur peut les modifier.

**US19 — Objectifs d'activité (UC21, I).** En tant qu'utilisateur, je veux me fixer des objectifs de séances, de minutes ou de calories brûlées, par jour ou par semaine, pour toutes les activités ou pour une catégorie, afin de rester régulier.
- Par exemple « 3 séances par semaine » ou « 30 minutes de cardio par jour ».
- Un même objectif (métrique, période, catégorie) ne peut pas exister deux fois (RG37).

**US20 — Pesées (UC22 en I, UC29 en M).** En tant qu'utilisateur, je veux enregistrer mon poids et voir sa courbe, afin de suivre mon évolution.
- Une seule pesée par jour : une nouvelle saisie remplace celle du jour, après confirmation (RG39).
- La courbe couvre 1 mois, 3 mois ou 1 an.

**US21 — Tableau de bord (UC23, I).** En tant qu'utilisateur, je veux voir ma journée d'un coup d'œil, afin de savoir où j'en suis.
- On y trouve :
  - les kcal consommées face à l'objectif, et les macros sous forme d'anneau ;
  - les kcal brûlées (RG40) ;
  - la progression des objectifs d'activité, les minutes de la semaine ;
  - les alertes et les recommandations (RG41).
- Toute saisie met à jour le tableau de bord sans le recharger à la main.
- Chaque chiffre affiché est égal à celui que donne la base (critère d'évaluation du brief).

**US22 — Historique (UC24, I).** En tant qu'utilisateur, je veux parcourir mes semaines et mes mois, et chercher une date ou une plage, afin d'analyser mes habitudes.
- On peut choisir une date au calendrier, ou une plage comme « du 1er au 7 novembre » (p. 18). Une plage dont la fin précède le début est refusée.
- La vue semaine montre le détail jour par jour.
- La vue mois montre les résumés : kcal consommées et brûlées, séances, repas.
- Le détail d'un jour donne ses repas et ses activités.

**US23 — Rappels et messages motivants (UC25, I).** En tant qu'utilisateur, je veux recevoir des rappels et des encouragements, à l'heure de mon choix, afin de rester régulier sans être dérangé.
- Les rappels sont des notifications locales, désactivables une par une, à 18 h par défaut (RG42).
- Un message de félicitation part quand un objectif de la semaine atteint 90 % ou 100 %, une seule fois par objectif et par semaine.
- Un message d'encouragement part le soir quand l'objectif du jour n'est pas atteint, au plus une fois par jour.
- Le contenu correspond aux données du moment : chaque saisie reprogramme les notifications concernées.

**US24 — Santé (UC26, M).** En tant qu'utilisateur, je veux relier ZakFit à l'app Santé, afin de ne pas tout saisir deux fois.
- L'autorisation est demandée type par type, avec une explication. L'écran précise que les données lues sont copiées sur le serveur ZakFit.
- Les séances, l'énergie active et le poids sont importés sans doublon.
- Les séances et les pesées saisies dans ZakFit sont écrites dans Santé.
- Rien n'est réimporté de ce que ZakFit a lui-même écrit (RG33).

**US25 — Export (UC27, B).** En tant qu'utilisateur, je veux exporter une période au format CSV, afin d'analyser mes données ailleurs.
- Je choisis une période et un contenu : repas, activités, ou les deux (p. 20).
- Le fichier est en UTF-8, avec une ligne par élément et des colonnes nommées.
- Il est partagé avec la feuille de partage d'iOS.
- L'export PDF de la p. 20 est hors périmètre (section 5).

### Administration (back-office)

**US30 — Accès (UC30, B).** En tant qu'administrateur, je veux me connecter au back-office, afin de gérer l'application. Un compte qui n'a pas le rôle administrateur est refusé, aussi bien par l'API que par l'interface.

**US31 — Utilisateurs (UC31 à UC33, B).** En tant qu'administrateur, je veux lister, filtrer, bloquer, suspendre, réactiver ou supprimer un utilisateur, afin de faire respecter les règles.
- Filtres : statut, date d'inscription, nombre d'activités, objectif atteint. Tri et pagination.
- Le blocage et la suspension coupent l'accès à la requête suivante, et les données sont conservées (p. 21).
- La suppression demande une confirmation et efface tout (RG43). Chaque action est journalisée (RG48).

**US32 — Référentiels (UC34, UC35, B).** En tant qu'administrateur, je veux gérer les aliments de base et les types d'activité, afin de garder des données justes.
- Les mêmes contrôles de vraisemblance que RG18 s'appliquent.
- Un élément déjà utilisé n'est pas supprimé mais archivé (RG46).

**US33 — Tableau de bord global (UC36, B).** En tant qu'administrateur, je veux des statistiques globales, afin de suivre l'usage de l'app.
- Inscrits, actifs, repas et séances par période et par type, objectifs atteints, répartitions.
- Une répartition qui porte sur moins de 5 personnes est masquée (RG47).

## 4. Règles de gestion

Chaque règle est vérifiée par l'API, ou par l'app quand elle est locale (RG08, RG42, RG49). L'app iOS et le back-office vérifient aussi les règles de l'API, quand c'est possible, avant l'envoi.

### Compte et accès

- **RG01** — L'email est obligatoire, au format valide, et unique sans tenir compte de la casse. Il est enregistré en minuscules.
- **RG02** — Le mot de passe compte au moins 8 caractères, dont au moins une lettre et un chiffre (« longueur et complexité », p. 5), et au plus 72 octets en UTF-8. Une lettre accentuée compte pour 2 octets. Le maximum tient à bcrypt, qui ignore tout ce qui dépasse 72 octets.
- **RG03** — Le mot de passe est haché avec bcrypt avant l'enregistrement, à la création comme à la modification. Aucune réponse de l'API ne contient de hash.
- **RG04** — Un échec de connexion donne toujours le même message, « Email ou mot de passe incorrect », pour ne pas révéler si un email existe. L'exemple « Mot de passe incorrect » de la p. 6 est volontairement écarté.
- **RG05** — Le jeton JWT contient l'identifiant de l'utilisateur et expire 7 jours après sa création. L'API le vérifie à chaque requête protégée, puis relit en base le statut et le rôle du compte. Un rôle retiré prend donc effet à la requête suivante. Un jeton absent, invalide ou expiré donne une erreur 401.
- **RG06** — Un compte a l'un de ces statuts : **actif**, **bloqué** (temporaire, avec une date de fin facultative) ou **suspendu** (sans date de fin).
  - Le statut est contrôlé à chaque requête : un compte bloqué ou suspendu reçoit une erreur 403, même avec un jeton valide.
  - Ses données sont conservées.
  - Seul un administrateur bloque, suspend ou réactive. Un blocage avec une date de fin se lève tout seul à cette date : il n'est plus appliqué dès la première requête qui suit.
- **RG07** — Un compte a l'un de ces rôles : **utilisateur** ou **administrateur**. L'inscription publique crée toujours un utilisateur. Un administrateur ne peut ni se bloquer, ni se suspendre, ni se supprimer lui-même.
- **RG08** — La déconnexion efface le jeton dans le Trousseau. Il n'y a pas de révocation côté serveur (p. 7).
- **RG09** — Un utilisateur n'accède qu'à ses propres données. Une ressource qui appartient à quelqu'un d'autre répond 404, comme si elle n'existait pas.

### Profil, santé et consentement

- **RG10** — Certaines données ne sont enregistrées qu'avec un **consentement santé** explicite :
  - **données de santé** (article 9 du RGPD) : taille, pesées, niveau d'activité, orientation, allergènes, régimes alimentaires, données importées de Santé ;
  - **donnée qui révèle une religion** (article 9 aussi) : la préférence halal ou casher ;
  - **données ordinaires placées sous le même consentement par prudence** : année de naissance et sexe. Elles ne servent qu'au calcul de l'objectif.

  Le consentement est enregistré avec sa date et la version du texte affiché. Ce texte annonce aussi l'usage de statistiques globales anonymes (RG47).

  Sans consentement, l'app fonctionne, mais l'objectif calorique se saisit à la main et l'estimation des calories d'une activité n'est pas proposée.
- **RG11** — Effet du retrait du consentement :

  | Donnée | Effet du retrait | Raison |
  |---|---|---|
  | Taille, année de naissance, sexe, niveau d'activité, orientation | Effacée | Couverte par le consentement |
  | Régimes, préférence de viande, allergènes | Effacée | Article 9 |
  | Pesées saisies ou importées | Effacées | Donnée de santé |
  | Séances et énergie active importées de Santé | Effacées, et l'import s'arrête | Viennent de Santé, sous consentement |
  | Séances saisies dans ZakFit, avec leurs kcal saisies | Gardées | Suivi sportif saisi par l'utilisateur, hors consentement santé |
  | Kcal **estimées** des séances | Effacées (« non renseignées ») | Elles dérivent du poids : avec le MET et la durée, on pourrait recalculer le poids de chaque séance |
  | Repas, favoris, aliments personnalisés | Gardés | Suivi alimentaire, sans donnée de l'article 9 |
  | Objectif calorique | Passe en mode saisi, avec la dernière valeur calculée, ramenée entre 1 200 et 6 000 kcal | L'utilisateur garde un objectif valide (RG35) |
  | Versions calculées de l'historique des objectifs (RG52) | Effacées | Elles dérivent du poids, de la taille, de l'âge et du sexe |
  | Objectifs d'activité | Gardés | Pas de donnée de santé |
  | Historique des consentements (date, version, retrait) | Gardé | Preuve du consentement (article 7 du RGPD) |

- **RG12** — ZakFit s'adresse aux adultes. À l'inscription, une case obligatoire et **déclarative**, « J'ai 18 ans ou plus », est cochée par tous, avec ou sans consentement santé.
  - Si l'année de naissance saisie ensuite donne moins de 18 ans, elle est refusée.
  - La vérification reste déclarative : elle **réduit** le risque d'un utilisateur mineur, sans l'exclure.
  - On n'enregistre que l'année de naissance (minimisation).
  - Limite des formules : Mifflin-St Jeor est validée de 19 à 78 ans, et le Compendium adulte de 19 à 59 ans. Pour 18 ans, et pour 60 ans et plus, l'estimation sort de ces plages, et l'app l'indique.
- **RG13** — Bornes de saisie : taille de 100 à 250 cm, poids de 30 à 300 kg. Le sexe vaut **femme** ou **homme** et ne sert qu'au calcul, parce que la formule de Mifflin-St Jeor n'en connaît que deux. L'écran l'explique.
- **RG14** — Le niveau d'activité prend une valeur d'une liste fermée de 4 niveaux : peu actif, modérément actif, actif, très actif. Ce sont les niveaux d'activité physique (PAL) de l'EFSA 2013 : 1,4, 1,6, 1,8 et 2,0 (voir `02-formules.md`).
- **RG15** — L'orientation vaut **perte**, **maintien** ou **prise de masse** (p. 6). Elle ajuste l'objectif calculé dans des limites (RG34).
- **RG16** — Régimes, repris de Bon App' :
  - préférence de viande : standard, halal, casher ou sans porc ;
  - indicateurs végétarien et végan ;
  - « sans gluten » et « sans lactose » passent par la déclaration des allergènes gluten et lait (RG17), pour ne pas enregistrer deux fois la même information ;
  - végan implique végétarien ;
  - un végétarien n'a pas de préférence de viande, puisqu'elle ne sert plus.
- **RG17** — Les allergènes déclarés appartiennent à la liste des 14 allergènes réglementaires (règlement UE 1169/2011, annexe II). La préférence « sans lactose » du cahier (p. 6) passe par l'allergène « lait (y compris le lactose) ».

### Aliments

- **RG18** — Valeurs d'un aliment, pour 100 g :
  - énergie de 0 à 900 kcal ;
  - protéines, glucides et lipides de 0 à 100 g chacun, avec une somme d'au plus 100 g ;
  - l'énergie déclarée doit rester proche de celle calculée avec les coefficients du règlement UE 1169/2011 : 4 × protéines + 4 × glucides + 9 × lipides + 2 × fibres + 7 × alcool. L'écart toléré est d'au plus 20 %, ou d'au plus 20 kcal, au choix du plus favorable. La marge couvre les polyols et les acides organiques ;
  - pour les aliments de base, la somme protéines + glucides + lipides peut aller jusqu'à 100,5 g, pour tenir compte des arrondis de CIQUAL.

  Cela répond aux pages 13 et 22, qui demandent des valeurs « cohérentes » et des calories « réalistes ».
- **RG19** — Un aliment est soit de **base**, soit **personnalisé**.
  - Les aliments de base sont au départ environ 300 aliments tirés de CIQUAL. L'administrateur peut ensuite en ajouter.
  - Chaque aliment de base appartient obligatoirement à une catégorie : le groupe CIQUAL, par exemple « fruits, légumes, légumineuses » (p. 22). Pour un aliment personnalisé, la catégorie est facultative ; sans elle, il compte comme « non classé » dans les statistiques.
  - Un aliment personnalisé n'est visible et utilisable que par son créateur.
- **RG20** — Unités :
  - un aliment peut avoir plusieurs unités, chacune avec un libellé et un poids en grammes, par exemple « 1 œuf moyen = 50 g » ;
  - une quantité se saisit en grammes ou en unités, et elle est enregistrée en grammes ;
  - l'unité choisie est gardée pour l'affichage.
- **RG21** — Étiquettes et compatibilité :
  - chaque aliment porte ses étiquettes (viande, porc, produit animal, alcool) et ses allergènes. Le poisson, les fruits de mer et le gluten se lisent dans les allergènes ;
  - les étiquettes sont cohérentes : le porc implique la viande, la viande implique un produit animal, et 0,5 g d'alcool pour 100 g ou plus implique l'étiquette alcool ;
  - un aliment est incompatible avec un régime quand ses étiquettes le contredisent ;
  - chaque aliment de base a des étiquettes vérifiées une à une (voir `donnees/README.md`) ;
  - un aliment personnalisé sans étiquettes est marqué « allergènes non renseignés ». L'absence d'étiquette ne vaut jamais « compatible » ;
  - les libellés restent prudents. Par exemple : « ne contient pas de céréales à gluten (aliment générique) », jamais « sans gluten », qui est une mention réglementée par le règlement UE 828/2014 ;
  - **Halal et casher :** aucune base nutritionnelle ne connaît la certification. Le porc rend un aliment incompatible, et les autres viandes affichent « certification non connue ». L'app ne prétend jamais qu'un aliment est halal ou casher.
- **RG22** — Un aliment personnalisé déjà utilisé dans un repas ou un favori ne peut pas être supprimé. Il est archivé : il disparaît de la recherche, mais l'historique reste lisible.

### Repas

- **RG23** — Le type de repas vaut **petit-déjeuner**, **déjeuner**, **dîner** ou **collation** (p. 12).
  - L'utilisateur choisit la date du repas, aujourd'hui par défaut. Il peut choisir un jour passé, mais pas un jour futur.
  - Les dates sont des dates locales. Le fuseau horaire est enregistré dans le profil : l'app l'envoie à la connexion et quand il change.
- **RG24** — Un repas compte au moins une ligne, et la quantité d'une ligne va de 1 à 5 000 g.
  - L'API calcule les valeurs de chaque ligne : valeur pour 100 g × grammes / 100.
  - Elle ignore toute valeur nutritionnelle envoyée par le client.
- **RG25** — Les valeurs calculées d'une ligne sont **figées à l'enregistrement**. Si un aliment de base est corrigé plus tard, les repas passés ne changent pas. Il s'agit d'une valeur historique, comme le prix d'une commande, et non d'une redondance.
  - Quand on modifie un repas, une ligne ajoutée ou dont la quantité change est recalculée avec les valeurs actuelles.
  - Une ligne inchangée garde ses valeurs figées.
- **RG26** — Le total d'un repas est la somme de ses lignes, et le total d'un jour la somme de ses repas. Les deux sont calculés par l'API.
- **RG27** — Un favori a un nom, unique pour un même utilisateur, et des lignes (aliment, quantité, unité). Partir d'un favori crée un nouveau repas, recalculé avec les valeurs actuelles.
- **RG28** — Bonus photo :
  - la proposition ne contient que des aliments de la base, avec leurs grammes ;
  - rien n'est enregistré sans validation ;
  - la photo n'est jamais envoyée ni conservée ;
  - un repas validé garde son origine « photo » et, pour chaque ligne, les grammes estimés. Ces deux informations servent à mesurer la précision du bonus.

### Activités

- **RG29** — Le type d'une activité vient de la liste de référence.
  - Au départ, elle compte 24 types tirés du Compendium 2024, avec leur code et leur MET (voir `02-formules.md`, section 7).
  - Chaque type appartient à une catégorie : cardio, musculation, yoga et souplesse, marche, sports.
  - Il porte aussi (p. 22) :
    - une difficulté (facile, modérée, difficile), tirée au chargement de sa classe d'intensité du Compendium (moins de 3 MET, de 3 à 5,9, 6 et plus) et modifiable par l'administrateur ;
    - des instructions facultatives, en français et en anglais ;
    - les groupes musculaires sollicités. La correspondance de départ est une proposition de ZakFit, modifiable dans le back-office.
  - L'administrateur peut créer un type, mais seulement avec un code et un MET du Compendium. Il ne peut pas modifier le MET d'un type, parce que les conditions d'usage du Compendium l'interdisent. Cette limite s'écarte de la p. 22 (voir section 5).
- **RG30** — La durée est un nombre entier de 1 à 600 minutes. La date ne doit pas être dans le futur.
- **RG31** — Les calories sont facultatives, de 0 à 5 000 (p. 8). Elles ont l'un de ces trois états :
  - **saisies** ;
  - **estimées** : quand elles sont vides et que le poids est connu, l'API les estime en MET net, (MET − 1) × poids × heures (voir `02-formules.md`), à partir du dernier poids ;
  - **non renseignées** : sans poids connu. La séance s'affiche « calories non renseignées » (p. 9), et ces calories ne comptent dans aucune somme. Un total qui contient une séance non renseignée est marqué « incomplet ».
- **RG32** — Filtres et tris (p. 9) :
  - filtres : type ou catégorie, durée minimale, période ;
  - tris : par date (croissante ou décroissante), par type ou par durée.
- **RG33** — Une activité a une origine : **saisie** ou **Santé**.
  - Une activité importée garde l'identifiant de Santé, unique par utilisateur, ce qui évite les doublons.
  - ZakFit écrit dans Santé ses séances saisies, avec leurs kcal, et ses pesées. Il ne réimporte jamais ce qu'il a écrit lui-même (contrôle de la source, qui vaut aussi pour l'énergie).
  - Supprimer une activité importée la marque comme ignorée, pour qu'elle ne revienne pas. Ses kcal sont effacées ; seuls restent ses champs obligatoires (minimisation).
  - Correspondance des types : l'API tient une table fixe qui associe chaque type de séance de Santé à un code du Compendium du référentiel (par exemple, course vers 12050). Une séance sans équivalent n'est pas importée, et l'app indique combien de séances ont été écartées.

### Objectifs, pesées, tableau de bord

- **RG34** — En mode **calculé**, l'objectif calorique part de la dépense de repos (Mifflin-St Jeor), que la p. 15 appelle « métabolisme basal ». On la multiplie par le niveau d'activité (PAL), puis on l'ajuste selon l'orientation, dans des limites.
  - Le résultat ne descend jamais sous la dépense de repos ni sous le plancher de 1 200 kcal, et ne dépasse jamais 6 000 kcal (borne de RG35). Il est arrondi à la dizaine **supérieure**.
  - Il est recalculé à chaque changement du profil ou du poids.
  - Les valeurs sont dans `02-formules.md`.
- **RG35** — En mode **saisi** :
  - une valeur sous 1 200 kcal ou au-dessus de 6 000 kcal est refusée. Ces bornes sont des décisions de conception (voir `02-formules.md`) ;
  - une valeur sous la dépense de repos estimée affiche un avertissement, seulement si cette dépense est calculable, c'est-à-dire avec le consentement santé.
- **RG36** — Les objectifs de macros sont exprimés **en grammes** (p. 14).
  - Par défaut, l'API les calcule à partir de l'objectif calorique et de la répartition de l'ANSES (`02-formules.md` §4), et les recalcule quand l'objectif change.
  - Dès que l'utilisateur les modifie, ils ne bougent plus. Si leur énergie (4 P + 4 G + 9 L) s'écarte de plus de 10 % de l'objectif calorique, l'app affiche un avertissement sans refuser.
- **RG37** — Un objectif d'activité se définit par :
  - une métrique : séances, minutes ou calories brûlées ;
  - une période : jour ou semaine, ou **séance** pour les calories, par exemple « 300 calories par séance » (p. 16) ;
  - une catégorie facultative (vide pour toutes) ;
  - une valeur strictement positive.

  Un objectif a une **période de validité** (premier et dernier jour). Le modifier clôt la ligne en cours et en crée une nouvelle. Le trio métrique, période, catégorie n'a qu'un objectif en cours par utilisateur. Un bilan passé se compare donc à l'objectif qui s'appliquait ce jour-là.
- **RG38** — La semaine va du lundi au dimanche (ISO 8601), et le mois est le mois civil, tous deux dans le fuseau de l'utilisateur. Le jour local d'un repas (`eaten_on`) et d'une séance (`performed_on`) est figé à l'enregistrement : changer de fuseau ne déplace pas les jours passés.
- **RG39** — Une pesée a une date, un poids (RG13) et une origine (saisie ou Santé).
  - On compte au plus une pesée par jour et par utilisateur.
  - Le même jour, une pesée saisie l'emporte sur une pesée importée.
  - Supprimer une pesée importée la marque comme ignorée, pour qu'elle ne revienne pas au prochain import, comme une séance (RG33). Son poids est effacé : seuls restent son jour et son identifiant Santé (minimisation).
  - **Le poids du profil n'est pas stocké à part** : c'est celui de la dernière pesée, ce qui évite d'enregistrer la même information deux fois.
- **RG40** — **Les kcal brûlées** d'un jour sont la somme des kcal des séances de ce jour, saisies ou importées de Santé (sans doublon, RG33), hors séances non renseignées (RG31). Cette valeur sert aux objectifs, au tableau de bord et aux rapports.
  - L'**énergie active** de Santé, qui compte aussi les déplacements du quotidien, est affichée à part, à titre d'information. Elle n'entre dans aucun calcul.
  - Exemple 1, sans Santé : une course saisie de 291 kcal et une marche de 98 kcal donnent 389 kcal brûlées.
  - Exemple 2, avec une montre : une séance importée de 350 kcal donne 350 kcal brûlées, et l'énergie active de 620 kcal s'affiche à part.
  - Exemple 3, avec une séance saisie et l'énergie de l'iPhone : un yoga saisi de 60 kcal donne 60 kcal brûlées, et l'énergie active de l'iPhone (410 kcal) s'affiche à part.
- **RG41** — Les alertes et recommandations sont calculées par l'API à la demande, et non stockées (p. 14-15 et 10-11) :
  - objectif calorique dépassé de X kcal ;
  - macro à moins de 80 % de son objectif à partir de 18 h, ou au-delà de 110 % ;
  - recommandation : « Il te manque X g de protéines », pour une macro sous son objectif à partir de 18 h ;
  - suggestion d'activité pour atteindre un objectif de la semaine, calculée avec la formule MET.
    - On propose l'activité la plus pratiquée, ou la marche rapide sans historique.
    - Sans poids connu, la suggestion se fait en minutes seulement, pour les objectifs en minutes ou en séances.
- **RG42** — Les rappels et les messages motivants (p. 17) sont des notifications locales.
  - L'app les programme à partir des données de l'API, à 18 h par défaut, et chacun se désactive séparément.
  - Elle les reprogramme après chaque saisie, pour que le contenu reste juste.
  - Les messages tutoient, sur un ton sobre.
  - Écart avec la p. 17 (« l'API envoie des notifications ») : voir section 5.

### Suppression et administration

- **RG43** — Supprimer un compte efface toutes ses données : repas et leurs lignes, favoris, aliments personnalisés, activités, pesées, objectifs, consentements. Un seul service sert à l'utilisateur (UC07) et à l'administrateur (UC33).
- **RG44** — Le back-office et ses routes sont réservés au rôle administrateur.
- **RG45** — La liste des utilisateurs affiche le nom, l'email, le statut, la date d'inscription, le nombre d'activités et les objectifs définis (p. 21).
  - Les objectifs affichés sont le mode de l'objectif calorique (calculé ou saisi) et les objectifs d'activité. La valeur calculée n'est pas montrée : elle dérive du poids, de la taille, de l'âge et du sexe.
  - La liste est paginée, filtrable et triable.
  - **Aucune donnée de santé individuelle n'est visible par l'administrateur** : ni poids, ni allergènes, ni régimes, ni orientation. Le filtre de la p. 21 « ayant un objectif de perte de poids » est donc écarté.
- **RG46** — Un aliment de base ou un type d'activité déjà utilisé n'est pas supprimé mais archivé. Un élément jamais utilisé peut être supprimé. La création et la modification appliquent RG18 ou RG29.
- **RG47** — Les statistiques globales sont des agrégats. Une répartition (par âge, sexe ou orientation) qui porte sur moins de 5 personnes est masquée, pour empêcher de reconnaître quelqu'un.
- **RG48** — Les actions d'administration (bloquer, suspendre, réactiver, supprimer, modifier un référentiel) sont journalisées : date, administrateur, identifiant de la cible, action. Le journal ne garde ni l'email ni le nom de la cible, pour que la suppression du compte (RG43) ne laisse pas de donnée personnelle. Le compte d'un administrateur qui a des actions journalisées ne se supprime pas : on le suspend.

### Langue, mentions et avertissements

- **RG49** — L'app suit la langue de l'appareil, français ou anglais. Les aliments ont un nom dans chaque langue : CIQUAL 2025 fournit le nom anglais dans son fichier XML.
- **RG50** — La mention « ZakFit ne remplace pas un avis médical » apparaît dans le questionnaire de démarrage et dans les réglages. Les valeurs calculées sont présentées comme des estimations.
- **RG51** — La recherche d'aliments et les badges de régime ou d'allergène portent un avertissement permanent : « Informations indicatives pour un aliment générique. Vérifie toujours la liste des ingrédients du produit. »
- **RG52** — **L'objectif calorique et les macros sont historisés.** À chaque changement de la cible effective (modification, changement de mode, nouvelle pesée ou nouveau profil en mode calculé), l'API enregistre une version datée et figée. Le bilan d'un jour passé (historique, rapports, statistiques d'administration) utilise la version qui s'appliquait ce jour-là (p. 16, 19, 20, 23).
- **RG53** — Chaque connexion réussie est journalisée avec sa date seulement, sans adresse IP ni appareil. Le tableau de bord d'administration en tire la fréquence des connexions (p. 21). Le journal est effacé avec le compte (RG43).

## 5. Exigences non fonctionnelles et écarts assumés

### Exigences non fonctionnelles (p. 2, 25-26)

| Exigence | Page | Réponse |
|---|---|---|
| MVVM, SwiftUI, app réactive | 25 | ViewModels `@Observable`, vues SwiftUI, injection par protocoles (diagramme de classes du 26/11) |
| Base relationnelle, clés primaires et étrangères, normalisée | 25 | MCD, MLD, MPD (25/11). Seule redondance assumée : les valeurs figées des lignes de repas (RG25) |
| Données centralisées, retrouvées sur tout appareil, iPhone et iPad | 2, 25 | La base du serveur fait foi, et l'app ne garde que le jeton. Elle fonctionne sur iPad sans mise en page dédiée |
| API REST Vapor, performante | 25 | Contrat OpenAPI (26/11), pagination, index SQL |
| JWT vérifié à chaque requête, accès interdit après expiration | 25-26 | RG05, RG06, RG09 |
| CORS selon les bonnes pratiques | 25 | Seule l'origine du back-office est autorisée. L'app native n'en a pas besoin |
| Mots de passe hachés | 26 | RG03 (bcrypt) |
| Chiffrement des données sensibles | 25 | Chiffrement au repos de MariaDB pour les tables qui portent des données personnelles et de santé (plugin `file_key_management`, clé hors du dépôt). Les mots de passe sont en plus hachés (RG03) |
| HTTPS (optionnel) | 26 | Hors périmètre : l'API reste locale (voir ci-dessous) |
| Requêtes SQL optimisées | 26 | Index sur les colonnes de filtre, statistiques en SQL écrit à la main |
| Cache et réduction des appels (optionnel) | 26 | Pas de cache local. Les écrans regroupent leurs données en un seul appel (tableau de bord, journée) |

### Écarts assumés

| Exigence du cahier | Page | Décision | Justification |
|---|---|---|---|
| Base MySQL | 3-5, 25 | MariaDB 10.4 | Base du cours, compatible avec le pilote MySQL de Fluent (décision E1) |
| L'API envoie les notifications | 17 | Notifications locales programmées par l'app à partir des données de l'API | Pas de serveur public pour le push. Le contenu suit les données (RG42) |
| Objectif de poids, délai, rappels de poids | 7, 15, 17 | Hors périmètre | Choix de périmètre (D12). La courbe des pesées reste (UC29) |
| Export PDF | 20 | Hors périmètre, seul le CSV est prévu, en bonus | Choix de périmètre (D17) |
| Exemple « Mot de passe incorrect » | 6 | Message générique | Ne pas révéler qu'un email existe (RG04) |
| L'administrateur modifie les calories brûlées d'un exercice | 22 | Le MET d'un type ne se modifie pas, mais on peut créer un type | Conditions d'usage du Compendium (RG29) |
| Filtre « utilisateurs ayant un objectif de perte de poids » | 21 | Écarté | Donnée de santé, invisible pour l'administrateur (RG45) |
| Section 6.4, fonctionnalités avancées d'administration | 23-24 | Hors périmètre | Choix de périmètre (D18) |
| Déploiement en HTTPS | 26 | Local seulement | Choix E7. L'app joint l'API par le réseau local |
| Micronutriments (vitamines, minéraux) | 12 | Hors périmètre | Mentionnés dans la présentation du suivi, sans liste ni fonctionnalité dans le cahier. ZakFit suit l'énergie et les trois macros, plus les fibres et l'alcool pour le contrôle RG18 |
| Progression automatique d'un objectif (« 10 minutes de plus chaque semaine ») | 16 | Hors périmètre | Possibilité citée en exemple. L'utilisateur peut modifier son objectif, et l'historique garde chaque version (RG37) |
