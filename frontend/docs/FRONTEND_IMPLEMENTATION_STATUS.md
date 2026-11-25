# NexusAI — état et traçabilité du frontend

## État actuel

Le cahier des charges V1.0 du 25 novembre 2026 a été lu intégralement et conservé sans modification dans `CAHIER_DES_CHARGES.md`. L’archive Nexus-main a été inspectée sans exécuter son code. **L’application importée n’est pas encore implémentée dans ce projet.** L’accord pour remplacer React Router par le système TanStack Router imposé par Lovable reste nécessaire.

Les éléments « partiels dans l’archive » ne sont ni intégrés, ni testés, ni déclarés conformes. Aucun paiement réel, aucune connexion Stripe/IA, aucun backend ou déploiement n’est autorisé dans cette tâche frontend.

## Exigences fonctionnelles

| ID | Fonction / lot | État frontend et source pertinente | Couverture à prévoir | Dépendance backend / limite |
| --- | --- | --- | --- | --- |
| F01 | Authentification — FE-01 | Partiel dans `src/features/auth/AuthPages.tsx` de l’archive | Validation, consentements, session, déconnexion | Unicité email, comptes autorisés et sessions réelles : FastAPI |
| F02 | Profil/session — FE-00/03 | Session partielle dans `src/hooks/useSession.ts` ; réglages absents | Profil isolé, erreurs 401, nettoyage | Email vérifié/réinitialisation et sessions sécurisées non connectés |
| F03 | Catalogue des offres — FE-01 | Partiel dans `PricingPage.tsx` et client API de l’archive | Valeurs exactes et catalogue reçu du serveur | Prix/gemmes faisant autorité : API |
| F04 | Checkout/retours — FE-01 | Partiel, défauts de parcours identifiés | Pending, refus, annulation, confirmation et absence de crédit à l’ouverture du retour | Stripe hébergé et validation serveur externes |
| F05 | Premium/portail — FE-01 | Activation mock partielle ; portail et renouvellements manquants | Activation, renouvellement payé/échoué, résiliation | Customer, factures, abonnement et URL portail : API |
| F06 | Solde/ledger — FE-01 | Wallet partiel ; pagination à compléter | Solde entier, filtres, pagination, références et états | Journal financier persistant côté serveur |
| F07 | Personnages — FE-02 | Pages placeholders | Recherche, Atlas/Luna/Nova/Echo, fiche, ouverture | Catalogue réel via API ; avatars originaux/licenciés à créer |
| F08 | Conversations/chat — FE-02 | Pages placeholders | Historique, suppression confirmée, SSE, annulation, erreurs | Propriété et persistance : API |
| F09 | Mémoire/affinité — FE-02 | Non implémenté | Effacement, reset, score 0–100, achats sans influence | Contrats mémoire/reset non finalisés ; score côté serveur |
| F10 | Réservation/restitution — FE-02 | Non implémenté | 2 gemmes, insuffisance, erreur terminale et restitution unique simulées | Atomicité et réconciliation réelles : PostgreSQL/backend |
| F11 | PWA — FE-03 | Manifest/worker absents | W01–W06, tailles 360/768/1440 | HTTPS publié et tests sur vrais appareils distincts |
| F12 | Signalement/blocage/admin — FE-04 | Placeholder admin ; garde staff partielle | Signalement, blocage, démonstration admin séparée | RBAC réel et opérations admin/blocage à contracter |
| F13 | Export/suppression — FE-03 | Placeholder réglages | Confirmation et limites clairement affichées | Endpoints et politique de conservation non finalisés ; pas de faux succès |
| F14 | Social/communauté — V2 | Hors périmètre P2 | Aucun faux OAuth ou publication communautaire | À replanifier après V1 |

## Règles financières

| ID | Responsabilité frontend / lot | Test frontend ou simulation à prévoir | Dépendance et limitation |
| --- | --- | --- | --- |
| R01 | Afficher un solde reçu du service — FE-01/02 | Aucun solde négatif dans le service mock | Autorité et concurrence réelles côté serveur |
| R02 | Afficher journal signé, références et dates UTC — FE-01 | Somme du ledger mock = solde ; compensation append-only | Ledger immuable et contraintes SQL : backend |
| R03 | Envoyer SKU et clé d’idempotence, pas un prix autoritaire — FE-01 | Contrôle du contenu de la demande Checkout | Montant/devise/offre/utilisateur vérifiés par API |
| R04 | Observer une seule attribution — FE-01 | Confirmation dupliquée sans double crédit mock | Concurrence, factures et événements : backend |
| R05 | Une demande IA idempotente à la fois — FE-02 | Deux envois avec solde 2 : une réservation mock | Transaction atomique réelle : backend |
| R06 | Afficher débit conservé ou compensation unique — FE-02 | Succès et échec terminal ; restitution mock sans effacer le débit | Résultat final persistant : backend |
| R07 | Ne pas offrir un crédit arbitraire — FE-02 | Pas de relance automatique d’une requête payante interrompue | Tâche de réconciliation : backend |
| R08 | Afficher compensation/revue si fournie — FE-01 | États cohérents, opérations bloquées en revue | Calcul proportionnel des remboursements non détaillé ; ne pas inventer de formule |

## PWA

