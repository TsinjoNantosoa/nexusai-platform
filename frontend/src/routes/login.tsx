import { createFileRoute } from "@tanstack/react-router";
import { AuthPage } from "@/features/Auth";
import { pageHead } from "@/lib/meta";
export const Route = createFileRoute("/login")({
  head: () =>
    pageHead(
      "Connexion",
      "Connectez-vous à votre espace NexusAI ou utilisez un compte de démonstration.",
    ),
  component: Page,
});
function Page() {
  return <AuthPage />;
}
