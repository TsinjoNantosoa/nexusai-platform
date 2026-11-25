# NexusAI

Frontend de portfolio : personnages IA, conversations, mémoire, portefeuille et facturation **simulée**. Cahier des charges V1.0 conservé dans docs/CAHIER_DES_CHARGES.md.

## Démarrer

```sh
npm install
npm run dev
npm run test
npm run lint
npm run typecheck
npm run build
```

Lockfile : bun.lock ; pour une installation verrouillée utiliser `bun install --frozen-lockfile`.

React 19 / TypeScript strict / Vite / TanStack Start et Router (adaptation approuvée) / TanStack Query / Tailwind 4 / shadcn / i18next / React Hook Form / Zod / vite-plugin-pwa / Vitest.

## Démonstration

Depuis Connexion, choisissez « Compte de démonstration » ou « Démo administrateur ». Les données restent en mémoire et sont perdues au rechargement. Aucun mot de passe réel, aucune carte bancaire et aucune donnée sensible. Le mock n’est pas une authentification sécurisée.

20 gemmes initiales. Starter 2,99 €/100 ; Plus 9,99 €/500 ; Premium 19,99 €/mois et 1500 par période payée. Scénarios succès/pending/refus/doublon/annulation ; abonnement renouvelé/échoué/résilié ; chat simulé 2 gemmes avec restitution sur erreur.

Routes : /, /login, /register, /explore, /characters/:id, /conversations, /chat/:id, /wallet, /pricing, /billing/success, /billing/cancel, /settings, /admin.

## Intégration future

VITE_DATA_MODE=mock par défaut ; VITE_DATA_MODE=api utilise VITE_API_BASE_URL=/api/v1 sans fallback. Backend Python/FastAPI séparé ; aucun Cloud, aucune DB, aucun Stripe/IA réel. Contrats mémoire/blocage/admin/export/suppression restent à approuver. PWA publiée et appareil réel non vérifiés. Aucune publication réalisée.

Consulter docs/FRONTEND_ARCHITECTURE.md, docs/API_CONTRACT.md, docs/FRONTEND_IMPLEMENTATION_STATUS.md, docs/FRONTEND_TEST_REPORT.md et docs/BACKEND_INTEGRATION_HANDOVER.md.

## Tests

33 tests Vitest réussis et parcours Chromium financier/chat/mobile vérifiés. Le lint global n’est pas validé (timeout) ; voir le rapport. Tests Stripe/DB/sécurité serveur et recette réelle T01–T18 restent externes. `npm run test:e2e` nécessite Python Playwright et serveur localhost:8080.
