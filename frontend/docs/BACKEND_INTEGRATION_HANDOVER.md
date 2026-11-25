# Passation backend NexusAI

## Exécution frontend

```sh
bun install --frozen-lockfile
bun run dev
bun run test
bun run lint
bun run typecheck
bun run build
```

Le frontend est une SPA Vite autonome. Le proxy de développement `/api` cible `http://127.0.0.1:8000`, configurable par `API_PROXY_TARGET`. Pour FastAPI, exposer un reverse proxy même origine et définir `VITE_DATA_MODE=api`; ne jamais mettre de secret dans `VITE_*`.

## Sessions et CSRF

FastAPI doit fournir session opaque HttpOnly/Secure, rotation, révocation, SameSite approprié et RBAC. Le client utilise `credentials: include` et n’enregistre aucune session dans le stockage navigateur.

Contrat CSRF proposé, à approuver avant Phase 2 :

1. un endpoint public de bootstrap renvoie un token lié à la session ou un cookie CSRF lisible par le frontend;
2. le frontend conserve le token uniquement en mémoire et l’envoie dans `X-CSRF-Token` sur chaque mutation, y compris le POST SSE;
3. login, rotation de session, expiration et logout renouvellent ou effacent le token;
4. un 403 CSRF est distingué d’un 401 session expirée et ne déclenche jamais un retry financier automatique.

Le frontend prépare `setCsrfToken`; l’endpoint, le format, la rotation et les codes d’erreur restent des décisions backend.

## Paiement et IA

Checkout reçoit uniquement le SKU et une clé `Idempotency-Key`; les prix, crédits et commandes proviennent du serveur. Stripe Checkout, Customer Portal, signatures webhook, factures, refunds, ledger et réconciliation restent Python/PostgreSQL. Le retour UI observe la commande et ne crédite jamais le portefeuille.

Le POST SSE doit émettre des frames `delta`, `done` et `error`. Le client accepte plusieurs événements par chunk, frames fragmentées, UTF-8 fragmenté et interruption; aucun retry payant automatique n’est effectué.

## PWA et recette

Le worker est généré dans `dist/sw.js` par `bun run build`. Le preview local contrôlé est `/?sw=on`; le développement normal reste sans worker. Vérifier en publication le fallback SPA, l’installation, le cache uniquement public, l’absence de données privées et l’approbation des mises à jour pendant checkout/génération.

## Hors périmètre frontend

OpenAPI final, sessions/CSRF/RBAC serveur, PostgreSQL/concurrence, Stripe Sandbox/webhooks, fournisseur IA, refunds R08, modération production, export/suppression, backup/restore, CI/infrastructure et recettes T01–T18 réelles restent à exécuter.
