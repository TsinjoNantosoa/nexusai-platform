import { createFileRoute } from "@tanstack/react-router";
import { ExplorePage } from "@/features/Discovery";
import { pageHead } from "@/lib/meta";
import { catalogueOptions } from "@/services/api";
import { characters } from "@/lib/characters";
export const Route = createFileRoute("/explore")({
  loader: ({ context }) => context.queryClient.ensureQueryData(catalogueOptions),
  head: () =>
    pageHead(
      "Explorer les personnages",
      "Découvrez Atlas, Luna, Nova et Echo, quatre personnages IA NexusAI.",
      characters.find((c) => c.id === "luna")?.image,
    ),
  component: Page,
});
function Page() {
  return <ExplorePage />;
}
