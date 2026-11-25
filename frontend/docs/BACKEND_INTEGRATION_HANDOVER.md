# Passation backend NexusAI

## Exécution locale

Node.js récent et npm sont nécessaires. Depuis la racine :

```sh
npm install
npm run dev
npm run test
npm run lint
npm run typecheck
npm run build
```

Le lockfile installé est `bun.lock` (reproduction exacte : `bun install --frozen-lockfile`). Le projet n’exige pas un compte Bolt pour ses services mock. Le pipeline Vite utilise la configuration TanStack de ce projet Lovable, pas le bootstrap React Router de l’archive. Cette adaptation a été approuvée.

`.env.example` ne contient que les deux valeurs publiques. Mock par défaut. Pour FastAPI, définir VITE_DATA_MODE=api et VITE_API_BASE_URL ; utiliser un reverse proxy même origine. Aligner les schémas JSON/pagination du client HTTP avec l’OpenAPI final. Ne jamais placer Stripe/OpenAI ou des secrets serveur dans VITE_*.

## Sessions, CSRF et paiement

FastAPI réalise les sessions HttpOnly/Secure, rotation, révocation, CSRF et RBAC. Le frontend utilise credentials include. Contracter l’acquisition du jeton CSRF, puis appeler setCsrfToken en mémoire. Auth côté client n’est qu’une garde UX. Aucun backend ou fournisseur alternatif n’a été provisionné.

Backend Checkout : SKU et clé idempotente → URL Stripe et commande. Webhooks, signature, factures, journal financier, refunds et réconciliation restent Python/PostgreSQL. Le retour UI observe seulement la commande. Customer Portal reste backend-owned. Aucune carte n’est collectée et aucun secret n’est demandé.

## SSE et opérations manquantes

Voir API_CONTRACT.md pour l’enveloppe SSE proposée et les contrats encore à approuver. Ajouter endpoints mémoire/reset/block, commandes paginées, export/suppression, administration catalogue et modération. La restitution réelle ne doit jamais être déclenchée arbitrairement par le frontend.

## PWA et recette externe

Manifest-only en preview, worker généré seulement pour publication, registration refusée en preview/dev/iframe. Vérifier le worker émis par le pipeline déployé, les exclusions du cache, les mises à jour pendant opération active, l’installation Chrome/Edge/Android et iOS, le retour réseau et le mode hors ligne publié. Aucun appareil réel n’a été testé.

Les tests Stripe, PostgreSQL/concurrence, CSRF/RBAC, remboursement R08, backup/restore, CI/infrastructure et T01–T18 réels restent à exécuter. Le service mock ne les valide pas. L’application n’a pas été publiée.

Tests navigateur locaux : installer Python Playwright dans votre environnement et Chromium, puis `npm run test:e2e` avec le serveur démarré sur localhost:8080. Les captures sont temporaires sous /tmp/browser/nexus.
