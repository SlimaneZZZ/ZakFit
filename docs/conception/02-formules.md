# ZakFit — formules de calcul

Version 1 du 23/11/2026. Chaque formule cite sa source. Quand aucune source institutionnelle n'existe, la valeur est présentée comme une **décision de conception**, avec sa justification. Toutes les valeurs sont des **estimations** : l'app le dit à l'utilisateur et ne remplace pas un avis médical.

## 1. Dépense de repos : Mifflin-St Jeor

```
Homme : REE = 10 × poids (kg) + 6,25 × taille (cm) − 5 × âge (ans) + 5
Femme : REE = 10 × poids (kg) + 6,25 × taille (cm) − 5 × âge (ans) − 161
```

- **Source :** Mifflin MD et al., *A new predictive equation for resting energy expenditure in healthy individuals*, Am J Clin Nutr 1990;51(2):241-247, DOI 10.1093/ajcn/51.2.241.
  - L'équation a été établie sur 498 adultes de 19 à 78 ans.
- **Précision :** environ 4 personnes sur 5 sont estimées à ±10 % de la mesure.
  - 78 % selon Frankenfield 2003, DOI 10.1016/s0002-8223(03)00982-9 ;
  - 82 % selon Frankenfield 2013, DOI 10.1016/j.clnu.2013.03.022, avec 87 % chez les personnes non obèses et 75 % chez les personnes obèses.
  - Une revue systématique la juge la plus fiable des équations courantes (Frankenfield 2005, DOI 10.1016/j.jada.2005.02.005).
- **Dans ZakFit :**
  - l'âge vaut l'année en cours moins l'année de naissance. On ne stocke que l'année (RG12), et un an d'écart change le résultat de 5 kcal ;
  - le poids est celui de la dernière pesée (RG39) ;
  - le résultat est arrondi à l'unité.

## 2. Dépense totale : niveau d'activité physique (PAL)

```
Dépense totale = REE × PAL
```

| Niveau dans l'app | PAL | Description affichée |
|---|---|---|
| Peu actif | 1,4 | Travail assis, peu de déplacements à pied, pas d'exercice régulier |
| Modérément actif | 1,6 | Environ 30 minutes d'activité modérée par jour, en comptant les déplacements |
| Actif | 1,8 | Environ 1 heure d'exercice modéré à vigoureux par jour |
| Très actif | 2,0 | Métier très physique, ou entraînement soutenu de plus d'une heure par jour |

**Les descriptions sont une décision de conception.** Seul le niveau « Actif » s'appuie sur un exemple de la FAO (2004, §5.3.2) : une heure par jour d'exercice modéré à vigoureux fait passer un mode de vie sédentaire (PAL 1,55) à « modérément actif » (1,70 à 1,99). Les trois autres sont interpolés à partir des plages de la FAO. Elles ont été choisies prudentes : surestimer le niveau d'activité réduirait le déficit réel.

- **Source :** EFSA NDA Panel, *Scientific Opinion on Dietary Reference Values for energy*, EFSA Journal 2013;11(1):3005, DOI 10.2903/j.efsa.2013.3005. Les besoins de l'adulte y sont calculés avec des PAL de 1,4, 1,6, 1,8 et 2,0.
  - Les définitions s'appuient sur FAO/OMS/UNU, *Human energy requirements*, 2004, chapitre 5 : sédentaire de 1,40 à 1,69, actif de 1,70 à 1,99, vigoureux de 2,00 à 2,40.
- **Écart assumé :** les coefficients 1,2 / 1,375 / 1,55 / 1,725 / 1,9 que reprennent beaucoup d'applications n'ont pas de source vérifiable. Le 1,2 est même sous le seuil sédentaire de la FAO et de l'EFSA. ZakFit ne les utilise pas.
- **Cohérence :** l'EFSA rapporte le PAL à la **dépense de repos** (équation de Henry), comme Mifflin-St Jeor. Choisir les valeurs de l'EFSA est donc cohérent avec la formule. La FAO, elle, rapporte le PAL au métabolisme basal. L'écart entre les deux notions n'a pas été chiffré dans nos sources.

## 3. Objectif calorique calculé

```
Base        = Dépense totale (section 2)
Perte       : Base − 500
Maintien    : Base
Prise       : Base + 300
Objectif    = min(6 000, arrondi à la dizaine supérieure de max(Base ajustée, REE, 1 200))
```

Le plafond de 6 000 kcal reprend la borne de l'objectif saisi (RG35). Ainsi, au retrait du consentement, la dernière valeur calculée reste toujours un objectif saisi valide (RG11).

L'arrondi se fait **vers le haut**, pour que l'objectif ne tombe jamais sous la REE. Par exemple, une REE de 1 214 donne 1 220, et non 1 210.

