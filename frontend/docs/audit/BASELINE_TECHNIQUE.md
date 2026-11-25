# NexusAI — baseline technique Phase 0

Date de l’audit : 25 novembre 2026  
Périmètre : frontend existant uniquement. Le cahier des charges V1.0 n’a pas été modifié.

## Conclusion

Le projet est reproductible avec Bun et son lockfile, et le frontend passe les contrôles locaux exécutés. Il s’agit d’un projet React 19/TypeScript/Vite avec TanStack Start, TanStack Router, TanStack Query, Nitro et un service mock en mémoire. Il n’existe ni backend FastAPI, ni PostgreSQL, ni Stripe connecté dans cet espace.

Le principal blocage de récupération est l’absence des quatre fichiers `.webp` originaux : les descripteurs JSON pointent encore vers des URLs Lovable `/__l5e/assets-v1/`. Le second risque important concerne la chaîne PWA : le worker est généré sous `dist/sw.js`, mais n’est pas présent dans `.output/public` après le build Nitro observé.

## Environnement

| Élément | Résultat |
|---|---|
| OS | Windows 11 Professionnel 10.0.26300, 64 bits |
| Répertoire | `C:\Users\Tsinjo\Documents\projet\pixel-perfect-replica-main\frontend` |
| Git | Aucun dépôt détecté ; branche, HEAD et index indisponibles |
| Node.js | v24.13.0 |
| Bun | 1.4.4 |
| npm | 11.6.2 |
| Python | 3.12.10 |
| Docker | 29.2.0 |
| Docker Compose | v5.0.2 |
| Stripe CLI | Non installé ou non disponible dans le PATH |
| Espace libre initial | 34,434,646,016 octets sur C: |
| Dépendances avant installation | `node_modules` absent |
| Dépendances après installation | `node_modules` présent ; 853 installations vérifiées sur 876 paquets |

## Git et secrets

`git rev-parse --show-toplevel`, `git status` et `git log` échouent car le workspace n’est pas un dépôt Git. Aucun dépôt ou remote GitHub n’a donc pu être vérifié. Aucun `git init` n’a été exécuté.

Seul `.env.example` existe. Il contient uniquement `VITE_DATA_MODE=mock` et `VITE_API_BASE_URL=/api/v1`. Une recherche de marqueurs de secrets (clés Stripe, clés AWS et clés privées) n’a trouvé aucun fichier, sans afficher de valeur sensible. Le `.gitignore` ne couvre toutefois pas explicitement `.env` et `.env.*`.

## Architecture constatée

- 13 routes fichier dans `src/routes/`, plus les paramètres `characters/$id` et `chat/$id` : accueil, auth, découverte, conversations, chat, portefeuille, pricing, retours billing, paramètres et admin.
- `src/router.tsx` crée un `QueryClient` par requête SSR ; `src/routeTree.gen.ts:321` active `ssr: true`.
- `src/services/types.ts` définit `ApiClient`; `src/services/mock.ts` implémente les scénarios en mémoire; `src/services/http.ts` implémente le transport FastAPI futur.
- `src/services/api.ts:4` sélectionne le mock pour toute valeur différente de `api`; il n’y a pas de fallback du client HTTP vers le mock après erreur.
- `vite.config.ts:10` dépend de `@lovable.dev/vite-tanstack-config`; Nitro produit une cible `cloudflare-module` via cette configuration.
- La PWA est configurée par `vite-plugin-pwa` en `generateSW`; les API privées et les conversations ne sont pas ciblées par le runtime cache déclaré.

## Reproduction

| Commande | Code | Résultat |
|---|---:|---|
| `bun install --frozen-lockfile` | 0 | Installation verrouillée, aucune modification de dépendance |
| `bun run lint` | 0 | 10 avertissements `react-refresh/only-export-components`, 0 erreur |
| `bun run typecheck` | 0 | `tsgo -b --noEmit` fonctionne depuis `node_modules/.bin/tsgo.exe` |
| `bun run test` | 0 | 3 fichiers de test, 33 tests réussis |
| `bun run build` | 0 | Build client, SSR et Nitro réussis; avertissements PWA de glob sans correspondance |
| `bun audit` | 1 | 2 vulnérabilités modérées : `glob`, `minimatch` |
| `npm audit --omit=dev --package-lock=false --json` | 1 | Même chaîne Workbox; pas de `package-lock.json` créé |

Le SHA-256 observé de `bun.lock` après installation est `E28DFB13362D8CFDB1E7E9576F1E1190E11B3C37A03B861C050B1898FAC61904`. Aucun lockfile ni fichier source n’a été modifié pendant cette phase; seuls les artefacts ignorés et `node_modules` ont été produits par les commandes.

## Livrables et limites

Créés dans cette phase :

- `docs/audit/BASELINE_TECHNIQUE.md`
- `docs/audit/AUDIT_FRONTEND.md`
- `docs/audit/TEST_BASELINE.md`
- `docs/audit/PLAN_CORRECTION.md`
- `docs/audit/TRACEABILITY_MATRIX.md`

Non réalisé : migration, correction source, récupération d’assets, changement de dépendances, backend, Stripe, déploiement, commit ou push. Les tests backend, sécurité serveur, Stripe Sandbox, PostgreSQL, appareils réels et production restent non validés.

