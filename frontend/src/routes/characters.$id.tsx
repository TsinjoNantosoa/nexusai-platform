import { createFileRoute } from "@tanstack/react-router";
import { CharacterPage } from "@/features/Discovery";
import { pageHead } from "@/lib/meta";
import { characters } from "@/lib/characters";
export const Route = createFileRoute("/characters/$id")({
  head: ({ params }) => {
    const c = characters.find((c) => c.id === params.id);
    return pageHead(
      c ? `${c.name} · Personnage IA` : "Personnage introuvable",
      "Profil et personnalité de votre personnage artificiel NexusAI.",
      c?.image,
    );
  },
  component: Page,
});
function Page() {
  return <CharacterPage id={Route.useParams().id} />;
}
