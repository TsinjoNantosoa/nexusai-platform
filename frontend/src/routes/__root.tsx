import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import {
  Outlet,
  Link,
  createRootRouteWithContext,
  HeadContent,
  useRouter,
  type ErrorComponentProps,
} from "@tanstack/react-router";
import { useEffect } from "react";
import { createPortal } from "react-dom";

import { reportAppError } from "../lib/error-reporting";
import "@/i18n";
import i18n from "@/i18n";
import { useTranslation } from "react-i18next";
import { Shell } from "@/components/layout/Shell";
import { Toaster } from "@/components/ui/sonner";
import { Button } from "@/components/ui/button";
import { registerOfflineSupport } from "@/lib/offline";

function NotFoundComponent() {
  const { t } = useTranslation();
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">{t("error.pageNotFound")}</h2>
        <p className="mt-2 text-sm text-muted-foreground">{t("error.not_found")}</p>
        <div className="mt-6">
          <Button asChild>
            <Link to="/">{t("nav.home")}</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

function ErrorComponent({ error, reset }: ErrorComponentProps) {
  const { t } = useTranslation();
  console.error(error);
  const router = useRouter();
  useEffect(() => {
    reportAppError(error, { boundary: "router_root_error_component" });
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-xl font-semibold tracking-tight text-foreground">
          {t("error.pageLoad")}
        </h1>
        <p className="mt-2 text-sm text-muted-foreground">{t("error.unknown")}</p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          <Button
            onClick={() => {
              router.invalidate();
              reset();
            }}
          >
            {t("common.retry")}
          </Button>
          <Button asChild variant="outline">
            <Link to="/">{t("nav.home")}</Link>
          </Button>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    // Replace these placeholders with the app's name and description when first building the app.
    // Each content route, / included, must still set its own head(). Never add og:image or
    // twitter:image here: every page without its own would inherit the root's preview image.
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "NexusAI — AI Character Chat, Memory & Billing" },
      { name: "description", content: "NexusAI, personnages IA et facturation de démonstration." },
      { name: "author", content: "Sandaniaina Tsinjo Nantosoa" },
      { property: "og:title", content: "NexusAI" },
      {
        property: "og:description",
        content: "Personnages IA, mémoire et portefeuille de démonstration.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
      { name: "theme-color", content: "#171820" },
    ],
    links: [
      { rel: "icon", href: "/favicon.ico", type: "image/x-icon" },
      { rel: "manifest", href: "/manifest.webmanifest" },
      { rel: "apple-touch-icon", href: "/icons/icon-192.png" },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap",
      },
    ],
  }),
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
  errorComponent: ErrorComponent,
});

function RootComponent() {
  const { queryClient } = Route.useRouteContext();
  useEffect(() => {
    const change = (language: string) => {
      document.documentElement.lang = language;
    };
    i18n.on("languageChanged", change);
    void registerOfflineSupport();
    return () => {
      i18n.off("languageChanged", change);
    };
  }, []);

  return (
    <>
      {typeof document === "undefined" ? null : createPortal(<HeadContent />, document.head)}
      <QueryClientProvider client={queryClient}>
        <Shell>
          <Outlet />
        </Shell>
        <Toaster position="bottom-right" />
      </QueryClientProvider>
    </>
  );
}
