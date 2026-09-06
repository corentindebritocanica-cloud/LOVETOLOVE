# Duo Training

Application web mono-fichier (HTML/CSS/JS vanilla, aucun build, aucun npm) de suivi de musculation en duo pour **Corentin** et **Lisa**. Ouverte dans Safari sur iPhone. Thème sombre par défaut avec bascule vers un thème clair. ~5 000 lignes, ~249 Ko
(dont ~17 Ko d'icône encodée en base64).

## Où vit le projet

| | |
|---|---|
| Dépôt | `github.com/corentindebritocanica-cloud/PLANNING-CAB-LISA` |
| App déployée | `corentindebritocanica-cloud.github.io/PLANNING-CAB-LISA/` |
| Code (lecture directe) | `https://raw.githubusercontent.com/corentindebritocanica-cloud/PLANNING-CAB-LISA/refs/heads/main/index.html` |
| Ce fichier (lecture directe) | `https://raw.githubusercontent.com/corentindebritocanica-cloud/PLANNING-CAB-LISA/refs/heads/main/README.md` |

Le fichier s'appelle `index.html` dans le dépôt (contrainte GitHub Pages), et
`muscu-duo.html` dans les échanges. C'est le même fichier.

## Méthode de travail avec Claude

À chaque session : coller les deux liens bruts ci-dessus, décrire les
modifications voulues, récupérer le fichier complet en retour, le commiter.

Points à connaître, tous vérifiés :

- **Seul `raw.githubusercontent.com` est lisible.** Le lien « Raw » de
  `github.com` et la page `/branches` sont bloqués aux robots. La page
  `/blob/` du fichier s'arrête à la ligne 1000 et peut servir un rendu en
  cache périmé — ne pas s'y fier.
- **La lecture porte sur ce qui est poussé**, jamais sur les modifications
  locales non commitées.
- **Le fichier complet est rendu, pas un correctif** : appliquer un diff à la
  main dans 3 500 lignes sur téléphone est le meilleur moyen d'introduire une
  erreur.
- **Regrouper les demandes.** Chaque session commence par relire ~145 Ko ;
  cinq modifications d'un coup coûtent bien moins que cinq conversations.
- **Les suites de tests ne survivent pas d'une session à l'autre.** Elles sont
  réécrites au besoin, en couvrant la zone touchée — d'où l'importance de la
  section « Tests » plus bas.

## Contraintes techniques à toujours respecter

- **Fichier HTML unique**, tout le CSS et JS dedans. Pas de framework, pas de bundler. Décision confirmée : le découpage en `style.css` / `app.js` serait techniquement possible (l'app est forcément servie en HTTP, sinon le `<script type="module">` ne fonctionnerait pas), mais on garde la propriété « un fichier qu'on dépose et qui marche ».
- Firebase SDK chargé **en CDN via `<script type="module">`**. Version : `firebasejs/12.18.0`.
- Robustesse LocalStorage obligatoire : try/catch + fallback mémoire (préférences locales et données de la séance en cours ; les archives sont dans Firestore).
- **Tous les champs de saisie en `font-size:16px` minimum** : en dessous, Safari iOS zoome au focus.
- Cible : iPhone Safari. Voir « Bugs iOS déjà corrigés ».
- Avant toute livraison : `node --check` sur les quatre blocs `<script>` **et** les suites de tests (voir « Tests »).

## Architecture de navigation

```
[écran de connexion] → [splash 2,5 s] → view-menu (Menu principal)
├── Entraînement      → view-profile → view-session → view-exercises
│                                            └────── → view-archives ⇄ corbeille
├── Build Training    → view-builder
├── Coach             → view-coach (fil de discussion)
└── Suivi Progression → view-progress
```

**Retour par glissement.** Un balayage vers la droite déclenche le **bouton retour
de l'écran actif** (`goBackFromActiveView`) plutôt qu'une table de destinations :
le geste ne peut donc pas diverger du tap, y compris pour le rappel d'archivage.
Neutralisé sur les champs, les boutons, les listes déroulantes, les barres
segmentées et la zone de rédaction, ainsi que pendant le splash, la connexion et
toute modale ouverte. Exige un geste franchement horizontal (`SWIPE_MIN_X`,
`SWIPE_MAX_Y`, `SWIPE_MAX_MS`), sinon un défilement oblique déclencherait un retour.

`showView(viewId, direction)` gère l'affichage, le glissement et appelle systématiquement `adjustBottomSpacing()`. Un **écran de chargement** de 2,5 s précède le menu.

**Tous les écrans alignent leur contenu en haut.** Le menu principal et l'écran
des profils étaient les deux seuls centrés verticalement (classe `center-view`,
supprimée) : c'était la seule incohérence de mise en page de l'app. Seul
`view-exercises` a une structure différente — header collant + `main` + barre
du bas — les six autres partagent `.view-inner` à l'identique.

Retour contextuel du builder : `builderReturn` vaut `'menu'` (ouverture depuis le menu) ou `'session'` (édition via ✏️). `exitBuilder()` ramène au bon écran et le libellé du bouton s'adapte.

## Jetons de design (CSS)

**Toute couleur, tout rayon et toute ombre passe par un jeton défini en tête du `<style>`.** Une valeur codée en dur plus bas est une anomalie — et fait échouer `test9.js`.

- **Palette** : charcoal légèrement bleuté (`--bg:#0d1014`, `--card:#161b22`, `--card-2:#1e2530`), choisi pour évoquer l'acier laqué d'un rack sous néon plutôt qu'un gris neutre interchangeable.
- `--tint` / `--tint-strong` : voiles clairs posés sur les fonds (icônes, états sélectionnés). **Ils s'inversent en thème clair** — auparavant neuf `rgba(255,255,255,…)` en dur rendaient ces éléments invisibles en mode clair.
- `--sheen` : reflet blanc des animations de balayage (passe toujours sur une surface colorée).
- **Rayons**, cinq crans + pilule : `--r-xs` 4px (jauges), `--r-sm` 10px (champs), `--r-md` 14px (boutons), `--r-lg` 18px (cartes), `--r-xl` 22px (modales), `--r-pill`. **La taille encode la hiérarchie.** L'app comptait 14 valeurs distinctes avant harmonisation.
- **Ombres** : `--shadow-sm`, `--shadow`, `--shadow-lg`. Rien d'autre.
- **Durées** : `--t-fast` .14s, `--t-mid` .22s.
- Identité : `--corentin` `#4c8dfb`, `--lisa` `#f2599e`, `--done` `#12b981`, `--danger` `#ef4444`. `--accent` suit le profil actif.

## Icône d'application

Générée d'après l'écran de chargement (fond charcoal, dégradé radial bleu à
gauche / rose à droite, haltère centré) et **encodée en base64 dans le HTML** pour
tenir la contrainte du fichier unique. Rien à téléverser à côté.

Avec `apple-mobile-web-app-capable`, « Ajouter à l'écran d'accueil » ouvre l'app
en plein écran, sans la barre Safari.

Deux pièges :
- iOS met les icônes d'accueil **en cache très agressivement** : pour voir un
  changement, supprimer le raccourci et le recréer.
- Si iOS refusait le base64, déposer `icon.png` à côté de `index.html` et
  remplacer les deux `href="data:image/png;base64,…"` par `href="icon.png"`.
  L'icône source est reproductible : script PIL + numpy, dégradé radial calculé
  pixel par pixel, centre du motif vérifié au demi-pixel.

## Écran de chargement

2,5 s puis fondu de 0,46 s. Barre de musculation qui se dessine, disques bleu et rose qui glissent, jauge qui se remplit, trois messages de statut successifs (800 ms chacun).

Deux garde-fous à ne pas retirer : le script est **isolé dans sa propre balise `<script>`** placée juste après son markup (si le script principal plantait, l'écran s'effacerait quand même), et une animation CSS de secours l'efface à 5 s **même si le JS ne s'exécute pas du tout**.

## Programme fixe (SESSIONS) et surcharges

4 séances codées en dur (`s1` à `s4`) : `label`, `title`, `muscleIcon`, `cardio`, `exercises[]` avec `{ name, sets, target:{corentin,lisa}, logType? }`.
- `logType:'circuit'` → pas de charge, une seule case libre (voir « Circuits »).
- `equipmentOptions` n'est plus lu : le mode de charge est proposé sur **tous**
  les exercices chargés (voir « Mode de charge »).

**Les 4 séances sont modifiables.** Éditer l'une d'elles enregistre une
**surcharge** dans `customSessions`, sous le **même id** (`s1`…), qui prend le
pas sur la version codée en dur. Trois conséquences voulues :

- aucune collection ni règle Firestore supplémentaire ;
- les archives référencent `sessionId`, donc le tonnage par séance continue de
  fonctionner y compris sur les séances archivées avant modification ;
- c'est réversible : supprimer la surcharge (bouton ↺) restaure l'original.

Points d'implémentation :
- `getSession(id)` consulte **d'abord** la surcharge, puis `SESSIONS`.
- `getPureCustomSessions()` exclut les surcharges de la liste des séances
  personnalisées, sinon `s1` apparaîtrait deux fois.
- `decorateSession()` récupère le `muscleIcon` de l'originale : le SVG n'est pas
  stocké en base.
- À l'enregistrement, le `title` d'une séance fixe est **repris tel quel** — le
  builder ne saisit que le nom, et écraser le sous-titre par « Séance
  personnalisée » perdrait « Bas du Corps (Quads & Fessiers) ».
- Une séance fixe n'a **pas** de 🗑️ : elle ne doit pas pouvoir disparaître. Le ↺
  n'apparaît que si une surcharge existe, et la ligne porte une étiquette
  « modifiée ».

## Firebase / Firestore / Authentification

- **Projet** : `duo-training-e835b`.
- **La base est fermée.** Les règles exigent `request.auth != null` sur toutes les
  collections. Un **compte unique** (e-mail/mot de passe) est utilisé sur les deux
  téléphones.
- ⚠️ **Les abonnements `onSnapshot` sont regroupés dans `subscribeAll()` et ne
  démarrent qu'après `onAuthStateChanged`.** S'abonner avant la connexion
  provoquerait un `permission-denied` sur chaque écoute.
- **Le mode hors-ligne survit** : Firebase conserve la session localement, donc
  après une première connexion l'app fonctionne en salle sans réseau.
- **Collections** : `archives`, `customSessions`, `coachChat`, et `settings`
  (documents `coach` pour la clé API / le modèle / les poids, et `threads` pour la
  liste des conversations). La corbeille (`deletedAt`), le catalogue d'exercices
  (dérivé) et les surcharges de séances fixes (même id dans `customSessions`) n'ont
  demandé aucune collection supplémentaire.
- Règles à publier (console → Firestore → Règles) :

```
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    match /archives/{id}        { allow read, write: if request.auth != null; }
    match /customSessions/{id}  { allow read, write: if request.auth != null; }
    match /coachChat/{id}       { allow read, write: if request.auth != null; }
    match /settings/{id}        { allow read, write: if request.auth != null; }
    match /{document=**}        { allow read, write: if false; }
  }
}
```

⚠️ **Ordre des opérations** : créer le compte AVANT de publier les règles, sinon
l'app affiche un écran de connexion qu'aucun identifiant n'ouvre.
- **Persistance hors-ligne** : `initializeFirestore(app, { localCache: persistentLocalCache({ tabManager: persistentMultipleTabManager() }) })`, repli sur `getFirestore(app)` si IndexedDB manque. ⚠️ `enableIndexedDbPersistence` est **déprécié**, ne pas y revenir.
- **Écritures offline-first — la règle la plus importante du fichier** : Firestore ne résout la promesse de `setDoc`/`deleteDoc` qu'**après confirmation du serveur**. Hors ligne elle reste pendante indéfiniment alors que l'écriture est en cache. **Ne jamais mettre à jour l'interface dans un `.then()`** : agir immédiatement, et n'utiliser le `.catch()` que pour rattraper une erreur. Dans `finishArchive`, ce catch restaure la séance depuis une sauvegarde locale.
- **Marqueurs de chargement** : `window.__archivesLoaded` et `window.__customSessionsLoaded`, posés au premier snapshot, pilotent les squelettes.
- Caches : `window.archivesCache`, `window.archivesTrashCache`, `window.customSessionsCache`. Événements `archives-updated` / `custom-sessions-updated`.
- Pont module → script classique : `window.__fb = { db, doc, setDoc, deleteDoc }`.

## Écran de saisie

### Champs
- Poids / Reps / ✓ par série, avec bouton ⇊ de recopie à partir de la série 2.
- ⚠️ **Champs numériques en `type="text"` + `inputMode`**, jamais `type="number"` : avec un clavier français, « 22,5 » est jugé invalide par Safari et `input.value` renvoie une chaîne vide — la saisie disparaissait silencieusement. `sanitizeField()` filtre à la frappe ; **`parseNum()` (virgule → point) pour tout calcul**, jamais `parseFloat`.
- Note « 🗒️ Info » par exercice, et sélecteur de mode de charge sur tout
  exercice chargé.

### Circuits (`logType:'circuit'`)
Grille : `Tour | Résultat | ✓`, avec **une seule case de texte libre** par tour
(champ `info` sur la série). Deux cases chiffrées avaient été essayées puis
abandonnées : un circuit enchaîne des mouvements de natures différentes — des
répétitions pour l'un, des secondes pour l'autre — et aucun couple de champs
numériques ne peut représenter ça. On note « 14 relevés + 50 s de gainage »
dans les mots de l'exercice.

Les anciennes saisies `reps` / `duration` sont recomposées à l'affichage et à
l'export (« 12 reps + 45 s ») : rien n'est perdu.

La consigne d'origine reste dans le nom de l'exercice (« Relevés de jambes
12-15r + Gainage 45s ») et dans la cible (« 3 tours »). Les circuits sont exclus
du tonnage, des records, du rappel de dernier poids et du mode de charge — sans
charge, aucun de ces calculs n'a de sens.

### Mode de charge (`LOAD_MODES`)
Le matériel n'est pas le bon critère. La seule question qui change le calcul :
**une charge dans chaque main, ou une charge partagée ?**

- Deux haltères de 22,5 kg × 10 → chaque répétition déplace 45 kg → 450 kg.
- Poulie à 22,5 kg, 10 à droite puis 10 à gauche → 20 répétitions → 450 kg.

Simultané ou alterné, le total est le même : ce qui double, c'est la présence de
deux charges, pas l'ordre d'exécution. ⚠️ Le facteur est **×2, pas ×4** —
doubler à la fois le poids et les répétitions compterait chaque kilo deux fois.

Trois modes, proposés sur tous les exercices chargés :

| id | Bouton | Sous-titre | Facteur |
|---|---|---|---|
| `total` | Barre / machine | charge totale | ×1 |
| `dumbbell` | Haltères | poids par main | ×2 |
| `single` | Un bras à la fois | poids par main | ×2 |

- **Aucune présélection.** On arrive sur un exercice vierge : rien de coché, pas
  d'explication affichée, en-tête neutre, facteur ×1. Une déduction depuis le
  titre avait été essayée puis retirée — elle donnait l'impression que l'app
  choisissait à la place de l'utilisateur.
- **Re-toucher le mode actif le désactive** et revient à l'état vierge.
- Chaque bouton porte sa conséquence **en toutes lettres**, pas un `×2` : le
  facteur seul ne disait pas quoi taper. Le champ `hint` de chaque mode décrit
  case par case ce qu'on attend, avec un exemple chiffré.
- L'en-tête des colonnes devient « Poids / main » et « Reps / bras » quand le
  mode double, pour que la consigne soit visible au moment de la saisie.
- ⚠️ **La saisie n'est jamais modifiée.** Le doublement n'intervient qu'au calcul
  du tonnage. Le record reste 22,5 kg par haltère — sinon il deviendrait
  incomparable à une barre — et le rappel de dernier poids propose bien ce qu'il
  faut charger de chaque côté.
- ⚠️ **Les anciennes valeurs (« Haltères », « Poulie 2 mains »…) sont ignorées.**
  Elles désignaient un matériel, sans effet sur le tonnage. Les traduire vers un
  mode doublerait rétroactivement des séances saisies sous une autre règle.
  `normalizeLoadMode()` n'accepte que les identifiants du modèle actuel.

### Cardio
Proposé à la fin de **chaque** séance, y compris celles qui n'en prévoient pas
(`dayProgram.cardio === null`) : la carte affiche alors « Cardio — Optionnel ».

- Non coché, la carte se réduit à sa ligne du haut (classe `collapsed`).
- ⚠️ **Décocher n'efface rien** : les champs sont masqués, pas vidés. Effacer une
  saisie sur un simple appui aurait été une mauvaise surprise.
- Le cardio **optionnel** ne compte pas dans la progression : une case
  facultative ne doit pas empêcher d'atteindre 100 %. Le cardio **prévu** par la
  séance compte, lui, comme avant.
- L'export ne le mentionne que s'il est prévu ou coché ; un cardio fait en plus
  apparaît comme « Cardio (hors programme) ».
- Champs : minutes, % inclinaison, vitesse (⚠️ niveau affiché sur les tapis Basic
  Fit, pas des km/h), note libre.

### Structure de la carte
Deux zones distinctes : `.exercise-headwrap` (fond teinté — nom, cible, historique, record) et `.exercise-body` (fond neutre — badge, variantes, séries, note). Une carte dont toutes les séries sont validées reçoit la classe `complete` : bordure verte et liseré sur la tranche gauche.

### Historique et records
- `getLastPerformance(profile, nom)` alimente les **placeholders gris** de chaque série (la série 1 propose ce qui a été fait en série 1) et la ligne « Dernière fois : … ». Le placeholder n'est **jamais** une valeur : champ vide = vide dans l'export et dans le tonnage.
- `getPersonalRecord(profile, nom)` affiche le record et déclenche le badge vert dès qu'une saisie le dépasse, avec l'écart. Calculé **sur les archives uniquement** : la séance en cours ne doit pas faire bouger le record pendant la saisie.
- Les archives en corbeille sont exclues des deux.
- Les exercices `logType:'circuit'` sont épargnés (pas de poids).

### Clés de données
- **Notes et variantes indexées par nom d'exercice** (`exerciseKey()` → `name:<nom>`), pas par position. `readByExercise()` lit le nouveau format avec repli sur l'ancienne clé numérique.
- **Les clés de séries (`ex<idx>_set<n>`) restent indexées par position** : elles sont figées dans les archives et servent au graphique. Ne pas y toucher.

### Undo
Snapshot **armé** au focus (`armUndoSnapshot`), **empilé à la première frappe réelle** (`snapshotBeforeEdit`). `pushUndoSnapshot` refuse d'empiler deux états identiques. Sans ça la pile se remplissait de doublons et le bouton semblait cassé.

### Rappel d'archivage
`leaveExercisesView()` intercepte le retour. Si la séance contient des données non archivées, une modale rappelle que **rien n'est perdu** (tout est en LocalStorage) mais que la séance **ne comptera pas dans la progression**. Le message ne doit jamais parler de perte de données, ce serait faux — `test7.js` le vérifie.

« Plus tard » mémorise **l'état des données au moment du refus** (`leaveReminderDismissed`). Tant que rien ne bouge : silence. Dès qu'une nouvelle saisie arrive : le rappel se réarme. Une sourdine permanente aurait rendu le garde-fou inutile précisément quand il sert.

## Archives et corbeille

- Flux de fin de séance : « Séance terminée ✅ » → copier, ou archiver (vide la séance courante, fonctionne hors ligne).
- **Supprimer ne détruit rien** : on écrit un `deletedAt` et l'archive part en corbeille. Restauration en retirant le champ. Le vidage de la corbeille (`emptyTrash`) est le seul `deleteDoc` réel, sous confirmation explicite.
- **Pas de purge automatique** — décision assumée : quelques dizaines d'archives par an ne coûtent rien, et une purge silencieuse est le genre de chose qu'on regrette.
- Bascule Archives ⇄ Corbeille via `archivesMode`.

## Suivi Progression

Entrée du menu principal. Sélecteur **Corentin / Lisa** piloté par `progressProfile`, **volontairement distinct de `currentProfile`** : consulter les courbes de l'autre ne change pas le profil d'entraînement.

Ordre de lecture de l'écran, chaque bloc portant un intitulé : **qui** → **combien
au total** → **quoi suivre** → **sur quelle période** → **la courbe**.

- **Cumul** en tête (`getLifetimeStats`) : tonnage total et nombre de séances, corbeille exclue.
- **Sélection** : un `<select>` natif (`renderProgressExerciseList`), pas une
  liste de boutons. Sur iPhone, Safari l'affiche en molette plein écran et
  l'écran garde la même longueur quel que soit le nombre d'exercices. Deux
  `optgroup` : « Tonnage par séance (N) » puis « Exercices (N) ». Une option
  d'amorce « Choisis un exercice… » tant que rien n'est sélectionné, sinon le
  premier exercice paraîtrait choisi alors qu'aucune courbe n'est affichée ; le
  menu est reconstruit au `change` pour la retirer et marquer le champ.
  ⚠️ `font-size:16px` impératif sur `.progress-select`, sinon Safari zoome.
- **Une seule métrique : le poids max.** Volume et reps max ont existé puis ont
  été retirés — trois choix pour une même courbe brouillaient la lecture plus
  qu'ils n'aidaient. Le sélecteur de métrique a disparu avec eux.
- **Une note de séance** (`sessionNote`) distincte des notes d'exercice existe sur
  l'écran de saisie : elle porte le contexte du jour (fatigue, douleur, matériel)
  et part dans l'archive, donc jusqu'au coach.
- **Tonnage : une entrée par séance**, jamais un tonnage global. Clé
  `__tonnage__:<sessionId>` (`PROGRESS_TONNAGE_PREFIX`, `isTonnageKey()`,
  `tonnageSessionId()`). Additionner un bas du corps et un haut du corps n'a
  aucun sens : la courbe ne retient que les occurrences de **cette** séance.
  `getArchivedSessions()` liste les séances réellement archivées et retient le
  libellé de l'archive la plus récente, pour qu'une séance renommée garde son
  nom actuel.
- **Période** (`progressPeriod`) : 1 / 3 / 6 mois, ou tout. Placée juste
  au-dessus du graphique, puisque c'est lui qu'elle commande.
- **Écart** (`getProgressDelta`) : gain absolu, pourcentage et contexte, vert / rouge / gris. Rien ne s'affiche sous deux points.
- **Étiquettes de dates** : au-delà de 8 points, une sur N seulement, première et dernière toujours conservées. Sinon elles se chevauchent en bouillie.
- Ligne centrée verticalement quand toutes les valeurs sont identiques.
- Le rafraîchissement temps réel s'appuie sur `progressSelection`, qui survit au
  re-render — pas sur un élément du DOM, comme c'était le cas avant le passage
  au menu déroulant.

## Coach (IA)

Deux usages distincts, qui partagent la même mémoire :
- **Bilan de séance** : structuré, rattaché à une archive, met à jour le profil.
  Bouton dans la modale d'archive.
- **Fil de discussion** (`view-coach`) : questions libres, plusieurs conversations.

### Mémoire en trois couches
Envoyer tout l'historique brut atteindrait ~100 000 tokens par appel au bout d'un
an, pour un résultat *moins* bon — le modèle se noie dans le détail. D'où :

1. **Les chiffres**, calculés par le code (`buildCoachDigest`) : records, cinq
   dernières valeurs par exercice, tonnage par type de séance. Exact, gratuit,
   compact, et couvre **tout** l'historique.
2. **Les archives récentes en texte intégral** (`buildArchiveExcerpts`, 6 par
   défaut) : c'est là que sont les notes, le cardio, les variantes, le contexte.
3. **Un profil évolutif** que le modèle réécrit à chaque bilan, stocké dans le
   champ `coachProfile` de l'archive. Lire la dernière archive donne le profil
   courant, et l'historique de son évolution est conservé.

Le fil de discussion plafonne l'historique envoyé (`CHAT_HISTORY_LIMIT`) : sans
ça le coût grimperait indéfiniment à mesure que la conversation s'allonge.

### Conversations
Définies en base (`settings/threads`), donc créables et supprimables sans toucher
au code, et identiques sur les deux téléphones. Chacune porte un `prompt` — le
rôle du coach à cet endroit (« tu es diététicien… ») — placé **en tête** du prompt
système, les consignes de fond étant conservées.

- Barre **collante** en haut : changer de conversation sans remonter le fil.
  Menu déroulant plutôt qu'onglets, qui ne tiendraient pas en largeur au-delà de
  trois ou quatre.
- `suivi` et `questions` ne sont **pas supprimables** : les messages écrits avant
  cette fonctionnalité n'ont pas de champ `thread` et y sont rattachés par défaut
  (`messageThread`), ils deviendraient invisibles.
- Supprimer une conversation efface aussi ses messages, sous confirmation.
- L'ouverture et le changement de fil défilent en bas (`scrollChatToBottom`).

### Clés API et modèles
- Clé, modèle et poids de corps dans `settings/coach`, donc **saisis une fois pour
  les deux téléphones**. Acceptable uniquement parce que les règles sont fermées.
- ⚠️ **Google migre des clés `AIza` vers des clés d'autorisation `AQ.`**, liées à
  un compte de service. Toutes les nouvelles clés AI Studio sont au format `AQ.`,
  et de nombreux 401 sont rapportés avec elles sur l'API REST.
  `geminiFetch()` tente donc la clé **en paramètre d'URL d'abord** (voie
  historique, et pas d'en-tête personnalisé donc pas de requête CORS préalable
  depuis Safari), puis réessaie avec `x-goog-api-key` sur un 401.
- **Ne jamais coder un nom de modèle en dur.** Le défaut est `gemini-flash-latest`,
  un alias que Google repointe. Le bouton « Charger les modèles disponibles »
  interroge l'endpoint `models` et remplit une liste — il sert aussi de
  **diagnostic de la clé** : il affiche le code HTTP et le message brut de Google.
- **Auto-réparation** : sur un 404, `withModelRepair()` récupère la liste, choisit
  le meilleur remplaçant (`pickBestModel` : alias `latest` > flash stable >
  flash > n'importe lequel), l'enregistre et réessaie **une seule fois**.
  Si la réparation échoue à son tour, c'est l'erreur d'origine qui remonte, plus
  parlante que « liste indisponible ».
- Messages d'erreur distincts : 401 oriente vers la clé, 403 vers l'API désactivée
  sur le projet, 404 vers le modèle, 429 vers le quota.

### Cadrage
Le prompt impose la prudence sur les douleurs (réduire l'amplitude, substituer,
consulter si ça persiste — jamais forcer), interdit l'encouragement générique, et
exige de comparer des séances du **même type**. L'estimation calorique est
présentée comme un ordre de grandeur.

### Coût
~7 000 tokens en entrée et ~1 200 en sortie par bilan. À trois séances par
semaine, moins d'un euro par mois même avec un modèle haut de gamme. La mise en
cache des prompts ne sert à rien ici : elle expire bien avant le bilan suivant.

## Catalogue d'exercices (autocomplétion du Build Training)

Le graphique retrouve un exercice par son **nom exact** : une faute de frappe scinde la courbe.

- **Aucune collection dédiée** : le catalogue est dérivé de `SESSIONS`, `customSessionsCache` et des `exerciseNames` de toutes les archives (les deux profils). Un exercice reste donc proposé même si la séance qui l'a introduit est supprimée.
- Trois filets : suggestions filtrées (insensibles casse/accents), alerte de proximité par distance de Levenshtein (≤ 2, ou ≤ 3 au-delà de 12 caractères) avec bouton d'adoption, et `canonicalExerciseName()` qui recale casse, accents et espaces à l'enregistrement.
- Panneau maison (`<datalist>` est peu fiable sur Safari iOS). Les options ont un `onmousedown` avec `preventDefault()`, sinon le `blur` masquerait le panneau avant le clic.

## Build Training

Nom de séance, case cardio, exercices dynamiques (nom avec autocomplétion, séries, reps par profil, case circuit, case variante, réordonnancement ▲▼). Édition et suppression depuis la liste des séances.

⚠️ **Le nom de séance et la case cardio sont recopiés dans `builderDraft` à chaque frappe.** Sans ça, tout re-render du formulaire les réécrase avec les valeurs périmées du brouillon — le nom saisi se vidait dès qu'on cochait « circuit ».

## Animations et retours d'état

- **Validation de série** : agrandissement + onde verte (`checkRipple`). C'est le geste le plus répété de l'app, il doit se voir bras tendus.
- **Séance à 100 %** : jauge verte, reflet qui la parcourt **une seule fois** (classe `celebrate` posée au franchissement, pas à chaque re-render), libellé « Séance complète ».
- **Transitions d'écran** : 0,22 s / 16 px (contre 0,32 s / 28 px avant), pour accompagner le geste plutôt que le retarder.
- **Micro-animations** : enfoncement des boutons de variante et de duplication, animation de sélection, flash de confirmation à la recopie.
- **Toasts empilables** : 3 maximum, les plus anciens évincés. Un message répété est relancé, pas dupliqué. ⚠️ Le retrait du DOM est **différé** (temps du fondu) : ne jamais faire de `while` sur `stack.children` pour évincer l'excédent, ça boucle à l'infini. Filtrer d'abord sur `dataset.leaving`.
- **Squelettes de chargement** sur les archives, la liste des séances et la progression. Ils ne s'affichent **que si la liste est réellement vide** : Firestore livre souvent le cache local avant la confirmation serveur, et montrer des barres grises alors que les données sont disponibles serait absurde.
- `prefers-reduced-motion: reduce` respecté partout (au moins 6 garde-fous, vérifié par test).

## Autres

- **Thème clair/sombre** : bouton flottant, préférence en LocalStorage (`duo_theme`).
- **Barre de progression + tonnage**, recalculés **à chaque frappe**.
- **Échappement HTML** : `escapeHtml()` obligatoire sur tout contenu saisi injecté via `innerHTML`.
- **Stockage** : `storage.set` marque la clé dans `memoryOnlyKeys` si `setItem` échoue ; `storage.get` donne alors priorité à la mémoire.
- `loadDayData()` normalise systématiquement (`blankDayData()` + `Object.assign`).
- **Vibration** : code présent, sans effet sur Safari iOS.

## Bugs iOS déjà corrigés (ne pas régresser)

- `height:100%` sur `html, body` plafonnait la page → `min-height`.
- Bottom-bar recouvrant le dernier exercice → `adjustBottomSpacing()`. **La réserve n'est appliquée que sur `view-exercises`** ; ailleurs elle créait un grand vide.
- Bouton undo recouvert par le badge de sync et le bouton de thème (tous deux `position:fixed`) → `.header-row` a un `padding-right:86px`.
- Éviter de tuiler un `repeating-linear-gradient` avec un `background-size` qui ne correspond pas à sa période.

## Tests

Onze suites écrites au fil du projet, **273 assertions**. Elles vivent dans
l'environnement d'exécution et ne sont pas versionnées : elles sont réécrites à
la demande, en ciblant la zone modifiée. Ce tableau dit quoi recouvrir.

| Domaine | À couvrir |
|---|---|
| Saisie | virgule décimale, filtrage des champs, undo armé/empilé |
| Circuits | case libre, reprise des anciennes saisies, exclusion du tonnage |
| Mode de charge | facteur ×2, absence de présélection, en-têtes, export |
| Cardio | case à cocher, champs masqués, progression, export |
| Archivage | hors ligne (promesse non résolue), export texte, rappel d'archivage |
| Corbeille | `deletedAt`, restauration, vidage, exclusion des stats |
| Catalogue | suggestions, fautes de frappe, normalisation à l'enregistrement |
| Séances fixes | surcharge, restauration ↺, absence de doublon, titre et icône |
| Navigation | menu, profils, builder (retour contextuel), progression |
| Progression | menu déroulant, tonnage par séance, période, écart, étiquettes |
| Historique | dernier poids en placeholder, record personnel, cumul |
| Chargement | minutage du splash, disparition, filet de sécurité |
| Design | jetons (aucune valeur en dur), structure des cartes, alignement |
| Retours d'état | toasts empilables, validation, 100 %, squelettes |
| Connexion | écran, erreurs, abonnements différés après auth |
| Coach | mémoire trois couches, bilan, stockage sur les 2 archives |
| Conversations | création, rôle, cloisonnement, suppression, migration |
| Clés et modèles | `AQ.`/`AIza`, repli d'en-tête, liste, auto-réparation |
| Glissement | déclenche le bouton retour, zones neutralisées |

Méthode : charger le HTML dans **jsdom** (`runScripts:'dangerously'`) et appeler les fonctions globales.

Pièges connus :
- Les `const`/`let` de premier niveau (`storage`, `undoStacks`, `builderDraft`, `currentProfile`, `progressSelection`…) ne sont **pas** exposés sur `window` — y accéder via `window.eval('...')`. Les `function` le sont.
- Le script `type="module"` n'est pas exécuté par jsdom : simuler `window.__fb` à la main, avec des promesses **jamais résolues** pour reproduire le hors-ligne.
- `toLocaleString('fr-FR')` produit une **espace insécable fine** (U+202F), pas une espace ordinaire. Normaliser avant comparaison.
- Penser à poser `window.__archivesLoaded` / `__customSessionsLoaded`, sinon les squelettes remplacent le contenu attendu.
- Lancer avec un `timeout` : un bug de boucle fait geler la suite plutôt qu'échouer.
- Simuler `window.fetch` pour l'API Gemini : aucune clé n'est utilisée en test.
  Vérifier qu'aucune clé de test ne se retrouve dans le fichier livré. Attention,
  la clé **Firebase** (`AIza…`) y est légitimement présente : elle est publique par
  conception, la sécurité venant des règles.
- Poser `window.__authUser` puis émettre `auth-changed`, sinon l'écran de
  connexion recouvre l'app.

## Données non stockées côté app

Poids/reps/séries, notes libres, dates. Firestore est en accès ouvert (pas d'authentification) — acceptable entre deux personnes connaissant l'URL, mais c'est le point faible de l'architecture si l'app devait s'ouvrir.

## Pour la suite

Traité : refonte UI/UX, architecture en écrans, variantes, notes, cardio enrichi, undo, archives Firebase, Build Training, graphique de progression, export global, mode hors-ligne, badge de sync, passe complète de correction de bugs, catalogue d'exercices, menu principal, écran de chargement, corbeille, dernier poids, records, cumul, rappel d'archivage, lot progression complet, jetons de design, refonte des cartes, animations et retours d'état, réorganisation du Suivi Progression, menu déroulant, tonnage par séance, alignement de tous les écrans, séances fixes modifiables, saisie des circuits en case libre, mode de charge, cardio optionnel, note de séance, **authentification Firebase**, **coach IA** (bilans + fil de discussion, mémoire trois couches, conversations à rôle), réglages partagés, auto-réparation des modèles, retour par glissement, icône d'application.

Abandonné en connaissance de cause :
- **Série en échec** — écarté pour ne pas compliquer le calcul du tonnage et des records.
- **Accent personnalisable** — le bleu et le rose ne sont pas décoratifs, ils indiquent quel profil est actif et distinguent les courbes. Et il n'y a pas d'écran de réglages où le loger.
- **Choix de métrique** (volume, reps max) — implémenté puis retiré : trois
  courbes possibles pour un même exercice compliquaient la lecture sans rien
  apporter. Ne pas le réintroduire sans raison précise.
- **Tonnage toutes séances confondues** — retiré au profit d'une entrée par
  séance : la courbe globale mélangeait des séances incomparables.

Pistes évoquées, non faites :
- **Fusion de deux noms d'exercice déjà archivés.** Le catalogue protège les futures saisies, mais deux orthographes déjà en archive restent deux courbes (le nom est figé dans l'archive). Il faudrait réécrire les documents archivés.
- **Progression des circuits.** Les reps et durées des circuits sont désormais
  archivées : on pourrait tracer l'évolution du gainage, ce que le Suivi ne
  propose pas encore (il ne suit que le poids max).
- **Progression des circuits.** Reps et durées sont archivées mais le Suivi ne
  trace que le poids max.
- **Le bilan de séance et le fil de discussion sont indépendants.** Le bilan
  n'apparaît pas dans le fil, et le fil ne met pas à jour le profil. Les réunir
  serait cohérent mais demanderait de repenser les deux.
- Chrono de repos, boutons +/- de charge, bandeau « séance en cours », dupliquer une séance, bibliothèque d'exercices, comparer Corentin et Lisa sur un même graphe, calendrier des séances, recherche dans les archives, export CSV, partage iOS natif, installation en PWA, sauvegarde JSON, authentification Firebase.
