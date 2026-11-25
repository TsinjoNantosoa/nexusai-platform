import { toast } from "sonner";
import i18n from "@/i18n";
export function isPreviewHost(hostname: string) {
  const host = hostname.toLowerCase();
  if (host === "localhost" || host === "127.0.0.1") return true;
  if (
    ["lovableproject.com", "lovableproject-dev.com", "beta.lovable.dev"].some(
      (domain) => host === domain || host.endsWith(`.${domain}`),
    )
  )
    return true;
  if (host === "id-preview--77d9d9c5-4c2e-4a79-976a-50e74577f021.lovable.app") return true;
  return ["lovable.app", "gpt-eng.com", "gptengineer.run"].some(
    (domain) =>
      host.endsWith(`.${domain}`) &&
      (/^(?:id-preview|preview)(?:-[a-z0-9]+)?--.+$/.test(host.split(".")[0] ?? "") ||
        host.split(".")[0] === "project--77d9d9c5-4c2e-4a79-976a-50e74577f021-dev"),
  );
}
export async function registerOfflineSupport() {
  if (!("serviceWorker" in navigator)) return;
  const refuse =
    !import.meta.env.PROD ||
    window.self !== window.top ||
    isPreviewHost(window.location.hostname) ||
    new URLSearchParams(window.location.search).get("sw") === "off";
  if (refuse) {
    const registrations = await navigator.serviceWorker.getRegistrations();
    await Promise.all(
      registrations
        .filter((r) =>
          [r.active, r.waiting, r.installing].some(
            (worker) => worker && new URL(worker.scriptURL).pathname === "/sw.js",
          ),
        )
        .map((r) => r.unregister()),
    );
    const names = await caches.keys();
    await Promise.all(
      names
        .filter(
          (name) =>
            name === "nexusai-public-pages" ||
            (/^workbox-precache-v\d+-/.test(name) && name.endsWith(`${window.location.origin}/`)),
        )
        .map((name) => caches.delete(name)),
    );
    return;
  }
  try {
    const registration = await navigator.serviceWorker.register("/sw.js");
    registration.addEventListener("updatefound", () => {
      const installing = registration.installing;
      installing?.addEventListener("statechange", () => {
        if (installing.state === "installed" && navigator.serviceWorker.controller) {
          toast.info(i18n.t("network.update"), {
            duration: Infinity,
            action: {
              label: i18n.t("network.refresh"),
              onClick: () => {
                if (document.querySelector('[data-operation-active="true"]')) return;
                registration.waiting?.postMessage({ type: "SKIP_WAITING" });
                window.location.reload();
              },
            },
          });
        }
      });
    });
  } catch {
    /* Offline installation is optional; never turn a network error into an app failure. */
  }
}
