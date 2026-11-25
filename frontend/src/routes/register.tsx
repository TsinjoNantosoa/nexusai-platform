import { createFileRoute } from "@tanstack/react-router";
import { AuthPage } from "@/features/Auth";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/register")({
  head: () =>
    pageHead(
      "Créer un compte",
      "Créez un compte NexusAI de démonstration avec 20 gemmes de bienvenue.",
    ),
  component: Page,
});
function Page() {
  return <AuthPage registration />;
}
