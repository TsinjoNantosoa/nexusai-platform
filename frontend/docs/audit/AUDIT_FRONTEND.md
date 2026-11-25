# NexusAI — audit frontend Phase 0

Chaque constat ci-dessous comporte une preuve locale, un risque, une correction proposée et un critère d’acceptation. Aucune correction de code n’est appliquée dans cette phase.

## AUD-01 — Assets de personnages absents

- **Sévérité :** Élevée.
- **Preuve :** `src/assets/atlas.asset.json:5`, `echo.asset.json:5`, `luna.asset.json:5` et `nova.asset.json:5` référencent quatre URLs `/__l5e/assets-v1/`; `src/assets/` ne contient aucun `.webp`; `src/lib/characters.ts:1-18` consomme ces URLs.
- **Comportement actuel :** les cartes utilisent des pointeurs d’assets Lovable au lieu de fichiers livrés localement. Le parcours Chromium local a compté les quatre cartes, mais n’a pas certifié la présence des pixels.
- **Risque :** portraits cassés ou dépendance externe après export, publication indépendante ou suppression du projet Lovable.
- **Correction recommandée :** récupérer les originaux par les `asset_id` et `project_id` auprès de l’archive/propriétaire; vérifier dimensions, type, checksum et licence; conserver les designs; ne remplacer aucune image sans approbation.
- **Critères d’acceptation :** quatre fichiers `.webp` approuvés sont livrés localement, les quatre `naturalWidth` sont positifs sur un build indépendant, aucune URL `/__l5e/` ne subsiste dans le bundle d’images et les routes accueil/explore/profil restent visuellement inchangées.
- **Priorité :** P1.

## AUD-02 — Couplage Lovable et chaîne TanStack Start

- **Sévérité :** Moyenne à élevée.
- **Preuve :** `vite.config.ts:10` importe `@lovable.dev/vite-tanstack-config`; `package.json:81` le déclare; `bunfig.toml:5-7`, `AGENTS.md:1-30`, `.lovable/` et `src/lib/lovable-error-reporting.ts` contiennent des éléments de plateforme. `package.json` inclut également `@tanstack/react-start`, `nitro` et `@tanstack/router-plugin`.
- **Comportement actuel :** le build est piloté par une configuration Lovable qui injecte plugins, détection sandbox et cible Nitro Cloudflare; le routeur reste TanStack Start/Router.
- **Risque :** reproductibilité et portabilité vers un déploiement indépendant limitées; des hypothèses de runtime peuvent se révéler incompatibles avec FastAPI.
- **Correction recommandée :** ne pas migrer pendant Phase 0. Pour la cible indépendante, préférer à terme une SPA Vite + TanStack Router si le SSR n’apporte pas de besoin produit; sinon expliciter et tester le contrat SSR. Retirer les dépendances Lovable uniquement lors d’une migration approuvée.
- **Critères d’acceptation :** un build indépendant documenté fonctionne sans configuration Lovable implicite, le choix Start/SPA est approuvé, et les 13 routes conservent leurs URLs et leur identité visuelle.
- **Priorité :** P1.

## AUD-03 — Reproductibilité Bun non déclarée comme prérequis unique

- **Sévérité :** Faible.
- **Preuve :** `bun.lock` est présent; `package.json` ne définit pas de champ `packageManager`; `README.md:7-18` montre des commandes npm puis recommande Bun pour le lockfile; `bunfig.toml:1-7` fixe une garde d’âge des paquets.
- **Comportement actuel :** Bun 1.4.4 installe proprement avec `bun install --frozen-lockfile`; `node_modules` était absent avant l’installation; aucun `package-lock.json` n’existe.
- **Risque :** un contributeur utilisant npm peut produire une résolution différente ou croire que le lockfile est npm-compatible.
- **Correction recommandée :** documenter Bun comme gestionnaire supporté et ajouter une vérification CI de version; conserver le lockfile existant; ne pas régénérer les versions automatiquement.
- **Critères d’acceptation :** CI exécute `bun install --frozen-lockfile`, la version Bun supportée est documentée, et l’absence de `package-lock.json` est intentionnelle.
- **Priorité :** P2.

## AUD-04 — Vulnérabilités transitives modérées

- **Sévérité :** Moyenne.
- **Preuve :** `bun audit` et `npm audit` identifient `glob@11.1.0` via `vite-plugin-pwa > workbox-build > glob`, advisory `GHSA-3g3m-2fjr-6pw4`, plage `>=9.0.0 <=14.0.1`, CWE-400; ils identifient aussi `minimatch` via Workbox, advisory `GHSA-g3hv-75wg-m249`, plage `>=7.0.0 <11.0.1`, CWE-405. `bun pm why` confirme `workbox-build@7.4.1` et `vite-plugin-pwa@2.0.0`.
- **Comportement actuel :** l’audit retourne deux vulnérabilités modérées et le code de sortie 1. La chaîne est principalement de build/dev, pas un appel applicatif runtime démontré.
- **Risque :** traversée filesystem post-timeout ou amplification de glob dans les outils de build si une entrée non fiable atteint ces utilitaires.
- **Correction recommandée :** comparer une version compatible de `vite-plugin-pwa`/Workbox avec le build TanStack; tester la génération worker; ne pas lancer `bun audit fix --latest` ni modifier toutes les dépendances sans analyse.
- **Critères d’acceptation :** les advisories sont absents ou couverts par une justification documentée, le lockfile est régénéré volontairement et lint/typecheck/test/build restent verts.
- **Priorité :** P1.

