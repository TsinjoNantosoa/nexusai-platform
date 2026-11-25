import { createFileRoute } from "@tanstack/react-router";
import { AdminPage } from "@/features/Settings";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/admin")({
  head: () =>
    pageHead(
      "Administration",
      "Espace de modération et de gestion du catalogue NexusAI réservé à l’administrateur.",
    ),
  component: Page,
});
function Page() {
  return <AdminPage />;
}
