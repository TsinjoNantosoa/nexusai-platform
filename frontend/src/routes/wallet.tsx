import { createFileRoute } from "@tanstack/react-router";
import { WalletPage } from "@/features/Billing";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/wallet")({
  head: () =>
    pageHead(
      "Portefeuille",
      "Consultez votre solde de gemmes et votre historique de transactions NexusAI.",
    ),
  component: Page,
});
function Page() {
  return <WalletPage />;
}
