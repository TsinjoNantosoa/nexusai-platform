# NexusAI — Cahier des charges

**AI Character Chat · Memory · Stripe Billing · PWA**

Version 1.0 — 25 novembre 2026  
Projet personnel de portfolio — Sandaniaina Tsinjo Nantosoa  
Statut : spécification de référence proposée, à valider avant implémentation.

## Synthèse exécutive
NexusAI est une application web progressive de conversation avec des personnages d'intelligence artificielle. Elle permet de créer un compte, choisir un personnage, discuter avec lui, retrouver ses échanges et gérer un portefeuille de crédits virtuels. Elle démontre un parcours de paiement Stripe en environnement de test, incluant achats uniques, abonnements, webhooks et portail client.

Le projet est indépendant de la mission Ayorin. Aucun code, schéma confidentiel, nom commercial ou donnée du prospect ne sera utilisé. La priorité est une démonstration de facturation vérifiable, puis un MVP PWA déployable et reproductible.

**Décisions structurantes :** monorepo, monolithe modulaire FastAPI, React TypeScript, PostgreSQL, Stripe Checkout/Billing, sessions sécurisées, Docker Compose et CI/CD. Redis et pgvector restent optionnels. Aucun encaissement réel dans le MVP.

## Sommaire
| Section | Contenu |
|---|---|
| 01 | Contexte, objectifs, périmètre et acteurs |
| 02 | Exigences fonctionnelles et parcours |
| 03 | Portefeuille et règles financières |
| 04 | Stripe, abonnements et webhooks |
| 05 | Intelligence artificielle et mémoire |
| 06 | Interface, accessibilité et PWA |
| 07 | Architecture et organisation technique |
| 08 | Données et contrats API |
| 09 | Sécurité, confidentialité et exploitation |
| 10 | Recette et critères d'acceptation |
| 11 | Planning, risques, livrables et validation |

Les exigences P0 sont bloquantes pour la démonstration Stripe ; P1 sont requises pour le MVP PWA ; P2 relèvent des évolutions. Les cibles techniques et délais sont des hypothèses de réalisation, non des garanties commerciales.

<!-- PAGE -->
# 01 — Contexte, objectifs et périmètre

## 1.1 Enjeux
- Constituer une référence personnelle crédible sur Stripe, au-delà d'une simple page de paiement.
- Démontrer la conception de bout en bout d'un produit IA : interface, backend, données, paiement, sécurité et exploitation.
- Livrer rapidement une première version vérifiable, utilisable en entretien et enrichissable sans réécriture.
- Maintenir une application de démonstration indépendante, à coûts maîtrisés et sans données réelles sensibles.

## 1.2 Versions et limites
| Version | Périmètre | Critère de sortie |
|---|---|---|
| V0.1 — Stripe (P0) | Auth minimale, catalogue des offres, Checkout, ledger, webhooks, abonnement, portail | Achat et abonnement testés ; aucun double crédit ; historique consultable |
| V1.0 — MVP (P1) | V0.1 + personnages, chat, mémoire, affinité, débit/restitution, PWA, administration minimale, modération | Parcours utilisateur complet, tests bloquants réussis et déploiement de démonstration |
| V2.0 (P2) | OAuth Google/Apple, publication communautaire, modération avancée, push, recherche vectorielle, charge avancée | Backlog à replanifier après validation du MVP |

Hors périmètre initial : applications natives iOS/Android, stores, encaissement réel, place de marché, retrait ou transfert de crédits, entraînement de modèles, contenus explicites, microservices et Kubernetes. Managed Payments est une piste distincte soumise à l'éligibilité et à la validation technique.

## 1.3 Acteurs et droits
| Acteur | Droits principaux |
|---|---|
| Visiteur | Consulter présentation, offres et catalogue public ; créer un compte |
| Utilisateur | Gérer son profil, ses conversations, son portefeuille et ses abonnements uniquement |
| Administrateur | Gérer catalogue, signalements et incidents ; consulter données minimisées et journaux autorisés |
| Stripe | Émettre des événements authentifiés ; fournir Checkout et portail |
| Fournisseur IA | Générer des réponses via le backend, dans les limites configurées |