- **Perte, − 500 kcal par jour :** c'est le bas de la fourchette de déficit (500 à 750 kcal par jour) de la recommandation AHA/ACC/TOS 2013 (Jensen et al., Circulation 2014;129(25 Suppl 2):S102-S138). On retient la borne la plus prudente.
  - **Limite :** cette recommandation vise des adultes en surpoids ou obèses. Pour une personne de poids normal, la HAS (2011) rappelle qu'en simple surpoids l'objectif est surtout de ne pas prendre de poids, et l'ANSES (2010) décrit les risques d'un amaigrissement sans indication médicale.
  - ZakFit garde donc deux garde-fous : le plancher (REE et 1 200 kcal) et la mention médicale (RG50).
- **Prise de masse, + 300 kcal par jour : décision de conception.** Aucune référence institutionnelle n'a été trouvée pour ce chiffre. On choisit un surplus modéré, plus petit que le déficit, et l'utilisateur peut passer en mode saisi (p. 16 du cahier).
- **Plancher à 1 200 kcal : décision de conception**, appuyée sur NICE NG246 (2025, section 1.16).
  - Pour NICE, les régimes de 800 à 1 200 kcal par jour relèvent d'un service spécialisé, avec un suivi.
  - La HAS (2011) déconseille les régimes sous 1 000 kcal par jour, sauf exception supervisée.
  - Le chiffre de 1 200 kcal pour les femmes et 1 500 pour les hommes, souvent cité, n'est pas un seuil de sécurité dans les sources : c'est une cible de régime (AHA 2013). ZakFit applique donc un seul plancher, le même pour tous.
- **Ne jamais descendre sous la dépense de repos : décision de conception prudente.** Aucune source n'en fait un plancher. L'ANSES rappelle toutefois qu'une forte restriction fait baisser la dépense de repos et favorise la reprise de poids (*Évaluation des risques liés aux pratiques alimentaires d'amaigrissement*, 2010, p. 59).
- **Le rythme de perte n'est pas affiché**, puisque l'objectif de poids est hors périmètre. La règle des 7 700 kcal par kg surestime la perte réelle (Hall 2011, Lancet 378:826-837 ; Thomas 2013) : on ne l'utilise pas pour prédire une date.

**Objectif saisi (RG35) :**
- refusé sous 1 200 kcal ;
- refusé au-dessus de 6 000 kcal, comme saisie invraisemblable. C'est une **décision de conception**, sans source ;
- avertissement sous la REE, seulement si elle est calculable (avec le consentement santé) : « Cet objectif est inférieur à ta dépense de repos estimée ».

## 4. Macronutriments

**Répartition par défaut, en pourcentage de l'objectif calorique :**

| Macro | Défaut ZakFit | Intervalle ANSES (adulte) |
|---|---|---|
| Protéines | 15 % | 10 – 20 % |
| Lipides | 37 % | 35 – 40 % |
| Glucides | 48 % | 40 – 55 % |

- **Source :** Anses, avis 2012-SA-0103, *Actualisation des repères du PNNS*, décembre 2016, tableau 4. Les pourcentages s'entendent hors alcool.
- **Les valeurs par défaut sont une décision de conception :** on prend une valeur au milieu de chaque intervalle, ajustée pour que la somme fasse 100 %.
- **Personnalisation :** l'utilisateur peut fixer ses grammes librement (p. 14). L'app affiche un avertissement, sans refuser, si l'énergie de ses macros (4 P + 4 G + 9 L) s'écarte de plus de 10 % de l'objectif calorique, ou si leur répartition sort des intervalles de l'ANSES.

**Objectifs en grammes proposés par défaut (RG36), avec les coefficients d'Atwater :**

```
Protéines (g) = Objectif × %P / 4
Glucides  (g) = Objectif × %G / 4
Lipides   (g) = Objectif × %L / 9
```

- **Source :** règlement (UE) n° 1169/2011, annexe XIV : protéines 4 kcal/g, glucides 4, lipides 9, fibres 2, alcool 7. Voir aussi FAO, *Food energy – methods of analysis and conversion factors*, 2003, §3.5.1.

## 5. Valeurs d'un aliment et d'un repas

```
Valeur d'une ligne = valeur pour 100 g × grammes / 100
Grammes            = quantité en unités × poids de l'unité (g)   (si saisie en unités)
Total repas        = Σ lignes ; Total jour = Σ repas du jour
```