## AUD-05 — Règles `.env` incomplètes et index Git indisponible

- **Sévérité :** Moyenne.
- **Preuve :** `.gitignore:1-31` exclut logs, builds et `*.local`, mais pas `.env` ou `.env.*`; seul `.env.example` a été trouvé; la recherche locale de marqueurs de secrets n’a rien trouvé. Aucun index Git n’est disponible pour vérifier les fichiers suivis.
- **Comportement actuel :** l’exemple ne contient que deux variables publiques `VITE_*`; aucune valeur secrète n’a été affichée ou détectée.
- **Risque :** une future copie `.env`, clé Stripe ou secret backend peut être ajoutée accidentellement au dépôt; `VITE_*` serait exposé au bundle navigateur.
- **Correction recommandée :** proposer des règles `.env`, `.env.*` avec exception `.env.example`; rappeler que les secrets serveur restent hors frontend; faire une vérification Gitleaks dans un dépôt Git réel.
- **Critères d’acceptation :** les fichiers secrets sont ignorés, `.env.example` reste suivi/documenté, aucun secret n’est présent dans le bundle et le scan CI est vert.
- **Priorité :** P1.

## AUD-06 — Service worker volontairement désactivé en local

- **Sévérité :** Moyenne.
- **Preuve :** `src/lib/offline.ts:22-26` refuse toute registration hors production, sur localhost, iframe, preview Lovable ou `?sw=off`; `src/lib/offline.ts:28-47` supprime les registrations/caches publics refusés.
- **Comportement actuel :** les parcours dev ont `0` service worker enregistré; le test local PWA classique est donc impossible sur `localhost`.
- **Risque :** régression PWA non détectée avant publication; confusion entre le comportement dev et le comportement production.
- **Correction recommandée :** conserver le refus en dev et l’absence de cache privé; permettre un opt-in explicite dans un serveur de preview de production contrôlé, ou documenter une URL/hostname de preview dédié. Ne jamais mettre en cache auth, conversations, portefeuille ou réponses financières.
- **Critères d’acceptation :** dev reste sans worker, preview de production opt-in enregistre le worker, `?sw=off` désactive et nettoie les caches, et une inspection prouve l’absence de données privées dans les caches.
- **Priorité :** P1.

## AUD-07 — `autoUpdate` incompatible avec les opérations actives et sortie worker incomplète

- **Sévérité :** Élevée.
- **Preuve :** `vite.config.ts:19` utilise `registerType: "autoUpdate"`; le worker généré `dist/sw.js` contient `skipWaiting()` et `clientsClaim()`; `src/lib/offline.ts:52-67` n’empêche la prise de contrôle qu’au clic de l’utilisateur si `data-operation-active="true"`. Après `bun run build`, `dist/sw.js` existe mais `.output/public/sw.js` et `.output/public/workbox-*.js` sont absents.
- **Comportement actuel :** la configuration peut activer une nouvelle version pendant un checkout ou une génération; les warnings Workbox indiquent aussi des glob patterns sans correspondance dans `dist`.
- **Risque :** rechargement ou changement de worker pendant une opération financière/IA; en production Nitro, le worker peut ne pas être publié du tout.
- **Correction recommandée :** choisir une politique d’activation différée, intégrer un verrou d’opération réellement partagé avec le worker et corriger le pipeline de copie/publication; vérifier le worker émis dans l’artefact déployable.
- **Critères d’acceptation :** une mise à jour ne prend pas le contrôle pendant checkout/génération, le refresh reste explicite après opération, `.output/public/sw.js` et Workbox sont présents dans l’artefact final, et les warnings de précache sont compris ou supprimés.
- **Priorité :** P1.

## AUD-08 — Base API relative et cookies non résolus en SSR

- **Sévérité :** Élevée.
- **Preuve :** `src/services/api.ts:13-16` construit le client serveur avec `/api/v1`; `src/services/http.ts:22-40` appelle `fetch(this.base + path)` avec `credentials: "include"`; `src/routeTree.gen.ts:321` active SSR; les loaders publics de `src/routes/index.tsx:7-11`, `explore.tsx:6-7` et `pricing.tsx:5-6` appellent `getApi()`.
- **Comportement actuel :** en mode API, un loader SSR peut tenter un `fetch` relatif sans origin de requête et sans retransmettre explicitement le cookie entrant. `credentials: include` ne fabrique pas cette transmission côté serveur.
- **Risque :** échec SSR, session absente, divergence hydratation ou fuite de données si un état serveur est partagé incorrectement.
- **Correction recommandée :** soit rendre l’origin API absolue côté serveur et transmettre explicitement les headers de cookie depuis le contexte de requête, soit désactiver SSR pour les loaders dépendants de l’API et garder une navigation client. Un reverse proxy même origine reste recommandé.
- **Critères d’acceptation :** chaque route publique rend en mode API avec et sans session, les cookies sont isolés par requête, l’hydratation est stable et aucune donnée d’un utilisateur apparaît dans une autre réponse SSR.
- **Priorité :** P0.

