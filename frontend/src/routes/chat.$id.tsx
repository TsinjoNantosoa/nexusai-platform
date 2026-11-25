import { createFileRoute } from "@tanstack/react-router";
import { ChatPage } from "@/features/Conversations";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/chat/$id")({
  head: () =>
    pageHead(
      "Conversation IA",
      "Discutez avec votre personnage NexusAI et gérez votre mémoire de conversation.",
    ),
  component: Page,
});
function Page() {
  return <ChatPage id={Route.useParams().id} />;
}