- **Énergie de référence :** la colonne « Energie, Règlement UE N° 1169/2011 (kcal/100 g) » de CIQUAL 2025. Son libellé a été vérifié dans le fichier téléchargé le 23/11/2026.
- **Valeurs spéciales de CIQUAL :**
  - « - » (inconnu) n'est jamais compté comme zéro. Un aliment dont l'énergie, les protéines, les glucides ou les lipides sont inconnus n'est pas importé.
  - « traces » vaut 0.
  - « < x » vaut 0 pour les protéines, les glucides et les lipides. C'est un choix conservateur, dont l'impact est d'au plus x g.
- **Contrôle de cohérence (RG18), coefficients de l'annexe XIV du règlement UE 1169/2011 :**
  ```
  Énergie calculée = 4 × P + 4 × G + 9 × L + 2 × fibres + 7 × alcool
  Accepté si |Énergie déclarée − Énergie calculée| ≤ max(20 kcal, 20 % de l'énergie déclarée)
  ```
  - La marge restante couvre les polyols et les acides organiques.
  - Une valeur de fibres ou d'alcool inconnue compte pour 0 dans ce contrôle seulement.
  - Pour les aliments de base, la somme P + G + L peut aller jusqu'à 100,5 g, à cause des arrondis de CIQUAL : l'huile d'olive, par exemple, fait 100,15 g.
  - Jeux d'essai :
    - poulet rôti, 165 kcal avec 31 g de protéines et 3,6 g de lipides : 4 × 31 + 9 × 3,6 = 156,4 kcal, accepté ;
    - vin rouge : accepté grâce au terme 7 × alcool.
- **Arrondis :** les calculs se font en décimal (type `Decimal` en Swift et `DECIMAL` en SQL), sans arrondi intermédiaire. L'arrondi de l'affichage se fait au plus proche, 0,5 vers le haut, aussi bien dans l'API que dans le SQL écrit à la main. On affiche les kcal à l'unité et les grammes de macros à 0,1 g près.

## 6. Calories d'une activité : MET

```
kcal estimées = (MET − 1) × poids (kg) × durée (h)
```

- **Unité :** 1 MET = 1 kcal/kg/h, selon le Compendium of Physical Activities, page « Unit Conversions », https://pacompendium.com/.
- **On soustrait 1 MET** pour ne garder que la dépense due à l'activité (**MET net**). C'est une **adaptation inspirée de l'IOM, donc une décision de conception** : dans *Dietary Reference Intakes for Energy…* (2005, chapitre 12), l'IOM calcule le gain de PAL d'une activité avec (MET − 1). La formule en kcal ci-dessus n'y figure pas telle quelle.
  - **Pourquoi :** la dépense de repos est déjà comptée dans l'objectif (REE × PAL).
  - **Cohérence :** Apple distingue de la même façon l'énergie active (`activeEnergyBurned`) de l'énergie de repos (`basalEnergyBurned`), dans la documentation HealthKit `HKQuantityTypeIdentifier` (https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier).
- **Exemple :** 70 kg, 30 min de course à 9,3 MET donnent (9,3 − 1) × 70 × 0,5 = 290,5, soit **291 kcal** avec l'arrondi 0,5 vers le haut (section 5).
- **Limite :** le Compendium sert à classer des intensités, pas à mesurer la dépense d'une personne (Herrmann 2024, §4.3). 1 MET surestime en moyenne de 20 % la dépense de repos réelle (Byrne 2005, J Appl Physiol 99:1112). L'app affiche donc « estimé ».
- **Âge :** les valeurs adultes valent pour les 19 à 59 ans. Il existe un Compendium pour les 60 ans et plus, non intégré dans la version 1.

## 7. Types d'activité (référentiel)

**Source des valeurs :** Herrmann SD et al., *2024 Adult Compendium of Physical Activities*, J Sport Health Sci 2024;13(1):6-12, DOI 10.1016/j.jshs.2023.10.010, PDF officiel sur https://pacompendium.com/.
- **Conditions d'usage :** les valeurs sont libres d'usage, y compris commercial, à condition de citer le site et de **ne pas modifier les valeurs ni fusionner des activités de MET différents**. ZakFit garde donc un code du Compendium par type d'activité.

