# Base d'aliments pré-remplie de ZakFit

Ce dossier contient les aliments « de base » de ZakFit (RG19) : 302 aliments courants tirés de la table CIQUAL 2025, avec leurs étiquettes de régime et d'allergènes (RG16, RG17, RG21) et 150 unités de portion (RG20).

> **Statut : remise candidate, révisée le 23/11/2026** selon les décisions de l'orchestrateur : formule RG18 complétée, tolérance d'arrondi, règle de l'étiquette alcool, mention « portion US ».

## Fichiers

| Fichier | Rôle |
|---|---|
| `aliments.csv` | 302 aliments, valeurs pour 100 g, étiquettes et allergènes. **Généré.** |
| `portions.csv` | 150 portions (136 aliments), poids en grammes et source. **Généré.** |
| `outils/selection.csv` | Les 302 aliments choisis à la main (`alim_code`, `motif`). C'est la décision humaine, relisible. |
| `outils/etiquettes.csv` | Les étiquettes relues ligne par ligne (`verifie = oui`, `note` qui justifie les cas non évidents). |
| `outils/portions_choix.csv` | Pour chaque portion : la portion USDA retenue (`fdc_id`, `portion_id`, `portion_us`) ou une estimation avec sa justification. |
| `outils/construire_aliments.py` | Script de construction et de contrôle (bibliothèque standard Python uniquement). |

Les fichiers sources (CIQUAL, USDA) ne sont pas versionnés : on les télécharge (voir « Régénérer les fichiers »).

## Provenance et licences

**Valeurs nutritionnelles** : Anses. 2025. Table de composition nutritionnelle des aliments Ciqual. https://doi.org/10.57745/RDMHWY

- Version : table Ciqual 2025 (fichiers du 03/11/2025, documentation du 19/11/2025), 3 484 aliments.
- Licence : Licence Ouverte / Open Licence Etalab 2.0. Réutilisation libre, à condition de citer la source et de ne pas altérer les données.
- Extrait et adapté par ZakFit : sélection d'aliments et de colonnes, valeurs spéciales converties comme décrit plus bas. Les valeurs chiffrées sont reprises telles quelles, sans arrondi. L'Anses n'est pas associée à cette application.
- Noms anglais : champ `alim_nom_eng` du fichier `alim_2025_11_03.xml` du même dépôt.

**Poids des portions** : U.S. Department of Agriculture, Agricultural Research Service. FoodData Central, 2019. fdc.nal.usda.gov. Jeu « SR Legacy » d'avril 2018 (`FoodData_Central_sr_legacy_food_csv_2018-04`), domaine public (CC0 1.0). Seuls `food.csv`, `food_portion.csv` et `measure_unit.csv` sont lus.

**Date d'extraction** : 23/11/2026.

## Colonnes de `aliments.csv`

| Colonne | Contenu |
|---|---|
| `ciqual_code` | `alim_code` CIQUAL (clé de traçabilité). |
| `nom_fr`, `nom_en` | Noms CIQUAL (`alim_nom_fr`, `alim_nom_eng`), espaces normalisés. |
| `groupe_fr` | Groupe CIQUAL (`alim_grp_nom_fr`). |
| `kcal_100g` | « Energie, Règlement UE N° 1169/2011 (kcal/100 g) », celle des étiquettes. |
| `proteines_100g` | « Protéines, N x 6.25 », cohérentes avec l'énergie réglementaire. |
| `glucides_100g`, `lipides_100g` | Glucides (hors fibres, polyols compris), lipides totaux. |
| `fibres_100g` | Fibres alimentaires ; vide si inconnu. |
| `viande`, `porc`, `poisson_fruits_de_mer`, `produit_animal`, `alcool` | 1 ou 0. `produit_animal` = tout ce qui exclut le végan (viande, poisson, lait, œuf, miel, gélatine…). |
| `allergenes` | Codes des 14 allergènes réglementaires séparés par `|` : `gluten`, `crustaces`, `oeufs`, `poisson`, `arachides`, `soja`, `lait`, `fruits_a_coque`, `celeri`, `moutarde`, `sesame`, `sulfites`, `lupin`, `mollusques`. |

Les nombres utilisent le point décimal. Les valeurs sont celles publiées par CIQUAL (3 chiffres significatifs).

Les compatibilités se déduisent des étiquettes :
- un aliment est végétarien si `viande = 0` et `poisson_fruits_de_mer = 0` ;
- un aliment est végan si `produit_animal = 0` ;
- un aliment est « sans porc » si `porc = 0`, et « sans alcool » si `alcool = 0` ;
- un aliment est « sans céréale à gluten » si `allergenes` ne contient pas `gluten`.

