import { createFileRoute } from "@tanstack/react-router";
import { ConversationsPage } from "@/features/Conversations";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/conversations")({
  head: () =>
    pageHead("Conversations", "Retrouvez et gérez vos conversations de démonstration NexusAI."),
  component: Page,
});
function Page() {
  return <ConversationsPage />;
}
