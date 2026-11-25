import { createFileRoute } from "@tanstack/react-router";
import { BillingCancelPage } from "@/features/Billing";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/billing/cancel")({
  head: () =>
    pageHead(
      "Paiement interrompu",
      "Votre paiement NexusAI a été annulé ou interrompu. Consultez votre portefeuille.",
    ),
  component: Page,
});
function Page() {
  return <BillingCancelPage />;
}