## Contrôle RG18 appliqué

Décision du 23/11/2026. La formule précédente (4P + 4G + 9L) ignorait l'alcool et les fibres. Elle refusait donc le vin, la bière et le champagne, et l'arrondi CIQUAL écartait les huiles d'olive et de tournesol.

```
Énergie calculée = 4 × P + 4 × G + 9 × L + 2 × fibres + 7 × alcool
Accepté si |kcal − énergie calculée| ≤ max(20 kcal, 20 % des kcal)
Bornes : énergie de 0 à 900 kcal ; P, G et L de 0 à 100 g ; P + G + L ≤ 100,5 g
```

- Les coefficients sont ceux de la documentation CIQUAL 2025 (section 3.3.6) : fibres 2 kcal/g, éthanol 7 kcal/g.
- Les fibres et l'alcool sont pris dans CIQUAL. Une valeur inconnue (« - »), « traces » ou « < x » compte pour 0 **dans ce calcul seulement** : la colonne `fibres_100g` reste vide si la valeur est inconnue.
- **Tolérance de 0,5 g sur la somme** : CIQUAL arrondit à 3 chiffres significatifs. Une huile pure peut donc afficher 0,25 g de protéines et 100 g de lipides, soit une somme de 100,25 g. La même tolérance devra s'appliquer aux aliments personnalisés (RG18 côté API).
- Les 302 aliments retenus passent ce contrôle. Le script le vérifie deux fois, sur CIQUAL puis sur `aliments.csv`.

## Critères de sélection

- Aliments génériques couramment consommés par un adulte en France, répartis sur tous les groupes CIQUAL sauf les aliments infantiles (groupe 11).
- Une seule forme quand plusieurs sont quasi identiques. On garde celle que l'on pèse d'habitude : viande cuite (et quelques crues), riz, pâtes et légumineuses cuits et secs, légumes crus ou cuits selon l'usage.
- Pas de produits rares, régionaux ou de marque. Pour l'eau, on garde l'eau du robinet et la moyenne des eaux plates, pas les eaux minérales nommées.
- Des options végétariennes, véganes et sans gluten en nombre suffisant pour que les filtres aient du sens : tofu, tempeh, seitan, haché végétal, boissons végétales, légumineuses, pâtes et pain sans gluten…
- Les quatre valeurs clés (énergie, protéines, glucides, lipides) doivent être connues, et l'aliment doit passer RG18. Sinon, le script l'exclut ; on le remplace alors par un équivalent quand il en existe un.
- **Réintégrés après la révision de RG18** : vin rouge, vin blanc sec, vin rosé, champagne, bière « cœur de marché » (4-5°), huile d'olive vierge extra, huile de tournesol. L'huile de colza et l'huile combinée olive et graines sont conservées.

### Aliments par groupe

| Groupe CIQUAL | Aliments |
|---|---:|
| entrées et plats composés | 31 |
| fruits, légumes, légumineuses et oléagineux | 70 |
| produits céréaliers | 27 |
| viandes, oeufs, poissons | 52 |
| produits laitiers | 32 |
| eaux et autres boissons | 22 |
| produits sucrés | 34 |
| glaces et sorbets | 2 |
| matières grasses | 7 |
| aides culinaires et ingrédients divers | 25 |
| **Total** | **302** |

Étiquettes : 45 aliments avec viande, dont 22 avec porc ; 19 avec poisson ou fruits de mer ; 140 avec un produit animal ; 13 avec de l'alcool. Compatibilités : 238 végétariens, 162 végans, 233 sans céréale à gluten.

Allergènes : gluten 69, lait 79, œufs 29, soja 25, poisson 14, sulfites 10, fruits à coque 8, moutarde 6, céleri 5, sésame 4, mollusques 4, crustacés 2, arachides 2, lupin 0.

## Traitement des valeurs spéciales

D'après la documentation CIQUAL 2025 (sections 3.2.2 à 3.2.4 et 4.2) :

| Valeur CIQUAL | Sens | Traitement |
|---|---|---|
| nombre (virgule) | teneur moyenne | repris tel quel, virgule remplacée par un point |
| `-` | valeur inconnue (« ne pas assimiler à zéro ») | énergie, protéines, glucides ou lipides inconnus : l'aliment est exclu. Fibres inconnues : cellule vide (2 aliments : 11214, 19863). |
| `traces` | détecté sans pouvoir être quantifié, ou estimé très faible | 0 (glucides de 15 aliments, fibres de 3) |
| `< x` | sous la limite de quantification x | **0** (lipides de 30 aliments, fibres de 16) |