## 1.4 Indicateurs de réussite
Démontrer un achat test suivi d'un crédit unique ; un abonnement et un renouvellement test ; un refus sans crédit ; une restitution après erreur IA ; une installation PWA ; une CI reproductible. La conformité est démontrée par des preuves de tests, non par une déclaration de certification. Aucun taux de réussite ou performance n'est réputé acquis avant mesure.

<!-- PAGE -->
# 02 — Exigences fonctionnelles

## 2.1 Catalogue des exigences
| ID / priorité | Exigence et résultat attendu |
|---|---|
| F01 / P0 | Inscription email/mot de passe, connexion et déconnexion ; unicité email, consentement aux conditions de démo et déclaration 18+ ; refus des comptes non autorisés. |
| F02 / P0 | Profil et session ; afficher uniquement les données du compte connecté. Réinitialisation mot de passe et vérification email avant ouverture publique non restreinte (P1). |
| F03 / P0 | Catalogue des packs et abonnement ; prix, devise et crédits issus du serveur. |
| F04 / P0 | Acheter un pack via Stripe Checkout hébergé ; retour succès, attente ou annulation sans mutation financière côté client. |
| F05 / P0 | Souscrire au Premium, consulter l'état et ouvrir le portail Stripe ; synchronisation des renouvellements et résiliations. |
| F06 / P0 | Voir le solde et l'historique paginé ; chaque mouvement possède type, date, montant et référence. |
| F07 / P1 | Explorer quatre personnages prédéfinis, consulter leur description et démarrer une conversation. |
| F08 / P1 | Envoyer un message, recevoir une réponse progressive, retrouver et supprimer ses propres conversations. |
| F09 / P1 | Mémoire contextuelle et résumé ; consulter/effacer les informations mémorisées ; affinité plafonnée et indépendante des achats. |
| F10 / P1 | Réserver les crédits avant génération ; restituer sur échec confirmé, sans double opération. |
| F11 / P1 | Installer la PWA ; interface responsive, écran hors ligne et reprise explicite en ligne. |
| F12 / P1 | Signaler un contenu, bloquer un personnage, traiter les signalements via un rôle administrateur. |
| F13 / P1 | Export et suppression de compte ; informer des limites de conservation des écritures nécessaires. |
| F14 / P2 | Authentification sociale, création et publication communautaires avec validation, signalement et retrait. |

## 2.2 Parcours principaux
**Paiement :** connexion → choix de pack → création de commande → Checkout → retour en attente → webhook vérifié → crédit affiché → historique. En cas de refus/annulation, aucun crédit.

**Chat :** choix du personnage → ouverture d'une conversation → envoi → contrôle d'accès, modération et solde → réservation → réponse progressive → confirmation ou restitution → historique.

**Abonnement :** choix Premium → Checkout → facture confirmée → attribution unique des crédits → gestion via le portail → renouvellement ou fin de période. Les états en attente et en erreur restent visibles.

<!-- PAGE -->
# 03 — Portefeuille et règles financières

## 3.1 Offres de démonstration
| Offre | Prix TTC affiché en test* | Crédits / règle |
|---|---:|---|
| Free | 0 € | 20 gemmes, une seule fois par compte |
| Starter | 2,99 € | 100 gemmes par achat payé |
| Plus | 9,99 € | 500 gemmes par achat payé |
| Premium | 19,99 €/mois | 1 500 gemmes par période effectivement payée |

*Prix fictifs en EUR, non validés commercialement ; aucune TVA réelle ni obligation fiscale simulée. Coût proposé d'un message : 2 gemmes. Pas de transfert ni conversion en argent. Les crédits acquis restent disponibles après résiliation du plan ; les avantages futurs cessent selon l'état Stripe. Pas de prorata, essai gratuit ou changement de formule dans V0.1.

