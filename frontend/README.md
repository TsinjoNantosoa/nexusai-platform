# NexusAI

Frontend PWA de portfolio : personnages IA, conversations, mémoire, portefeuille et facturation **simulée**. Le cahier des charges V1.0 reste dans `docs/CAHIER_DES_CHARGES.md`.

## Démarrer

```sh
bun install --frozen-lockfile
bun run dev
bun run test
bun run lint
bun run typecheck
bun run build
```

Le projet est une SPA Vite indépendante avec TanStack Router, TanStack Query, React 19, Tailwind 4, shadcn/ui, i18next et `vite-plugin-pwa`. Le serveur de développement écoute par défaut sur le port Vite standard; utiliser `--host 127.0.0.1 --port 8080` pour les scripts Chromium existants.

Pour un backend local, le proxy `/api` cible `http://127.0.0.1:8000` par défaut. Remplacer la cible avec `API_PROXY_TARGET`; le mock ne nécessite aucun backend.

## Démonstration

Depuis Connexion, choisir « Compte de démonstration » ou « Démo administrateur ». Les données restent en mémoire et sont perdues au rechargement. Aucun mot de passe réel, aucune carte bancaire et aucune donnée sensible. Le mock n’est pas une authentification sécurisée.

20 gemmes initiales. Starter 2,99 €/100 ; Plus 9,99 €/500 ; Premium 19,99 €/mois et 1500 par période payée. Les scénarios succès/pending/refus/doublon/annulation, renouvellement/échec/résiliation et restitution IA sont simulés.

Routes : `/`, `/login`, `/register`, `/explore`, `/characters/:id`, `/conversations`, `/chat/:id`, `/wallet`, `/pricing`, `/billing/success`, `/billing/cancel`, `/settings`, `/admin`.

## Modes et PWA

`VITE_DATA_MODE=mock` est le mode démonstration; `VITE_DATA_MODE=api` utilise le backend sous `/api/v1`. Toute autre valeur provoque une erreur de configuration. Aucun fallback mock n’existe après une panne API.

Le worker est généré seulement par `bun run build` et n’est pas activé en développement. Pour tester localement le worker de production :

```sh
bun run build
bun run preview -- --host 127.0.0.1
# ouvrir http://127.0.0.1:4173/?sw=on
```

Le serveur de publication doit réécrire les routes SPA vers `index.html`. Le service worker ne cache que les ressources statiques approuvées et la navigation publique `/`; les données privées et opérations payantes restent réseau uniquement.

## Intégration future

FastAPI doit fournir les sessions cookie, CSRF, RBAC, catalogue, portefeuille, Checkout Stripe, webhooks, SSE IA, mémoire, modération, export et suppression. Le frontend envoie `credentials: include` et le SKU/idempotency key, mais ne crédite jamais un portefeuille réel. Voir `docs/API_CONTRACT.md` et `docs/BACKEND_INTEGRATION_HANDOVER.md`.

## Tests

Les tests Vitest couvrent les règles mock financières et conversationnelles. Les parcours Chromium couvrent la connexion démo, achat Starter, doublon, chat, restitution, hors ligne, responsive et logout. Stripe, PostgreSQL, sécurité serveur et appareils réels restent des recettes backend/production.
