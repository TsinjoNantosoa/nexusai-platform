# Contrat frontend / FastAPI

Préfixe configurable `VITE_API_BASE_URL=/api/v1`. Mode `VITE_DATA_MODE=api` : aucun fallback vers les données fictives.

Implémentés dans HttpApiClient : POST auth/register, auth/login, auth/logout ; GET users/me, characters, wallet, wallet/transactions, billing/products, billing/subscription, billing/orders/{id} ; POST billing/checkout, billing/portal, conversations, reports ; GET conversations, conversations/{id}, conversations/{id}/messages, admin/reports ; DELETE conversations/{id} ; POST conversations/{id}/messages avec SSE.

Checkout : `{sku}` et `Idempotency-Key` stable ; réponse `{checkout_url, order_id}`. Aucun prix/gemmes envoyé comme autorité. Redirection HTTPS vers checkout.stripe.com uniquement. Portal : `{portal_url}`, HTTPS billing.stripe.com. Retour de paiement : observation bornée, 12 lectures maximum espacées de 2,5 s ; aucune confirmation ou attribution automatique depuis la page.

Les structures du cahier des charges sont initiales, pas un OpenAPI complet : les types de `types.ts` sont des propositions d’adaptateur à valider. Les listes sont actuellement attendues comme tableaux ; la pagination serveur et les formes JSON doivent être finalisées. Les commandes en attente globales, la mémoire, le blocage, le reset d’affinité, la modération détaillée, l’export/suppression et les modifications catalogue n’ont pas d’endpoints approuvés : erreur integration_pending, jamais faux succès.

SSE proposé, à approuver : `event: delta`, `data: {"delta":"texte"}` ; `event: done`, `data: {"message": {...Message}}` ; `event: error`, `data: {"code":"...","request_id":"..."}`. Parser fetch streaming avec frames partielles ; état final obligatoire. Aucun retry automatique payant.

Cookies credentials include ; aucune session/token en localStorage. `HttpApiClient.setCsrfToken` prévoit X-CSRF-Token sur mutations ; acquisition et rotation restent à contracter. Le serveur doit vérifier CSRF, propriétaire, rôles et limites. Erreurs structurées : code métier, request_id, HTTP 401/403/404/409/422/429/503. Aucune intégration réelle n’a été testée.