| Catégorie | Activité (FR) | Activity (EN) | Code | MET |
|---|---|---|---|---|
| Marche | Marche lente | Slow walk | 17152 | 2,8 |
| Marche | Marche modérée | Moderate walk | 17190 | 3,8 |
| Marche | Marche rapide | Brisk walk | 17200 | 4,8 |
| Marche | Randonnée | Hiking | 17080 | 6,0 |
| Cardio | Course lente (~8 km/h) | Easy run (~8 km/h) | 12030 | 8,5 |
| Cardio | Course modérée (~10 km/h) | Moderate run (~10 km/h) | 12050 | 9,3 |
| Cardio | Course rapide (~11 km/h) | Fast run (~11 km/h) | 12070 | 11,0 |
| Cardio | Vélo loisir (< 16 km/h) | Leisure cycling (< 16 km/h) | 01010 | 4,0 |
| Cardio | Vélo soutenu (22-25 km/h) | Fast cycling (22-25 km/h) | 01040 | 10,0 |
| Cardio | Natation (longueurs, allure tranquille) | Lap swimming (easy) | 18240 | 5,8 |
| Cardio | Rameur | Rowing machine | 02071 | 5,0 |
| Cardio | Elliptique | Elliptical trainer | 02048 | 5,0 |
| Cardio | HIIT | HIIT | 02214 | 11,0 |
| Cardio | Corde à sauter | Jump rope | 15551 | 11,8 |
| Musculation | Musculation | Strength training | 02054 | 3,5 |
| Musculation | Musculation intense | Heavy strength training | 02050 | 6,0 |
| Musculation | Circuit training | Circuit training | 02035 | 5,0 |
| Yoga et souplesse | Yoga | Yoga | 02175 | 2,3 |
| Yoga et souplesse | Pilates | Pilates | 02105 | 2,8 |
| Sports | Football | Soccer | 15610 | 7,0 |
| Sports | Basket | Basketball | 15055 | 7,5 |
| Sports | Tennis | Tennis | 15675 | 6,8 |
| Sports | Danse | Dancing | 03025 | 4,5 |
| Sports | Boxe (sac) | Boxing (punching bag) | 15110 | 5,8 |

**Difficulté (RG29) :** elle est tirée de la classe d'intensité du Compendium (Herrmann 2024, §2.5) : facile sous 3 MET, modérée de 3 à 5,9, difficile à partir de 6.

Cela fait 24 types. Les catégories reprennent celles du cahier (p. 8 : cardio, musculation, yoga, marche), plus « sports ». Les vitesses en km/h sont converties depuis les intitulés du Compendium, qui sont en mph.

## 8. Totaux, périodes et kcal brûlées

- **Semaine :** du lundi au dimanche (ISO 8601). **Mois :** mois civil. Tous deux dans le fuseau de l'utilisateur (RG38).
- **Kcal brûlées d'un jour :** la somme des kcal des séances du jour, saisies ou importées sans doublon, hors séances non renseignées (RG40). L'énergie active de Santé est affichée à part, sans entrer dans les calculs.
- **Bilan du jour affiché :** consommé moins objectif. Le graphique « consommé contre brûlé » du cahier (p. 16 et 19) compare les kcal consommées aux kcal brûlées par l'activité.
- **Suggestion d'activité (RG41) :** minutes nécessaires = kcal manquantes / ((MET − 1) × poids) × 60, avec l'activité la plus pratiquée de l'utilisateur, ou la marche rapide (4,8 MET) s'il n'a pas d'historique.

## Références

- Mifflin MD et al. Am J Clin Nutr. 1990;51(2):241-247. https://pubmed.ncbi.nlm.nih.gov/2305711/
- Frankenfield DC et al. J Am Diet Assoc. 2003;103(9):1152-1159 ; 2005;105(5):775-789. Frankenfield DC. Clin Nutr. 2013;32(6):976-982.
- EFSA NDA Panel. EFSA Journal. 2013;11(1):3005. https://efsa.onlinelibrary.wiley.com/doi/10.2903/j.efsa.2013.3005
- FAO/WHO/UNU. *Human energy requirements*. 2004. https://www.fao.org/4/y5686e/y5686e07.htm
- Institute of Medicine. *Dietary Reference Intakes for Energy, Carbohydrate, Fiber, Fat, Fatty Acids, Cholesterol, Protein, and Amino Acids*. 2005. DOI 10.17226/10490
- Herrmann SD et al. J Sport Health Sci. 2024;13(1):6-12. https://pacompendium.com/
- Byrne NM et al. J Appl Physiol. 2005;99(3):1112-1119.
- Anses. Avis 2012-SA-0103. 2016. Anses. *Évaluation des risques liés aux pratiques alimentaires d'amaigrissement*. 2010.
- Règlement (UE) n° 1169/2011, annexe XIV. https://eur-lex.europa.eu/legal-content/FR/TXT/?uri=CELEX:32011R1169
- FAO. *Food energy – methods of analysis and conversion factors*. 2003.
- Jensen MD et al. (AHA/ACC/TOS). Circulation. 2014;129(25 Suppl 2):S102-S138.
- NICE. Guideline NG246. 2025. https://www.nice.org.uk/guidance/ng246
- HAS. *Surpoids et obésité de l'adulte : prise en charge médicale de premier recours*. 2011.
- Hall KD et al. Lancet. 2011;378:826-837. Thomas DM et al. Int J Obes. 2013;37:1611-1613.