## 3.2 Invariants métier
| ID | Règle obligatoire |
|---|---|
| R01 | Solde entier non négatif ; contrôle côté serveur, jamais calculé par le navigateur comme autorité. |
| R02 | Ledger append-only : un mouvement signé avec référence unique, type, compte, date UTC. Solde = somme des écritures validées. |
| R03 | Paiement, événement et crédit sont corrélés ; montant, devise, produit et utilisateur sont vérifiés côté serveur. |
| R04 | Une commande payée ou facture éligible ne produit qu'un crédit, même en cas de concurrence, retry ou événement différent. |
| R05 | Réservation IA et débit du solde atomiques ; une demande possède une clé d'idempotence unique par utilisateur. |
| R06 | Réponse finale persistée = débit conservé. Erreur terminale = mouvement compensatoire unique ; aucun effacement de l'historique. |
| R07 | Une tâche de réconciliation traite les demandes bloquées ; le client ne peut pas demander un crédit arbitraire. |
| R08 | Remboursement Stripe distinct d'une restitution IA : retrait des crédits inutilisés dans la limite du solde ; insuffisance → compte en revue, opérations payantes suspendues. |

## 3.3 Transactions et états
Utiliser PostgreSQL avec verrou de ligne ou UPDATE conditionnel, et contraintes UNIQUE sur références métier. Le solde matérialisé, si retenu, et le ledger sont mis à jour dans une même transaction. Le solde est recalculable depuis le journal. Les paiements en EUR sont stockés en centimes entiers ; les gemmes en entiers.

Commande : créée → Checkout en attente → payée / échouée / expirée → remboursée partiellement ou totalement (état dérivé du montant remboursé). Génération : réservée → en cours → terminée / échec → restituée si nécessaire. Les transitions concurrentes sont conditionnelles ; un retry ne doit pas créer une nouvelle réservation. Ne pas garder une transaction SQL ouverte pendant un appel réseau IA ou Stripe.

<!-- PAGE -->
# 04 — Stripe et traitement des webhooks

## 4.1 Intégration P0
Stripe Checkout hébergé (mode payment ou subscription), Stripe Billing et Customer Portal. Le backend crée les sessions à partir d'un identifiant d'offre autorisé, associe le Customer au compte, stocke une commande interne et utilise une clé d'idempotence stable sur les appels de création. Le portail est créé pour le Customer du compte authentifié, avec URL de retour contrôlée.

Le navigateur n'envoie ni prix de référence, ni nombre de gemmes de confiance. Les secrets de paiement sont exclusivement côté serveur. La page de retour n'accorde aucun crédit ; elle interroge le statut de la commande. Seuls les objets Stripe vérifiés déterminent le paiement.

## 4.2 Événements et effets attendus
| Événement | Traitement |
|---|---|
| checkout.session.completed | Pour mode payment : vérifier paiement effectivement payé, commande et offre ; crédit unique. Pour subscription : associer les identifiants, pas de crédit ici. |
| checkout.session.async_payment_succeeded / failed | Confirmer ou refuser les paiements différés ; aucune attribution sur échec. |
| checkout.session.expired | Marquer l'expiration sans écraser un paiement déjà confirmé. |
| invoice.paid | Vérifier facture Premium éligible et paiement positif ; crédit unique par facture, y compris renouvellement. Exclure factures hors formule et ajustements. |
| invoice.payment_failed | Indiquer échec/retard ; aucun nouveau crédit. |
| customer.subscription.updated / deleted | Synchroniser l'état actuel et dates de période ; fin des avantages futurs selon état et politique. |
| charge.refunded | Vérifier remboursement cumulé, appliquer une compensation proportionnelle documentée et plafonnée ; tracer les cas nécessitant revue. |

## 4.3 Fiabilité, environnement et démonstration
Vérifier Stripe-Signature sur le corps brut et le secret de l'endpoint avant tout traitement. Enregistrer l'événement dans une inbox durable avec identifiant unique ; répondre 2xx seulement après persistance durable ou traitement réussi. Un traitement réessayable applique les effets métier en transaction ; réconcilier depuis Stripe si des événements arrivent en désordre. Journaliser les erreurs sans secrets ni données de carte.

