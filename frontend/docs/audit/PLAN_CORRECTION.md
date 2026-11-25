# NexusAI — plan de correction après baseline

Ce plan est une recommandation de Phase 0. Il ne lance aucune migration et nécessite l’approbation du propriétaire avant toute modification de source, lockfile ou architecture.

## Décisions à obtenir

1. Autoriser la récupération des quatre assets originaux sans redessiner les personnages.
2. Choisir le gestionnaire officiel : Bun avec `bun install --frozen-lockfile`.
3. Approuver la stratégie API/SSR : SPA Vite recommandée pour un backend FastAPI séparé, ou maintien de TanStack Start avec contrat SSR explicite.
4. Approuver la politique PWA de preview et de mise à jour différée.
5. Finaliser le contrat CSRF, pagination, mémoire, export/suppression, refunds et administration avant backend.
6. Décider le traitement de la télémétrie Lovable et du dépôt Git absent.

## Architecture recommandée

Pour l’application indépendante finale, la cible la plus simple est une SPA Vite + TanStack Router + TanStack Query, servie par un reverse proxy même origine vers FastAPI. Elle évite que les loaders publics tentent de faire des `fetch` relatifs côté SSR et simplifie la propagation des cookies.

TanStack Start peut être conservé temporairement pour préserver le frontend actuel et son identité. Dans ce cas, il faut fournir une origin API serveur, transmettre les cookies de la requête au client HTTP par requête, garantir l’isolation du `QueryClient` et tester l’hydratation. Aucun choix ne doit modifier les URLs des 13 routes.

Organisation cible proposée, sans déplacement en Phase 0 :

```text
nexusai-platform/
├── frontend/
├── backend/
├── infrastructure/
├── docs/
├── .github/workflows/
├── compose.yaml
├── AGENTS.md
└── README.md
```

## Priorités

### P0 — bloquant intégration

- Contracter la résolution API SSR et la transmission de cookies, ou approuver la migration SPA.
- Contracter CSRF : bootstrap, rotation, stockage mémoire, mutations protégées, erreurs et tests.
- Ne pas commencer Stripe, PostgreSQL ou IA réelle avant validation des contrats et de l’autorité serveur.

### P1 — démonstration indépendante et sécurité

- Récupérer les portraits originaux et supprimer la dépendance runtime aux URLs Lovable.
- Corriger la sortie du service worker dans l’artefact Nitro et définir une activation différée pendant checkout/génération.
- Décider une version compatible de `vite-plugin-pwa`/Workbox pour les deux advisories, puis régénérer le lockfile volontairement.
- Ajouter les règles `.env` et un scan de secrets en CI dans un vrai dépôt Git.
- Valider strictement `VITE_DATA_MODE` et conserver l’absence de fallback mock en mode API.

### P2 — portabilité et documentation

- Remplacer la matrice historique obsolète par la traçabilité corrigée sans écraser le rapport de tests historique.
- Isoler la télémétrie Lovable et remplacer les instructions de plateforme par les règles du projet, tout en gardant l’interdiction de réécriture Git.
- Documenter Bun, les versions d’outils et le protocole de preview PWA.

### P3 — qualité ultérieure

- Certification accessibilité, performance, appareils réels, installation iOS/Android et backup/restore.
- Durcir les tests de route, erreurs, pagination, reconnexion et mises à jour offline après disponibilité du backend.

## Plan de récupération des assets

1. Obtenir les quatre fichiers source depuis l’archive Lovable ou le propriétaire, avec les IDs des descripteurs : Atlas `5329dedf-3ced-4f14-8c91-a20ad4dff447`, Echo `c18777e6-8247-4dd8-9fd8-504888ab911a`, Luna `8565b9a8-39d0-4593-aa4b-8a036c344d3b`, Nova `34e2ca90-3de8-46c8-b2fe-7c8dfab08975`.
2. Vérifier type WebP, dimensions, checksum, licence et absence de données cachées.
3. Après approbation seulement, livrer les fichiers dans un emplacement local stable et mettre à jour les pointeurs.
4. Vérifier les quatre portraits sur les routes `/`, `/explore` et `/characters/:id` en build de production.

## Prochaine phase proposée

Phase 1 doit commencer par la décision architecture/API et les contrats CSRF/session, puis par la récupération des assets et la correction PWA. Le backend FastAPI/PostgreSQL, Stripe Sandbox et les fournisseurs IA restent explicitement hors de Phase 0.

