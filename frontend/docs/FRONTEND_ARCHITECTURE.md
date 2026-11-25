# Architecture frontend NexusAI

## Runtime

NexusAI est une SPA Vite indépendante : React 19, TypeScript strict, TanStack Router file-based, TanStack Query, Tailwind 4 et composants shadcn. `index.html` monte `src/main.tsx`, qui crée un router navigateur et un `QueryClient` par application. Le build ne dépend plus de TanStack Start, Nitro ou d’une configuration Lovable.

Le serveur de publication doit fournir un fallback SPA vers `index.html` pour les treize routes. Le proxy Vite local transmet `/api` vers FastAPI mais n’est jamais nécessaire en mode mock.

## Routes et données

Les fichiers `src/routes` conservent les URLs existantes. `src/services/types.ts` définit `ApiClient`; `src/services/mock.ts` fournit une démonstration strictement en mémoire; `src/services/http.ts` parle au futur backend via cookies `credentials: include`. `src/services/config.ts` n’autorise que `mock` et `api`, sans fallback automatique.

Les loaders catalogue/offres restent des loaders TanStack Router côté navigateur; ils ne font plus de SSR. Le portefeuille, les produits, l’authentification, l’administration et les paiements en mode API sont donc autoritaires côté FastAPI.

## PWA

`vite-plugin-pwa` utilise `generateSW` et `registerType: "prompt"`. Le worker n’est pas activé en développement. Un preview de production local peut l’activer explicitement avec `?sw=on`; les hosts Lovable, les iframes et `?sw=off` restent refusés.

Le precache contient uniquement les ressources statiques générées, icônes et `offline.html`. Le runtime cache ne couvre que la navigation publique `/`. Les API, sessions, conversations, profils privés, wallet, billing, webhooks et vérifications de paiement ne sont pas cachés. Une mise à jour attend l’approbation utilisateur et l’absence d’opération marquée active.

## Sécurité

Les tokens et sessions ne sont pas persistés dans `localStorage` ou `sessionStorage`. Le token CSRF est prévu en mémoire par `HttpApiClient.setCsrfToken`; son acquisition/rotation doit être finalisée avec FastAPI. Le frontend ne contient aucun secret Stripe/IA et ne simule jamais une mutation financière en mode API.
