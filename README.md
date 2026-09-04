# Duo Training

Application web mono-fichier (HTML/CSS/JS vanilla, aucun build, aucun npm) de suivi de musculation en duo pour **Corentin** et **Lisa**. Ouverte dans Safari sur iPhone. Thème sombre par défaut avec bascule vers un thème clair. ~3 460 lignes.

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
view-menu (Menu principal)
├── Entraînement      → view-profile → view-session → view-exercises
│                                            └────── → view-archives ⇄ corbeille
├── Build Training    → view-builder
└── Suivi Progression → view-progress
```

`showView(viewId, direction)` gère l'affichage, le glissement et appelle systématiquement `adjustBottomSpacing()`. Un **écran de chargement** de 2,5 s précède le menu.

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

## Écran de chargement

2,5 s puis fondu de 0,46 s. Barre de musculation qui se dessine, disques bleu et rose qui glissent, jauge qui se remplit, trois messages de statut successifs (800 ms chacun).

⚠️ Le commentaire HTML au-dessus du bloc dit encore « 2 s puis fondu » alors que
le code est à 2500 ms — reste d'un ajustement, à corriger à l'occasion.

Deux garde-fous à ne pas retirer : le script est **isolé dans sa propre balise `<script>`** placée juste après son markup (si le script principal plantait, l'écran s'effacerait quand même), et une animation CSS de secours l'efface à 5 s **même si le JS ne s'exécute pas du tout**.

## Programme fixe (SESSIONS)

4 séances codées en dur (`s1` à `s4`) : `label`, `title`, `muscleIcon`, `cardio`, `exercises[]` avec `{ name, sets, target:{corentin,lisa}, logType?, equipmentOptions? }`.
- `logType:'circuit'` → pas de poids/reps, « Tour N » + check.
- `equipmentOptions` → sélecteur de variante Haltères / Poulie.

## Firebase / Firestore

- **Projet** : `duo-training-e835b`.
- **Collections** : `archives` et `customSessions`. **Aucune collection n'a été ajoutée** depuis la mise en place des règles — ni la corbeille (champ `deletedAt` dans `archives`) ni le catalogue d'exercices (dérivé) n'en ont eu besoin. Si une nouvelle collection apparaît un jour, **penser aux règles de sécurité**.
- **Persistance hors-ligne** : `initializeFirestore(app, { localCache: persistentLocalCache({ tabManager: persistentMultipleTabManager() }) })`, repli sur `getFirestore(app)` si IndexedDB manque. ⚠️ `enableIndexedDbPersistence` est **déprécié**, ne pas y revenir.
- **Écritures offline-first — la règle la plus importante du fichier** : Firestore ne résout la promesse de `setDoc`/`deleteDoc` qu'**après confirmation du serveur**. Hors ligne elle reste pendante indéfiniment alors que l'écriture est en cache. **Ne jamais mettre à jour l'interface dans un `.then()`** : agir immédiatement, et n'utiliser le `.catch()` que pour rattraper une erreur. Dans `finishArchive`, ce catch restaure la séance depuis une sauvegarde locale.
- **Marqueurs de chargement** : `window.__archivesLoaded` et `window.__customSessionsLoaded`, posés au premier snapshot, pilotent les squelettes.
- Caches : `window.archivesCache`, `window.archivesTrashCache`, `window.customSessionsCache`. Événements `archives-updated` / `custom-sessions-updated`.
- Pont module → script classique : `window.__fb = { db, doc, setDoc, deleteDoc }`.

## Écran de saisie

### Champs
- Poids / Reps / ✓ par série, avec bouton ⇊ de recopie à partir de la série 2.
- ⚠️ **Champs numériques en `type="text"` + `inputMode`**, jamais `type="number"` : avec un clavier français, « 22,5 » est jugé invalide par Safari et `input.value` renvoie une chaîne vide — la saisie disparaissait silencieusement. `sanitizeField()` filtre à la frappe ; **`parseNum()` (virgule → point) pour tout calcul**, jamais `parseFloat`.
- Note « 🗒️ Info » par exercice, sélecteur de variante si `equipmentOptions`.

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

- **Cumul** en tête (`getLifetimeStats`) : tonnage total et nombre de séances, corbeille exclue.
- **Sélection** : `progressSelection` vaut un nom d'exercice ou `PROGRESS_TONNAGE_KEY`. L'entrée « Tonnage total de la séance » est en tête de liste, en bordure pointillée — le tonnage est une donnée de séance, pas d'exercice, mais il n'a pas mérité un écran à part.
- **Métrique** (`progressMetric`) : poids max, volume (poids × reps cumulé), reps max. **Masquée sur le tonnage** : proposer « reps max » sur un tonnage n'aurait aucun sens.
- **Période** (`progressPeriod`) : 1 / 3 / 6 mois, ou tout.
- **Écart** (`getProgressDelta`) : gain absolu, pourcentage et contexte, vert / rouge / gris. Rien ne s'affiche sous deux points.
- **Étiquettes de dates** : au-delà de 8 points, une sur N seulement, première et dernière toujours conservées. Sinon elles se chevauchent en bouillie.
- Ligne centrée verticalement quand toutes les valeurs sont identiques.

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

| Fichier | Couvre |
|---|---|
| `test.js` | virgule décimale, undo, échappement, espace bas, builder |
| `test2.js` | archivage hors ligne, export texte |
| `test3.js` | catalogue d'exercices, fautes de frappe, normalisation |
| `test4.js` | navigation (menu, profils, builder, progression) |
| `test5.js` | écran de chargement (minutage, disparition, robustesse) |
| `test6.js` | dernier poids, record personnel, cumul |
| `test7.js` | rappel d'archivage |
| `test8.js` | métrique, période, écart, tonnage, étiquettes |
| `test9.js` | jetons de design, structure des cartes |
| `test10.js` | toasts, validation, 100 %, micro-animations, squelettes |
| `audit.js` | socle de lecture des archives, corbeille |

Méthode : charger le HTML dans **jsdom** (`runScripts:'dangerously'`) et appeler les fonctions globales.

Pièges connus :
- Les `const`/`let` de premier niveau (`storage`, `undoStacks`, `builderDraft`, `currentProfile`, `progressSelection`…) ne sont **pas** exposés sur `window` — y accéder via `window.eval('...')`. Les `function` le sont.
- Le script `type="module"` n'est pas exécuté par jsdom : simuler `window.__fb` à la main, avec des promesses **jamais résolues** pour reproduire le hors-ligne.
- `toLocaleString('fr-FR')` produit une **espace insécable fine** (U+202F), pas une espace ordinaire. Normaliser avant comparaison.
- Penser à poser `window.__archivesLoaded` / `__customSessionsLoaded`, sinon les squelettes remplacent le contenu attendu.
- Lancer avec un `timeout` : un bug de boucle fait geler la suite plutôt qu'échouer.

## Données non stockées côté app

Poids/reps/séries, notes libres, dates. Firestore est en accès ouvert (pas d'authentification) — acceptable entre deux personnes connaissant l'URL, mais c'est le point faible de l'architecture si l'app devait s'ouvrir.

## Pour la suite

Traité : refonte UI/UX, architecture en écrans, variantes, notes, cardio enrichi, undo, archives Firebase, Build Training, graphique de progression, export global, mode hors-ligne, badge de sync, passe complète de correction de bugs, catalogue d'exercices, menu principal, écran de chargement, corbeille, dernier poids, records, cumul, rappel d'archivage, lot progression complet, jetons de design, refonte des cartes, animations et retours d'état.

Abandonné en connaissance de cause :
- **Série en échec** — écarté pour ne pas compliquer le calcul du tonnage et des records.
- **Accent personnalisable** — le bleu et le rose ne sont pas décoratifs, ils indiquent quel profil est actif et distinguent les courbes. Et il n'y a pas d'écran de réglages où le loger.

Pistes évoquées, non faites :
- **Fusion de deux noms d'exercice déjà archivés.** Le catalogue protège les futures saisies, mais deux orthographes déjà en archive restent deux courbes (le nom est figé dans l'archive). Il faudrait réécrire les documents archivés.
- Chrono de repos, boutons +/- de charge, bandeau « séance en cours », dupliquer une séance, bibliothèque d'exercices, comparer Corentin et Lisa sur un même graphe, calendrier des séances, recherche dans les archives, export CSV, partage iOS natif, installation en PWA, sauvegarde JSON, authentification Firebase.
