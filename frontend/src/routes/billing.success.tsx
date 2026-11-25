import { createFileRoute } from "@tanstack/react-router";
import { BillingSuccessPage } from "@/features/Billing";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/billing/success")({
  validateSearch: (search: Record<string, unknown>): { order?: string } =>
    typeof search["order"] === "string" ? { order: search["order"] } : {},
  head: () =>
    pageHead(
      "Vérification du paiement",
      "Vérifiez le statut de votre commande NexusAI sans crédit automatique au retour.",
    ),
  component: Page,
});
function Page() {
  return <BillingSuccessPage orderId={Route.useSearch().order ?? ""} />;
}
