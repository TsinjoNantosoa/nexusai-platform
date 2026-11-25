# NexusAI — baseline de tests Phase 0

Date : 25 novembre 2026. Les résultats ci-dessous séparent les commandes exécutées, l’inspection statique et les validations impossibles sans backend ou publication.

## Commandes exécutées

| Commande | Résultat | Preuve / limite |
|---|---|---|
| `bun install --frozen-lockfile` | PASS, code 0 | Bun 1.4.4; 853 installations vérifiées; aucun changement |
| `bun run lint` | PASS, code 0 | 10 avertissements Fast Refresh, 0 erreur |
| `bun run typecheck` | PASS, code 0 | `tsgo -b --noEmit`; `tsgo.exe` présent et exécutable |
| `bun run test` | PASS, code 0 | 3 fichiers, 33 tests réussis, Vitest 4.1.12 |
| `bun run build` | PASS, code 0 | client, SSR, Nitro et génération worker réussis; warnings PWA |
| `bun audit` | ATTENTION, code 1 | 2 vulnérabilités modérées, détaillées dans `AUDIT_FRONTEND.md` |

Le premier lancement groupé a dépassé la limite d’exécution de l’outil pendant le lint; chaque commande a ensuite été relancée séparément et son code a été capturé. Aucun résultat n’est extrapolé depuis ce lancement interrompu.

## Tests Vitest

Les tests exécutés sont :

- `src/services/mock.test.ts` : comptes démo/admin, validation inscription, 20 gemmes initiales, offres Starter/Plus/Premium, états pending/refus/annulation, idempotence, renouvellement/résiliation, ledger et logout.
- `src/services/chat.test.ts` : coût de 2 gemmes, limite 2 000 caractères, restitution unique, génération concurrente, blocage, garde admin et absence de crédit sur annulation.
- `src/test/app-routing.test.tsx` : correspondance de la route `/`.

Résultat exécuté : **33 tests réussis** dans **3 fichiers**. Ces tests exercent `MockApiClient`; ils ne prouvent ni transaction PostgreSQL, ni session sécurisée, ni paiement Stripe, ni autorisation serveur.

## Parcours Chromium local

Le serveur Vite a été lancé sur `http://127.0.0.1:8080` et les scripts existants ont été exécutés avec Chromium headless et Playwright Python.

| Parcours | Résultat observé |
|---|---|
| `tests/e2e/financial_journey.py` | PASS, code 0; titre landing, solde initial 20, Starter confirmé, solde 120, confirmation rejouée sans double crédit, 4 cartes, pas de débordement mobile, aucune `pageerror` |
| `tests/e2e/chat_journey.py` | PASS, code 0; Atlas, message 20→18, échec avec restitution, hors ligne désactive l’envoi, logout ferme `/wallet`, `localStorage=0`, `sessionStorage=1`, 0 service worker, aucune `pageerror` |

La valeur `sessionStorage=1` correspond à l’instrumentation/plateforme observée; aucune donnée privée NexusAI n’y a été écrite dans ce parcours. Le test n’a pas certifié `naturalWidth` des quatre portraits; ce point reste AUD-01.

## Vérification métier baseline

| Domaine | Niveau de preuve | Résultat |
|---|---|---|
| Authentification démo | Exécuté mock + Chromium | comptes fictifs, session mémoire, logout et garde UX validés |
| Welcome gems | Exécuté Vitest/Chromium | 20 gemmes attribuées dans le mock |
| Packs Starter/Plus | Exécuté Vitest/Chromium | crédits et confirmation simulée validés |
| Pending/refus/annulation/doublon | Exécuté Vitest/Chromium | états mock et absence de double crédit validés |
| Premium/renewal | Exécuté Vitest | activation, renouvellement payé, échec et résiliation mock validés |
| Ledger/solde | Exécuté Vitest | somme du ledger mock cohérente; pas de concurrence SQL |
| Débit/restitution IA | Exécuté Vitest/Chromium | 2 gemmes, échec et restitution unique mock validés |
| Propriété conversation | Inspection + mock tests | garde par identifiant dans le mock; aucune isolation backend testée |
| Administration | Exécuté Vitest/Chromium | compte admin fictif et garde de rapports validés |
| PWA/cache | Dev Chromium + build | 0 worker en dev; worker généré dans `dist`, sortie Nitro à corriger |

## Non validé

Les éléments suivants sont **NON EXÉCUTÉS** ou non prouvés par les simulations : API FastAPI réelle, OpenAPI final, cookies HttpOnly/Secure, CSRF, RBAC serveur, SSE fournisseur réel, Stripe Checkout/Portal/webhooks/factures, signatures et idempotence distribuées, concurrence PostgreSQL, refunds R08, limites/rate limiting serveur, modération de production, installation sur appareil réel, cache/updates PWA publié, accessibilité certifiée, performance, CI, backup/restore et l’ensemble des recettes T01–T18 en environnement réel.

La présence de tests mock réussis ne doit donc pas être présentée comme une validation Stripe Sandbox, base de données ou sécurité backend.

