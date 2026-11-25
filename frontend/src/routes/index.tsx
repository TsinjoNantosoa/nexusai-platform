import { createFileRoute } from "@tanstack/react-router";
import { LandingPage } from "@/features/Discovery";
import { pageHead } from "@/lib/meta";
import { catalogueOptions, productsOptions } from "@/services/api";
import { characters } from "@/lib/characters";
export const Route = createFileRoute("/")({
  loader: ({ context }) =>
    Promise.all([
      context.queryClient.ensureQueryData(catalogueOptions),
      context.queryClient.ensureQueryData(productsOptions),
    ]),
  head: () =>
    pageHead(
      "Accueil",
      "Personnages IA, conversations et facturation simulée NexusAI.",
      characters.find((c) => c.id === "luna")?.image,
    ),
  component: Page,
});
function Page() {
  return <LandingPage />;
}
