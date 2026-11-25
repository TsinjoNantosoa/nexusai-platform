import { createFileRoute } from "@tanstack/react-router";
import { PricingPage } from "@/features/Billing";
import { pageHead } from "@/lib/meta";
import { productsOptions } from "@/services/api";
export const Route = createFileRoute("/pricing")({
  loader: ({ context }) => context.queryClient.ensureQueryData(productsOptions),
  head: () =>
    pageHead(
      "Offres et abonnement",
      "Découvrez Free, Starter, Plus et Premium dans la démonstration NexusAI.",
    ),
  component: Page,
});
function Page() {
  return <PricingPage />;
}