## AUD-09 — Contrat CSRF incomplet

- **Sévérité :** Élevée.
- **Preuve :** `src/services/http.ts:18-25` expose `setCsrfToken` et envoie `X-CSRF-Token` seulement si le token existe; aucune acquisition ou rotation n’est implémentée; `src/start.ts:23-25` protège uniquement les server functions TanStack.
- **Comportement actuel :** login, register, checkout, conversations, reports et autres mutations peuvent partir sans token client si le backend l’exige.
- **Risque :** intégration FastAPI bloquée ou mutations refusées; implémentation ad hoc risquant une protection CSRF incomplète.
- **Correction recommandée :** approuver un endpoint/ cookie de bootstrap CSRF, définir quand le token est lu, stocké seulement en mémoire, renouvelé après login/rotation/logout et envoyé sur toutes les mutations, y compris SSE POST.
- **Critères d’acceptation :** contrat OpenAPI documenté, tests 401/403/rotation, aucune session en storage navigateur et mutations sans token refusées côté serveur.
- **Priorité :** P0.

## AUD-10 — Mode mock explicite visuellement mais permissif par défaut

- **Sévérité :** Moyenne à élevée.
- **Preuve :** `src/services/api.ts:4` définit `isMock` par `VITE_DATA_MODE !== "api"`; `src/components/layout/Shell.tsx:63-67` affiche la bannière; `src/features/Auth.tsx:192-213` limite les comptes démo au mock; `src/services/http.ts:120-126,222-245` laisse plusieurs opérations en `integration_pending`.
- **Comportement actuel :** `mock` est affiché et une erreur API ne bascule pas vers le mock, mais toute valeur inconnue, variable absente ou faute de frappe sélectionne silencieusement le mock.
- **Risque :** une recette censée utiliser FastAPI peut tester des comptes et paiements fictifs sans s’en rendre compte; logout efface volontairement les comptes fictifs en mémoire.
- **Correction recommandée :** valider strictement `mock|api`; refuser les valeurs inconnues; afficher le mode actif dans l’environnement de recette; conserver l’absence de fallback après panne API.
- **Critères d’acceptation :** `api` en panne expose une erreur visible sans données mock, `mock` est clairement marqué, une valeur inconnue bloque au démarrage et le logout mock efface seulement l’état fictif documenté.
- **Priorité :** P1.

## AUD-11 — Documentation de statut obsolète

- **Sévérité :** Moyenne.
- **Preuve :** `docs/FRONTEND_IMPLEMENTATION_STATUS.md:13-25` référence `src/features/auth/AuthPages.tsx` et `src/hooks/useSession.ts`, absents; le code actuel utilise `src/features/Auth.tsx` et `src/services/hooks.ts`, et implémente des scénarios dans `src/services/mock.ts`.
- **Comportement actuel :** le rapport historique décrit plusieurs écrans comme placeholders/non implémentés alors que le parcours mock actuel les exécute.
- **Risque :** mauvaise décision de planification et passation backend basée sur des chemins ou états faux.
- **Correction recommandée :** conserver le rapport historique intact et maintenir une matrice corrigée basée sur les chemins présents, en distinguant mock exécuté, HTTP préparé et backend non validé.
- **Critères d’acceptation :** la matrice pointe uniquement vers des fichiers existants, chaque exigence indique son niveau de preuve et le rapport historique n’est pas écrasé.
- **Priorité :** P2.

## AUD-12 — Télémétrie et instructions Lovable résiduelles

- **Sévérité :** Moyenne.
- **Preuve :** `AGENTS.md:1-30` impose des règles Lovable et mentionne gateway/connecteurs/secrets; `src/lib/lovable-error-reporting.ts:27-50` appelle conditionnellement `window.__lovableEvents` et `window.__lovableReportRuntimeError`; `src/routes/__root.tsx:14,46` l’utilise; `.lovable/` contient métadonnées et plan de migration.
- **Comportement actuel :** aucun appel n’est effectué si les hooks globaux n’existent pas, mais l’application indépendante conserve une intégration et des instructions propres à Lovable.
- **Risque :** télémétrie externe non attendue en preview intégrée; ambiguïté de gouvernance et contradiction avec une architecture FastAPI indépendante. Les protections d’historique Git restent utiles et ne doivent pas être supprimées.
- **Correction recommandée :** inventorier puis isoler ou supprimer l’adaptateur telemetry lors d’une approbation; remplacer les instructions de plateforme par celles du projet en conservant l’interdiction force-push/rewrite; ne pas introduire Supabase ou gateway IA.
- **Critères d’acceptation :** aucune télémétrie externe n’est requise pour le build indépendant, les appels optionnels sont documentés, les secrets ne passent jamais au navigateur et les garde-fous Git sont préservés.
- **Priorité :** P2.