**`< x` → 0 est un choix conservateur pour P, G et L.** La vraie teneur est comprise entre 0 et x : l'erreur sur chaque nutriment est donc au plus de x g pour 100 g. Les bornes rencontrées sont faibles (0,05 à 0,6 g pour les lipides), soit quelques kcal au plus. L'Anses ne prescrit pas de traitement ; x/2 était l'autre option possible.

## Méthode d'étiquetage

1. **Proposition automatique** : le script la recalcule à chaque exécution. Elle part de règles par sous-groupe CIQUAL (viandes, charcuteries, poissons, mollusques et crustacés, œufs, produits laitiers) et de mots-clés sur le nom (`porc`, `jambon`, `lardon`, `lait`, `fromage`, `blé`, `pain`, `pâtes`, `soja`, `sésame`, `noix`…).
2. **Relecture manuelle ligne par ligne** des 302 aliments, consignée dans `outils/etiquettes.csv` (`verifie = oui`, et une note dès que le cas n'est pas évident). Le rapport du script liste les 83 écarts entre la proposition automatique et la relecture. Ce sont surtout des plats composés, viennoiseries et biscuits, où le nom ne dit pas tout : farine du roux, œuf de dorure, lécithine de soja, lardons du bœuf bourguignon…
3. **Contrôles de cohérence**, bloquants dans le script :
   - viande ou poisson implique `produit_animal` ;
   - porc implique viande ;
   - un allergène d'origine animale (lait, œufs, poisson, crustacés, mollusques) implique `produit_animal` ;
   - poisson, crustacés ou mollusques vont avec `poisson_fruits_de_mer` ;
   - éthanol CIQUAL ≥ 0,5 g/100 g implique `alcool = 1` ;
   - `alcool = 1` sans ce seuil doit être justifié dans la note ;
   - les codes d'allergènes appartiennent à la liste des 14.

### Allergènes

On étiquette un allergène s'il figure dans la recette classique ou dans la plupart des produits du commerce. Exemples : pain = gluten ; pâtes aux œufs = gluten et œufs ; fromage = lait ; mayonnaise = œufs et moutarde ; avoine = gluten, au sens du règlement. Un allergène présent seulement dans certaines recettes figure dans la note, sans étiquette : lait dans certaines margarines, sésame sur certains pains à burger…

### Règle de l'étiquette `alcool`

`alcool = 1` dans l'un de ces trois cas seulement :
- c'est une boisson alcoolisée : vins, champagne, bières, cidre ;
- CIQUAL mesure au moins 0,5 g d'éthanol pour 100 g ;
- c'est un plat cuisiné avec un vin ou un alcool nommé : bœuf bourguignon et moules marinières (vin de cuisson, éthanol résiduel 0 dans CIQUAL), tiramisu (1,8 g/100 g dans la recette CIQUAL).

Sous le seuil, l'alcool n'est pas étiqueté et la teneur est notée : pain de mie blanc 0,2 g, pain sans gluten 0,078 g, gâteau marbré 0,1 g.

**Écart avec la consigne initiale, signalé** : la consigne demandait `alcool = 0` pour le pain de mie, le pain à burger, le pain sans gluten et la bière sans alcool, en les supposant sous 0,5 g. Or CIQUAL mesure 0,82 g (pain de mie complet), 0,89 g (pain à burger) et 0,62 g (bière sans alcool). Le seuil de 0,5 g s'applique donc et ces trois aliments gardent `alcool = 1`, avec une note. Pour les passer à 0, il suffit de modifier la colonne dans `outils/etiquettes.csv`. Il faut aussi assouplir le contrôle « éthanol ≥ 0,5 g ⇒ alcool » du script.

### Porc et viande non précisée : prudence

Ces étiquettes servent à exclure, et RG21 interdit d'affirmer qu'un aliment convient à un régime religieux. On applique donc la prudence :
- **Plats « à la viande » sans espèce précisée** (hachis parmentier, lasagnes et pâtes à la bolognaise, chili con carne) : `viande = 1` et `porc = 1`, avec la note « porc possible (viande non précisée) ». La recette type est souvent au bœuf, mais certaines versions du commerce contiennent du porc. Mieux vaut masquer à tort un plat sans porc que présenter comme compatible un plat qui en contient.
- Une charcuterie est classée porc sauf mention contraire (merguez bœuf-mouton, blanc de dinde).
- Le bœuf bourguignon est classé porc à cause des lardons de la recette classique.
- Le bonbon gélifié est classé viande et porc à cause de la gélatine, souvent porcine.
- Les plats dont la recette traditionnelle exclut le porc (couscous à la viande, kebab, hamburger, nuggets de poulet) ne sont pas classés porc. Ils restent soumis au message « certification non connue ».

## Portions (`portions.csv`)

- Seuls les aliments qui se comptent naturellement ont des portions : œuf, fruit ou légume entier, tranche, pot, cuillère, verre, canette… Les autres se saisissent en grammes.
- **122 portions** viennent de USDA SR Legacy (`source = USDA SR Legacy fdc_id=<id>`). Pour chacune, on a choisi l'aliment USDA le plus proche et la mesure correspondante (`portion_id` dans `outils/portions_choix.csv`). Le script vérifie que la portion appartient bien à ce `fdc_id`. Les poids USDA sont ceux de la partie mangée : 1 œuf « large » = 50 g sans coquille, 1 banane moyenne = 118 g sans peau. C'est la même base que CIQUAL (partie comestible).
- **Portions au format américain** : la `source` se termine par « (portion US) » quand le poids USDA est sans doute éloigné du produit français équivalent. C'est le cas de la tranche d'emmental (28 g), de la tranche de pain de mie complet (32 g) et de la petite sardine à l'huile (12 g). Ces portions sont gardées faute de meilleure source ouverte.
- **28 portions** sont des estimations (`source = estimation : <justification>`). On en fait une quand la mesure USDA ne correspond pas à l'usage français :
  - formats d'emballage français : pot de yaourt de 125 g, petit-suisse de 60 g, canette de 33 cl, demi de 25 cl ;
  - tailles différentes des produits américains : tranche de jambon, biscotte, petit-beurre.

  Pour les boissons, le poids est calculé à partir de la densité USDA (le `fdc_id` d'origine est cité dans la justification). Aucun `fdc_id` n'est inventé.
- Certains libellés gardent la mesure américaine quand c'est elle qui donne le poids, par exemple « 1 grand verre (1 tasse US) » ou « calibre US large ».

## Limites

- **Aliments génériques** : les étiquettes décrivent une recette type. Elles ne remplacent pas la liste des ingrédients et des allergènes de l'emballage. Il faut l'afficher dans l'app : « Informations indicatives pour des aliments génériques ».
- **« Sans gluten »** : c'est une mention réglementée (au plus 20 mg/kg, règlement (UE) n° 828/2014). L'app doit dire « ne contient pas de céréale à gluten (aliment générique) », pas « sans gluten ».
- **Halal et casher** : aucune base ne les connaît. On n'étiquette que le porc, l'alcool et la viande (RG21) ; les autres viandes affichent « certification non connue ». La séparation viande-lait n'est pas vérifiable aliment par aliment.
- **Végétarien** : les fromages à présure animale ne sont pas distingués. La gélatine n'est repérée que dans le bonbon gélifié, le seul aliment retenu qui en contient habituellement.
- **Recettes variables** : les plats préemballés (soupes, plats en sauce, falafels, haché végétal) ont été étiquetés selon la recette la plus courante. Leurs notes signalent les variantes.

## Régénérer les fichiers

Télécharger dans un dossier hors du dépôt :
- `Table Ciqual 2025_FR_2025_11_03.xlsx` : https://entrepot.recherche.data.gouv.fr/api/access/datafile/666260 (page : https://doi.org/10.57745/RDMHWY)
- `alim_2025_11_03.xml` : https://entrepot.recherche.data.gouv.fr/api/access/datafile/666252
- `FoodData_Central_sr_legacy_food_csv_2018-04.zip` : https://fdc.nal.usda.gov/fdc-datasets/FoodData_Central_sr_legacy_food_csv_2018-04.zip, à décompresser dans un dossier vide.

Puis, depuis `docs/conception/donnees/` :

```sh
python3 -I outils/construire_aliments.py \
  --ciqual "<sources>/Table Ciqual 2025_FR_2025_11_03.xlsx" \
  --xml "<sources>/alim_2025_11_03.xml" \
  --usda "<sources>/FoodData_Central_sr_legacy_food_csv_2018-04"
```

- Le script affiche son rapport : aliments par groupe, candidats exclus et pourquoi, valeurs spéciales, écarts d'étiquetage, détail des portions. Il écrit `aliments.csv` et `portions.csv`.
- Il s'arrête avec un code d'erreur si un contrôle échoue : code absent ou en double, nom manquant, étiquette incohérente, portion orpheline ou introuvable dans USDA, virgule non protégée dans un fichier de décision.
- Ajouter `--verifier` pour comparer sans rien écrire : le script échoue si les fichiers livrés diffèrent de la régénération.
- `--ciqual` accepte aussi un export CSV du même XLSX. Les deux donnent des fichiers identiques (vérifié le 23/11/2026).
- Pour modifier la base, éditer `outils/selection.csv`, `outils/etiquettes.csv` ou `outils/portions_choix.csv`, jamais les CSV générés.