| ID | Travail FE-03 | Preuve à obtenir | Limite actuelle |
| --- | --- | --- | --- |
| W01 | Manifest, standalone, scope, icônes 192/512 et maskable | Inspection du manifest/icônes | Non implémenté |
| W02 | Worker généré/versionné, ressources publiques explicitement permises | Inspection des règles et cache publié | Non implémenté ; aucun worker app-shell dans la preview |
| W03 | HTTPS et installation Chrome/Edge/Android, instructions iOS | Tests navigateurs et appareils réels | Aucun appareil testé ni publication autorisée |
| W04 | État hors ligne, paiements/IA désactivés, pas de file silencieuse | Parcours hors ligne | Non implémenté |
| W05 | Exclusion API/données privées/auth/paiement, nettoyage logout | Inspection caches et état client | Non implémenté |
| W06 | Mise à jour non intrusive, reprise réseau et actualisation wallet | Génération/checkout actifs, retour réseau | Non implémenté |

## Sécurité

| ID | Périmètre frontend | Preuve / dépendance |
| --- | --- | --- |
| S01 | Pas de secret de session dans le stockage navigateur ; cookies via credentials | Hash Argon2id, rotation, expiration et attributs cookies : backend |
| S02 | Gardes UX uniquement ; préparer CSRF et erreurs 403 | Propriété, RBAC, validation CSRF, CSP/origines : backend/hébergement |
| S03 | Configuration publique seulement ; aucun secret dans code/logs | Inspection des sources et bundle à réaliser |
| S04 | Validation formulaires et texte/Markdown sûr | Pydantic/ORM/payload/pagination autoritaire : backend |
| S05 | Ne jamais appeler un webhook depuis l’UI | Signature, atomicité et réconciliation : backend/Stripe |
| S06 | Mode mock explicite ; limites UX et retries bornés | Rate limiting et plafonds autoritaires : backend |
| S07 | Ne pas déclarer l’infrastructure validée depuis l’UI | Conteneurs/TLS/scans réseau/DB : infrastructure séparée |
| S08 | Pas de données privées dans cache PWA ni logs | Inspection cache/logout à réaliser ; accès journaux : backend |

## Critères de recette : aucune validation acquise

Tous les tests T01–T18 sont actuellement **NON EXÉCUTÉS**. Une simulation UI ne remplace pas leur validation sur Stripe/PostgreSQL.

| ID | Preuve frontend / mock prévue | Validation réelle encore nécessaire |
| --- | --- | --- |
| T01 | Starter 2,99 €, +100 une fois | Achat Stripe test et ledger corrélés |
| T02 | Refus/annulation sans crédit | Checkout Stripe refusé/annulé |
| T03 | Confirmation mock dupliquée sans double crédit | Événement rejoué et concurrence DB |
| T04 | Aucun appel webhook dans l’UI | Signature invalide/live rejetés par serveur |
| T05 | Premium +1 500 par période mock payée | Factures et renouvellement Stripe sandbox |
| T06 | Échec renouvellement mock sans crédit | Synchronisation invoice.payment_failed |
| T07 | Résiliation mock conserve crédits ; interface portail | Bon Customer et fin des avantages Stripe |
| T08 | États en attente/confirmation lisibles | Réconciliation d’événements désordonnés |
| T09 | SKU seul, pas de prix autoritaire | Rejet de commande tierce et validation serveur |
| T10 | Deux demandes mock/solde 2, une réservation | Dépenses concurrentes PostgreSQL |
| T11 | Échec et compensation mock unique | Timeout, restart et réconciliation persistants |
| T12 | Lecture historique et mémoire pendant session mock | Reconnexion réelle et isolation persistante |
| T13 | Garde UX et erreurs sans exposer données | Accès tiers et CSRF rejetés côté API |
| T14 | Shell public hors ligne, actions payantes bloquées | Installation et retour réseau publiés/appareils |
| T15 | Inspection stockage/cache et nettoyage logout | Vérification PWA publiée après session réelle |
| T16 | Affichage état remboursement/revue | Compensations précises/rejeu ; formule à préciser |
| T17 | Interfaces export/suppression/signalement/admin | Droits, endpoints et politique appliquée |
| T18 | Tests frontend, navigation et contrôles livrés | Restart persistant, sauvegarde/restauration, migrations, CI et scans |

## Contrats encore à finaliser

- Formes JSON précises, pagination bornée, objets session/profil et abonnement.
- Acquisition/transmission du jeton CSRF et rotation de session.
- Événements SSE, identifiants de demandes et statut après interruption.
- Mémoire, effacement, reset affinité, blocage et gestion du catalogue/admin.
- Export/suppression de compte et demandes de conservation.
- États remboursement/revue et formule proportionnelle R08.

La valeur +1 d’affinité maximum par jour/personnage, les limites de 2 000 caractères, 1 024 tokens de sortie et 10 requêtes/minute sont identifiées comme **propositions** dans le cahier des charges. Les limites serveur doivent être confirmées/configurables ; la limite UI de 2 000 caractères et le coût initial de 2 gemmes seront couverts par des tests frontend.

## Ordre d’exécution

1. Accord d’adaptation du routage ; FE-00 puis FE-01 et vérification du parcours financier simulé.
2. FE-02, FE-03 puis FE-04 avec vérifications propres à chaque lot.
3. FE-05 : tests effectivement exécutés, rapport de limites et passation API complète.

Le frontend reste seul dans le périmètre autorisé : le cahier des charges décrit aussi l’ensemble du produit, mais n’autorise pas ici la construction du backend, de l’infrastructure ou des intégrations réelles.