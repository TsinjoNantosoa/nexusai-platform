# Rapport des tests réellement exécutés

Date : 25 novembre 2026. Environnement : sandbox Lovable, Vite localhost:8080, Chromium headless, services frontend mock. Aucun serveur FastAPI, PostgreSQL, Stripe ou fournisseur IA connecté.

- `bunx vitest run src/services/mock.test.ts src/services/chat.test.ts src/test/app-routing.test.tsx` : **33 tests réussis**, 3 fichiers. Offres exactes, consentements, welcome 20, crédit unique, pending/refus/annulation, renouvellement/résiliation, ledger, logout, 2 gemmes par message, limite 2000, réservation unique, restitution et garde admin.
- Parcours navigateur financier : connexion fictive, solde 20, Starter confirmé, solde 120, confirmation rejouée : solde 120. Écran de retour et lecture portefeuille vérifiés.
- Parcours chat : Atlas, création, réponse progressive, solde 20→18 ; erreur simulée, restitution, solde final 18 ; hors ligne : envoi désactivé ; logout : accès privé fermé. Aucune erreur pageerror dans ces parcours.
- Catalogue : 4 portraits chargés avec naturalWidth=750 ; contrôles 360/768/1440, aucune largeur horizontale dépassée. Administration démo : catalogue et état vide des signalements vérifiés.
- Preview : 0 service worker enregistré ; code applicatif sans localStorage/sessionStorage. Instrumentation de plateforme peut utiliser sessionStorage ; aucune donnée privée NexusAI n’y est écrite.
- Dernier signal du contrôle automatique plateforme : **build OK**. Aucun build/typecheck manuel lancé (contrôle plateforme automatique).
- Lint global : tentative interrompue après 120 secondes, **non validé globalement**. Lint ciblé : erreurs de format i18n corrigées ; avertissements fast-refresh dans fichiers exportant aussi schémas/formateurs. Résultat final ciblé consigné lors de la clôture.

Non vérifiés : mode HTTP sur vrai FastAPI, OpenAPI final, CSRF/sessions/RBAC serveur, SSE fournisseur réel, Stripe Checkout/Portal/webhooks/factures, contraintes/concurrence PostgreSQL, R08 refunds, limites serveur, modération production, cache/updates offline publiés, installation réelle, accessibilité certifiée, performance, backup/restore, CI/infrastructure. T01–T18 ne sont pas déclarés validés par les simulations.

Captures temporaires dans /tmp/browser/nexus. Les scripts de reproduction sont conservés dans tests/e2e ; aucune capture de secrets ou données réelles.
