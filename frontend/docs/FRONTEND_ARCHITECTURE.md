# Architecture frontend NexusAI

React 19, TypeScript strict, Vite et TanStack Start/Router (adaptation approuvée), Tailwind 4 et composants shadcn. Les versions TanStack du projet cible sont conservées. Les treize routes sont des fichiers dans `src/routes`; chaque page possède ses métadonnées. Le shell partagé et la bannière de démonstration entourent l’Outlet racine.

`src/services/types.ts` définit l’interface ApiClient. `mock.ts` fournit la démonstration en mémoire ; `http.ts` utilise les cookies du futur FastAPI avec credentials include. `api.ts` choisit explicitement le mode et évite de partager les comptes mock entre requêtes SSR. Aucun fallback mock en mode API. TanStack Query gère l’état et l’invalidation.

Le service mock possède un ledger signé, des références uniques, une commande idempotente et une réservation IA suivie d’une compensation sur échec. Ce n’est pas une preuve d’atomicité PostgreSQL. Les mots de passe de démonstration ne sont pas persistés ni utilisés comme authentification sécurisée ; les comptes fictifs ne constituent pas une architecture de production.

Français par défaut, anglais via i18next. Couleurs et dimensions dans `src/styles.css`. Portraits originaux générés, optimisés WebP et référencés par des pointeurs d’assets.

PWA : manifest et icônes ; vite-plugin-pwa generateSW, registration unique gardée dans `src/lib/offline.ts`. Pas de registration dans preview/dev/iframe. La navigation publique `/` utilise NetworkFirst ; seules ressources statiques publiques permises sont précachées. API privées, contenu des conversations, wallet et pages auth/billing ne sont pas cachés. Le comportement publié reste à vérifier. Aucun cache privé TanStack persistant.