Mode `stripe_test` : clés test, événements non-live, produits sandbox, carte fictive 4242 4242 4242 4242. Mode `mock` : simulation interne distincte, avec indication permanente, sans fabriquer de webhook Stripe signé. Aucun passage en live autorisé dans le MVP. Prévoir script d'initialisation des offres et guide de renouvellement du sandbox ; disponibilité et persistance du compte à vérifier avant livraison.

Références techniques : Stripe Docs — Checkout fulfillment (https://docs.stripe.com/checkout/fulfillment), Webhooks (https://docs.stripe.com/webhooks), Billing (https://docs.stripe.com/billing). Managed Payments reste conditionnel et hors recette initiale.

<!-- PAGE -->
# 05 — Intelligence artificielle et mémoire

## 5.1 Personnages initiaux
| Personnage | Rôle | Comportement attendu |
|---|---|---|
| Atlas | Mentor technique | Explications structurées, programmation et architecture |
| Luna | Assistante créative | Brainstorming et rédaction |
| Nova | Coach de productivité | Organisation, objectifs et tâches |
| Echo | Personnage narratif | Histoires interactives non explicites |

Chaque personnage possède un identifiant, un nom, une description, une persona versionnée, un avatar sous licence appropriée, un statut de publication et une configuration du modèle. Indiquer clairement qu'il s'agit d'une IA, non d'une personne réelle. Aucune prétention à un service médical, juridique ou d'urgence.

## 5.2 Pipeline de génération (F08/F10)
1. Authentifier, vérifier la propriété de la conversation, valider longueur du message, limite de débit et contenu.
2. Créer une demande IA idempotente et réserver 2 gemmes en transaction PostgreSQL.
3. Charger persona, derniers messages et résumé ; borner le contexte et appeler le fournisseur abstrait.
4. Diffuser la réponse via SSE ; traiter timeout, interruption réseau, limites et erreurs du fournisseur.
5. Persister le résultat final et l'usage, conserver le débit si succès ; sur échec terminal, créer une restitution unique.
6. Réconcilier les demandes bloquées via tâche planifiée, sans relancer aveuglément les appels payants.

## 5.3 Mémoire et personnalisation
| Niveau | Exigence |
|---|---|
| Court terme | Historique récent, limité par un budget de tokens configurable |
| Résumé | Résumé des échanges antérieurs, versionné et associé à la conversation |
| Persistant | Informations utiles autorisées par utilisateur ; isolation utilisateur/personnage ; possibilité d'effacement |
| Vectoriel | pgvector en V2 seulement si la pertinence est démontrée |

Affinité : indicateur de personnalisation de 0 à 100, calculé côté serveur à partir d'interactions réussies (proposition : +1 maximum par jour et personnage). Aucun avantage payant lié à l'affinité, aucune pression émotionnelle ou notification culpabilisante. Prévoir réinitialisation par l'utilisateur.

## 5.4 Coûts et garde-fous
Fournisseur `mock` déterministe pour tests et démonstration publique ; fournisseur réel optionnel via SDK et clés serveur. Limites proposées : 2 000 caractères par message, 1 024 tokens de sortie, 10 requêtes/minute par compte et une génération simultanée par compte. Plafond global configurable, arrêt de la génération quand il est atteint. La modération ne repose pas exclusivement sur le prompt du personnage. Refuser les contenus explicites et appliquer des filtres adaptés avant et après génération ; tester aussi le streaming.

<!-- PAGE -->
# 06 — Interface utilisateur et PWA

## 6.1 Design et navigation
Identité proposée : thème sombre avec accents violets/bleus, typographie lisible, composants cohérents. Interface mobile-first ; menu latéral sur ordinateur et navigation basse sur mobile. Français et anglais (i18n), textes de paiement et états d'erreur compréhensibles. Aucune identité graphique reprise du prospect.

| Route | Contenu |
|---|---|
| /, /login, /register | Présentation, connexion, inscription, mentions de démo |
| /explore, /characters/:id | Catalogue et fiche personnage |
| /conversations, /chat/:id | Historique, conversation, streaming, coût et solde |
| /wallet | Solde et historique paginé, état des commandes |
| /pricing | Offres et gestion de l'abonnement |
| /billing/success, /billing/cancel | Retour Stripe, vérification de l'état et prochaine action |
| /settings | Profil, langue, confidentialité, export/suppression |
| /admin | Catalogue, signalements, état des événements et demandes bloquées ; rôle requis |

## 6.2 Exigences PWA
| ID | Critère |
|---|---|
| W01 | Manifest avec name, short_name, start_url, scope, display standalone, couleurs et icônes 192/512 px dont maskable. |
| W02 | Service worker versionné ; cache uniquement du shell et des ressources publiques explicitement autorisées. |
| W03 | HTTPS en ligne ; installation testée sur Chrome/Edge et Android compatible ; instruction d'ajout à l'accueil sur iOS Safari. |
| W04 | Hors ligne : afficher un état clair ; aucune dépense, création de paiement ou requête IA mise en file d'attente silencieusement. |
| W05 | Exclure API privées, conversations, tokens, webhooks, routes de paiement et réponses authentifiées du cache. Nettoyer données locales de session à la déconnexion. |
| W06 | Informer des mises à jour ; ne pas interrompre un paiement ou une génération active ; reprise réseau et actualisation du solde. |

## 6.3 Qualité d'usage
Objectif d'accessibilité WCAG 2.2 AA pour les parcours principaux, à vérifier : navigation clavier, focus visible, labels, contrastes, messages d'erreur, annonces de statut et zoom. Tester 360 px, 768 px et 1440 px. Prévoir états chargement, vide, erreur, attente paiement, solde insuffisant et perte réseau. Ne pas présenter un achat comme confirmé avant validation serveur. Afficher un bandeau permanent « Démonstration — aucun paiement réel ».

<!-- PAGE -->
# 07 — Architecture et organisation technique

## 7.1 Architecture cible
Navigateur/PWA → reverse proxy HTTPS (même origine) → API FastAPI → PostgreSQL. Le backend appelle Stripe et le fournisseur IA ; les webhooks entrants arrivent sur un endpoint dédié. Un worker léger traite l'inbox et les réconciliations. Redis est optionnel pour le rate limiting distribué ; il n'est jamais la source de vérité financière.

| Couche | Choix et justification |
|---|---|
| UI | React, TypeScript, Vite, Tailwind, shadcn/ui ; composants et types partagés |
| Données client | TanStack Query, React Router ; requêtes invalidées après mutation |
| PWA | vite-plugin-pwa/Workbox ; politiques de cache explicites |
| API | FastAPI, Pydantic, SQLAlchemy 2, Alembic ; modules à responsabilités séparées |
| Données | PostgreSQL ; intégrité, contraintes et transactions ; pgvector optionnel |
| IA et paiement | SDK IA derrière interface fournisseur ; Stripe SDK Python ; versions verrouillées |
| Tests / outils | Pytest, Vitest, Playwright, Ruff, ESLint, contrôle TypeScript |
| Infra | Docker Compose, Nginx, GitHub Actions ; images non-root et healthchecks |

## 7.2 Organisation du monorepo
| Chemin | Responsabilité |
|---|---|
| frontend/src/app, components, features | Routage, UI, auth, chat, wallet, billing, PWA |
| backend/app/core, db, auth, users | Configuration, persistance, sécurité, comptes |
| backend/app/characters, conversations, memory, ai | Domaine conversationnel et fournisseurs |
| backend/app/wallet, billing, webhooks | Ledger, commandes, Stripe, inbox et réconciliation |
| backend/app/moderation, admin | Administration et signalements |
| backend/migrations, backend/tests | Migrations et recette automatisée |
| infrastructure/, .github/workflows/ | Conteneurs, proxy, CI/CD |
| docs/, AGENTS.md, README.md, SECURITY.md | Spécifications, ADR, guide agent, exploitation |

Racine : compose.yaml, .env.example sans secrets, .gitignore et licence du code original (MIT proposée). Les versions et lockfiles sont choisis après audit local ; éviter `latest` en production. Modules backend : routes → services métier → repositories/modèles ; aucun accès direct à la DB depuis l'UI.

## 7.3 Règles de livraison
Branche main stable ; branches feat/bootstrap, feat/auth-wallet, feat/stripe-checkout, feat/stripe-billing, feat/ai-chat, feat/pwa et feat/devsecops. Une PR par lot cohérent, tests exécutés et preuve consignée ; aucun secret, aucun push automatique non demandé. Maintenir une trace des décisions d'architecture et des changements de périmètre. 

<!-- PAGE -->
# 08 — Données et contrats API

## 8.1 Modèle relationnel minimal
| Table | Champs structurants et contraintes |
|---|---|
| users, sessions | user UUID, email unique normalisé, hash, rôle, âge déclaré ; sessions expirables/révocables |
| characters, affinities | persona versionnée, statut ; UNIQUE(user_id, character_id), score 0–100 |
| conversations, messages, memories | FK utilisateur/personnage ; rôle, contenu, ordre et timestamps ; mémoire isolée |
| wallets, wallet_entries | wallet UNIQUE(user_id), solde entier >=0 ; écritures signées, référence métier unique |
| products, payments | SKU/Price ID, montant centimes, devise, crédits ; commande, Customer/Session/PaymentIntent uniques selon cardinalité |
| subscriptions, stripe_events | Stripe subscription ID unique, état/période ; event ID unique, état, tentatives, date, erreur expurgée |
| ai_requests | user/conversation, clé idempotence, statut, gemmes, tokens, timestamps ; UNIQUE(user_id, request_key) |
| reports, audit_logs | Auteur, cible, motif, état, trace et rétention définie |

Toutes les FK et index de recherche utiles sont définis par migration Alembic. Les dates sont stockées en UTC, identifiants internes en UUID, montants en entiers. Contraintes métier sur les références de crédit par commande/facture et de restitution par génération. Suppression des conversations et du compte : distinguer effacement des contenus et conservation minimale des écritures nécessaires, avec pseudonymisation et politique documentée.

## 8.2 API v1 (contrat initial)
| Méthode / route (préfixe /api/v1) | Entrée / sortie attendue |
|---|---|
| POST /auth/register, /auth/login, /auth/logout | Identité / session ; CSRF sur mutations selon flux |
| GET /users/me ; GET /characters | Profil / catalogue autorisé |
| POST /conversations ; GET /conversations | character_id / liste paginée |
| GET, DELETE /conversations/{id} | Détail ou suppression, contrôle propriétaire |
| GET, POST /conversations/{id}/messages | Historique paginé ; message + Idempotency-Key → SSE |
| GET /wallet ; GET /wallet/transactions | Solde / ledger paginé |
| GET /billing/products ; POST /billing/checkout | Offres ; SKU + Idempotency-Key → checkout_url, order_id |
| GET /billing/orders/{id} ; GET /billing/subscription | Statut de la commande et du plan, propriétaire requis |
| POST /billing/portal ; POST /webhooks/stripe | URL portail ; webhook corps brut et signature |
| POST /reports ; GET /admin/reports | Signalement ; liste réservée à l'administration |
| GET /health/live ; GET /health/ready (hors préfixe) | Santé du processus / dépendances |

Réponses JSON documentées via OpenAPI, sauf streaming. Erreurs structurées avec code métier et request_id : 401 non authentifié, 403 interdit, 404 introuvable, 409 conflit/solde insuffisant, 422 validation, 429 limite atteinte, 503 dépendance indisponible. Ne pas divulguer de détails internes. Pagination bornée ; schémas et exemples à versionner.

<!-- PAGE -->
# 09 — Sécurité, confidentialité et exploitation

## 9.1 Exigences de sécurité
| ID | Contrôle obligatoire |
|---|---|
| S01 | Hash des mots de passe Argon2id ; session opaque révocable, cookie HttpOnly, Secure en HTTPS, SameSite approprié ; rotation à la connexion. |
| S02 | Contrôle de propriété de chaque ressource et RBAC admin côté API ; refus par défaut. CSRF sur mutations, origines autorisées strictes, CSP et en-têtes adaptés. |
| S03 | Secrets hors Git, .env.example fictif, injection au runtime, séparation environnements ; aucun token dans les logs ou bundles. |
| S04 | Validation Pydantic, ORM paramétré, limites payload et pagination ; échappement du contenu IA, pas de HTML non assaini. |
| S05 | Signature Stripe, contrôles de montant/devise, idempotence, transactions atomiques, réconciliation et alertes d'anomalie. |
| S06 | Rate limiting auth/IA/paiement, plafond de coût, timeout et retries bornés. Démonstration publique mock par défaut ou accès restreint. |
| S07 | Conteneurs non-root, réseau DB privé, TLS, images épinglées, scans Gitleaks/Trivy et dépendances. |
| S08 | Aucun secret ou conversation privée en cache PWA ; logs minimisés, contrôle d'accès aux journaux. |

## 9.2 Confidentialité et majorité
Utiliser uniquement des comptes fictifs pour les scénarios et prévenir les visiteurs de ne pas saisir de données sensibles. Déclaration 18+ au MVP : ce n'est pas une preuve d'âge. Une vérification adaptée et une revue réglementaire seraient requises avant ouverture commerciale. Mettre à disposition notices de confidentialité, export et demande de suppression. Définir avant exposition publique la durée de conservation, le traitement des données par le fournisseur IA et la procédure d'incident. Proposition démo : purge des conversations/comptes de démo inactifs après 30 jours ; journaux techniques expurgés 14 jours ; écritures de test conservées le temps nécessaire à la recette puis anonymisées/purgées suivant politique. Ne pas prétendre à une conformité RGPD ou PCI certifiée.

## 9.3 Exploitation et objectifs non fonctionnels
Cibles de recette (à mesurer sur l'environnement déclaré) : API locale hors fournisseurs p95 ≤ 500 ms à 10 utilisateurs simultanés ; page principale LCP ≤ 2,5 s sur profil de test mobile ; objectif 0 crédit dupliqué et 0 solde négatif ; sauvegarde quotidienne et restauration testée avant publication. Logs structurés avec request_id, event_id et codes d'erreur ; métriques des webhooks en attente, erreurs IA et dépenses, sans contenu privé. Le MVP n'annonce aucun SLA contractuel. Documenter rollback et restauration, et vérifier que le mode public ne peut pas activer Stripe live.

<!-- PAGE -->
# 10 — Recette et critères d'acceptation

Tous les tests ci-dessous sont à exécuter ; aucun résultat n'est acquis à la date de rédaction. Les tests P0 sont bloquants pour V0.1, les autres pour V1.0.

| ID | Scénario | Résultat attendu |
|---|---|---|
| T01 P0 | Achat Starter 2,99 € test | +100 une fois, paiement et ledger corrélés |
| T02 P0 | Carte refusée / Checkout annulé | Aucun crédit ; état lisible |
| T03 P0 | Rejeu même événement et concurrence | Une seule écriture par commande |
| T04 P0 | Signature invalide / événement live | Rejet ; aucune mutation |
| T05 P0 | Premium payé puis renouvelé (test) | +1 500 par facture éligible, sans doublon |
| T06 P0 | Échec de renouvellement | Aucun crédit, statut synchronisé |
| T07 P0 | Portail et résiliation | Bon Customer, fin des avantages futurs |
| T08 P0 | Facture/événement désordonné | État réconcilié, pas de crédit indu |
| T09 P0 | Faux prix ou commande d'un tiers | Rejet ou valeur serveur utilisée |
| T10 P1 | Deux dépenses, solde de 2 | Une seule réservation ; solde non négatif |
| T11 P1 | Timeout IA et retry/restart | Restitution unique ; aucune demande bloquée |
| T12 P1 | Chat et mémoire après reconnexion | Historique isolé et contexte restitué |
| T13 P1 | Accès conversation d'un tiers, CSRF | Rejet ; aucune fuite ou mutation |
| T14 P1 | Installation PWA, hors ligne, retour réseau | Shell accessible, opérations payantes bloquées hors ligne |
| T15 P1 | Inspection cache après session/logout | Aucune conversation ou donnée privée persistante |
| T16 P1 | Remboursement partiel puis total/rejeu | Compensations exactes ; revue si insuffisance |
| T17 P1 | Export/suppression, signalement, admin | Droits contrôlés, politique appliquée |
| T18 P1 | Restart, backup/restore, CI et scan | Données conservées ; build, migration et restauration validés |

## 10.1 Méthode et preuves
Tests unitaires pour règles métier ; intégration sur PostgreSQL réel isolé (contraintes et concurrence) ; Stripe sandbox pour au moins achat, abonnement et portail, simulation pour cas reproductibles ; Playwright pour parcours UI. Tester factures via mécanismes Stripe de test lorsque disponibles. Consigner commande, date, environnement, résultat, logs expurgés et identifiants de test. Définition de terminé : tests bloquants verts, documentation à jour, revue du code, aucune vulnérabilité critique/élevée non traitée ou explicitement acceptée, aucun secret dans Git. Un mode mock seul ne valide pas l'intégration Stripe réelle.

<!-- PAGE -->
# 11 — Planning, risques et livrables

## 11.1 Planning accéléré (objectif 7–10 jours ouvrés)
| Lot | Cible | Livrable et condition de passage |
|---|---|---|
| L0 | J1 début | Audit Git/Node/Python/Docker/espace, Stripe CLI et accès sandbox ; socle, DB, auth minimale |
| L1 | J1–J2 | Checkout, ledger, inbox, abonnement, portail ; preuves T01–T09 |
| L2 | J3 | Auth durcie, portefeuille, tests concurrence, mécanismes remboursement |
| L3 | J4–J5 | Personnages, chat mock/IA, mémoire, streaming et réconciliation |
| L4 | J6 | Interface, PWA, parcours utilisateur et administration minimale |
| L5 | J7–J8 | Recette, CI/CD, scans, confidentialité, restauration et corrections |
| L6 | J9–J10 | Déploiement, documentation, vidéo et étude de cas portfolio |

Cible ambitieuse, à réévaluer après L0 ; priorité à une démonstration Stripe sûre. Les tâches non bloquantes peuvent être différées ; aucun contrôle financier ou d'accès ne peut être supprimé pour tenir le délai.

## 11.2 Risques et coûts
| Risque | Réponse |
|---|---|
| Accès Stripe test indisponible / expiré | Vérifier tôt ; script de bootstrap reproductible ; mode mock explicite ; indiquer les tests non réalisés |
| Faible espace disque / dépendances | Audit préalable ; images légères ; pas de nettoyage destructif des autres projets |
| Surcoût IA / abus public | Mock par défaut, plafonds, accès restreint au réel |
| Complexité abonnements et événements | Priorité aux invariants, tests concurrence, inbox et réconciliation |
| Retard PWA ou publication | Livrer d'abord Stripe, différer V2 ; déploiement HTTPS contrôlé |

Développement local visé sans achat obligatoire ; frais potentiels : hébergement, nom de domaine, API IA et quotas CI. Aucun budget réel fixé. Ne pas activer de paiement réel, ni contourner l'éligibilité Stripe. Managed Payments et OAuth social à confirmer séparément.

## 11.3 Livrables et validation finale
Repository original documenté, application PWA en ligne ou environnement de démo local reproductible, OpenAPI, migrations, scripts de seed, guide Stripe sandbox, tests et preuves, pipeline CI, guide d'exploitation/rollback, SECURITY.md, documentation architecture et vidéo de 3–5 minutes. Étude de cas portfolio mentionnant clairement le mode test et les limites.

Validation par le porteur du projet à chaque lot : résultat des tests, revue du diff, commit propre et mise à jour du backlog. Décisions ouvertes : accès sandbox, versions exactes, hébergeur, politique de conservation finale, fournisseur IA et budget. Ce cahier des charges constitue une base de travail ; aucun développement ni déploiement n'est déclaré réalisé.
