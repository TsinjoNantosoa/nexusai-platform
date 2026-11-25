import { createFileRoute } from "@tanstack/react-router";
import { SettingsPage } from "@/features/Settings";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/settings")({
  head: () =>
    pageHead(
      "Paramètres",
      "Gérez les préférences, la langue et la confidentialité de votre espace NexusAI.",
    ),
  component: Page,
});
function Page() {
  return <SettingsPage />;
}
