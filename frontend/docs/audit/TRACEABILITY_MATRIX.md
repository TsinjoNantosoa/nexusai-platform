# NexusAI — matrice de traçabilité corrigée

Cette matrice remplace seulement la lecture opérationnelle de l’ancien statut; `docs/FRONTEND_TEST_REPORT.md` reste historique et inchangé.

## Exigences fonctionnelles

| ID | Sources actuelles | État prouvé en Phase 0 | Limite / suite |
|---|---|---|---|
| F01 | `src/features/Auth.tsx`, `src/services/mock.ts:110-129` | Mock exécuté : inscription, validation, login démo, logout | Auth réelle, email et session FastAPI non validés |
| F02 | `src/services/hooks.ts`, `src/components/shared.tsx`, `src/components/layout/Shell.tsx` | Garde UX et session mock | Profil isolé, cookies, rotation et révocation backend à faire |
| F03 | `src/features/Billing.tsx`, `src/services/mock.ts:20-38`, `src/services/http.ts:71-73` | Catalogue mock et transport HTTP préparé | Prix et crédits autoritaires serveur à valider |
| F04 | `src/features/Billing.tsx`, `src/routes/billing.success.tsx`, `src/services/mock.ts:157-208` | Parcours simulé et retours exécutés | Stripe Checkout/webhooks/factures non connectés |
| F05 | `src/features/Billing.tsx`, `src/services/mock.ts:210-225` | Premium/renewal/fail/cancel mock testés | Customer Portal, factures et synchronisation backend manquants |
| F06 | `src/features/Billing.tsx`, `src/services/mock.ts:75-86,151-155` | Solde et ledger mock cohérents | Persistance, pagination et concurrence SQL manquantes |
| F07 | `src/lib/characters.ts`, `src/features/Discovery.tsx`, `src/routes/characters.$id.tsx` | Quatre personnages et navigation Chromium | Fichiers portraits locaux absents (AUD-01) |
| F08 | `src/features/Conversations.tsx`, `src/services/mock.ts:226-336`, `src/services/http.ts:146-220` | Chat progressif mock et parser SSE préparé | Fournisseur IA, persistance et propriété serveur non validés |
| F09 | `src/services/mock.ts:337-349`, `src/features/Conversations.tsx` | Toggle/clear/reset mock présents | Contrats mémoire et score serveur à finaliser |
| F10 | `src/services/mock.ts:270-335`, `src/services/chat.test.ts` | Réservation/restitution mock exécutées | Atomicité, retry, timeout et réconciliation backend manquants |
| F11 | `vite.config.ts`, `src/lib/offline.ts`, `public/manifest.webmanifest` | Manifest, offline page et worker généré; dev sans worker | Worker absent de `.output/public`, appareils réels non testés |
| F12 | `src/features/Discovery.tsx`, `src/features/Settings.tsx`, `src/services/mock.ts:351-380` | Signalement/blocage/admin mock testés | RBAC et modération serveur non validés |
| F13 | `src/features/Settings.tsx`, `src/services/http.ts:243-245` | Interface de réglages présente | Endpoints export/suppression non approuvés; aucun faux succès acceptable |
| F14 | Aucun code dédié | Hors périmètre P2 | À replanifier après V1 |

## Règles financières et sécurité

| ID | Source / preuve | État |
|---|---|---|
| R01 | `src/services/mock.ts:75-86`, `src/services/types.ts:23-35` | Invariant mock seulement |
| R02 | `src/services/mock.ts:75-86` | Ledger append-only simulé; dates et références présentes |
| R03 | `src/services/http.ts:101-111` | SKU + `Idempotency-Key`; prix non autoritaire côté client |
| R04 | `src/services/mock.ts:157-176,185-208` | Idempotence mock; concurrence serveur non prouvée |
| R05 | `src/services/mock.ts:272-286` | Une génération active mock; aucune transaction SQL |
| R06 | `src/services/mock.ts:284-332` | Débit/restauration mock; réconciliation réelle absente |
| R07 | `src/features/Conversations.tsx`, `src/services/http.ts:219` | Pas de retry payant automatique démontré; backend à contracter |
| R08 | `src/services/types.ts:65`, `src/features/Billing.tsx` | États de revue présents; formule refund non définie |
| S01 | `src/services/http.ts:28,163`, `docs/API_CONTRACT.md` | Cookies prévus; Hash/rotation backend non validés |
| S02 | `src/start.ts:23-25`, `src/services/http.ts:18-25` | CSRF et RBAC incomplets (AUD-09) |
| S03 | `.env.example`, `.gitignore` | Configuration publique correcte; ignore rules à renforcer |
| S04 | `src/features/Auth.tsx`, `src/services/mock.ts:281-283` | Validation UI/mock; Pydantic/payload serveur non validés |
| S05 | `src/services/http.ts:101-111` | Aucun webhook côté UI; signature/atomicité backend non testées |
| S06 | `src/services/hooks.ts`, `src/services/mock.ts` | Garde UX; rate limiting et coût serveur absents |
| S07 | `vite.config.ts`, `package.json` | Infrastructure hors périmètre et non validée |
| S08 | `src/lib/offline.ts:27-47`, `src/services/api.ts` | Pas de cache privé déclaré; publication worker à corriger |

## Recette T01–T18

| Tests | Statut Phase 0 |
|---|---|
| T01–T03 | Simulation mock exécutée; Stripe/DB/concurrence non validés |
| T04 | Non exécuté : signature webhook backend |
| T05–T09 | Scénarios mock exécutés; Stripe, factures, réconciliation et serveur non validés |
| T10–T13 | Règles mock exécutées; concurrence, reconnexion, propriété tiers et CSRF serveur non validés |
| T14–T15 | Dev Chromium vérifié; publication, installation et inspection cache réelle non validées |
| T16–T18 | Non exécutés : refunds, export/suppression, restart persistant, backup, CI et scans |

## Chemins corrigés par rapport à l’ancien statut

- Authentification : `src/features/Auth.tsx`, et non `src/features/auth/AuthPages.tsx`.
- Session/API : `src/services/hooks.ts`, `src/services/api.ts`, `src/services/http.ts`.
- Catalogue/personnages : `src/lib/characters.ts`, `src/features/Discovery.tsx`.
- Conversations : `src/features/Conversations.tsx`, `src/services/mock.ts` et `src/services/http.ts`.
- PWA : `vite.config.ts`, `src/lib/offline.ts`, `public/manifest.webmanifest`.

