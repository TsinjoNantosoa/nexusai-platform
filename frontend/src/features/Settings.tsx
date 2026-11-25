import { useState } from "react";
import { useQueryClient, useQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  Download,
  Trash2,
  LogOut,
  RotateCcw,
  Smartphone,
  ArrowUpRight,
  Shield,
  Pencil,
  Check,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Gate,
  PageTitle,
  ConfirmDialog,
  ErrorNotice,
  Loading,
  Status,
  formatDate,
} from "@/components/shared";
import { useSession, useRefresh } from "@/services/hooks";
import { getApi, isMock } from "@/services/api";
import { characters } from "@/lib/characters";
import type { Report } from "@/services/types";
import { toast } from "sonner";
function SettingsContent() {
  const { t, i18n } = useTranslation();
  const session = useSession();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [deleting, setDeleting] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const end = async (reset: boolean) => {
    setBusy(true);
    try {
      if (reset) await getApi().reset();
      else await getApi().logout();
      qc.clear();
      await navigate({ to: "/" });
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  const pending = () => toast.info(t("common.pendingIntegration"));
  return (
    <>
      <PageTitle title={t("settings.title")} subtitle={t("settings.subtitle")} />
      <section className="settings-section">
        <h2>{t("settings.profile")}</h2>
        <div>
          <label htmlFor="profile-email">{t("auth.email")}</label>
          <input id="profile-email" value={session.data?.email ?? ""} readOnly />
          <div className="settings-buttons mt-5">
            <Button variant="outline" disabled={busy} onClick={() => void end(false)}>
              <LogOut />
              {t("auth.logout")}
            </Button>
            {isMock && (
              <Button variant="ghost" disabled={busy} onClick={() => void end(true)}>
                <RotateCcw />
                {t("demo.reset")}
              </Button>
            )}
          </div>
        </div>
      </section>
      <section className="settings-section">
        <h2>{t("settings.language")}</h2>
        <div className="flex gap-2">
          <Button
            variant={i18n.language === "fr" ? "secondary" : "outline"}
            aria-pressed={i18n.language === "fr"}
            onClick={() => void i18n.changeLanguage("fr")}
          >
            Français
          </Button>
          <Button
            variant={i18n.language === "en" ? "secondary" : "outline"}
            aria-pressed={i18n.language === "en"}
            onClick={() => void i18n.changeLanguage("en")}
          >
            English
          </Button>
        </div>
      </section>
      <section className="settings-section">
        <h2>{t("settings.memory")}</h2>
        <div>
          <p>{t("settings.memoryDesc")}</p>
          <Button variant="outline" asChild>
            <Link to="/conversations">
              {t("nav.conversations")}
              <ArrowUpRight />
            </Link>
          </Button>
        </div>
      </section>
      <section className="settings-section">
        <h2>{t("settings.privacy")}</h2>
        <div>
          <p>{t("settings.privacyDesc")}</p>
          <div className="settings-buttons">
            <Button variant="outline" onClick={pending}>
              <Download />
              {t("settings.export")}
            </Button>
            <Button variant="ghost" onClick={() => setDeleting(true)}>
              <Trash2 />
              {t("settings.delete")}
            </Button>
          </div>
          <p className="text-[10px] mt-5">{t("common.pendingIntegration")}</p>
        </div>
      </section>
      <section className="settings-section">
        <h2 className="flex items-center gap-2">
          <Smartphone size={20} />
          {t("settings.install")}
        </h2>
        <div>
          <p>{t("settings.installDesc")}</p>
          <p>{t("settings.ios")}</p>
          <p>{t("settings.android")}</p>
          <p>{t("settings.notTested")}</p>
        </div>
      </section>
      {session.data?.admin && (
        <Button variant="outline" asChild>
          <Link to="/admin">
            <Shield />
            {t("nav.admin")}
          </Link>
        </Button>
      )}
      {error ? <ErrorNotice error={error} /> : null}
      <ConfirmDialog
        open={deleting}
        onOpenChange={setDeleting}
        title={t("settings.deleteTitle")}
        description={t("settings.deleteDesc")}
        destructive
        onConfirm={() => {
          pending();
          setDeleting(false);
        }}
      />
    </>
  );
}
export function SettingsPage() {
  return (
    <div className="page-content">
      <Gate>
        <SettingsContent />
      </Gate>
    </div>
  );
}
function AdminContent() {
  const { t, i18n } = useTranslation();
  const [tab, setTab] = useState("catalogue");
  const reports = useQuery({ queryKey: ["reports"], queryFn: () => getApi().reports() });
  const refresh = useRefresh();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [selected, setSelected] = useState<Report | null>(null);
  const action = async (id: string, status: Report["status"]) => {
    setBusy(true);
    try {
      await getApi().moderate(id, status);
      await refresh();
      setSelected(null);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <PageTitle title={t("admin.title")} subtitle={t("admin.subtitle")} />
      <div className="notice">{t("admin.noPrivate")}</div>
      <div className="admin-tabs" role="group" aria-label={t("nav.admin")}>
        {["catalogue", "reports", "events"].map((key) => (
          <Button
            key={key}
            variant={tab === key ? "secondary" : "ghost"}
            aria-pressed={tab === key}
            onClick={() => setTab(key)}
          >
            {t(`admin.${key}`)}
          </Button>
        ))}
      </div>
      {tab === "catalogue" &&
        characters.map((c) => (
          <div key={c.id} className="admin-item">
            <div className="admin-item-main">
              <img src={c.image} alt={c.name} />
              <div>
                <h3>{c.name}</h3>
                <p>{t(`character.${c.id}.role`)}</p>
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={() => toast.info(t("common.pendingIntegration"))}
            >
              <Pencil />
              {t("admin.edit")}
            </Button>
          </div>
        ))}
      {tab === "reports" &&
        (reports.isPending ? (
          <Loading />
        ) : reports.error ? (
          <ErrorNotice error={reports.error} />
        ) : reports.data.length ? (
          reports.data.map((r) => (
            <div className="admin-item" key={r.id}>
              <div>
                <h3>{r.characterId.toUpperCase()}</h3>
                <p>{r.reason}</p>
                <p className="mt-2">
                  {formatDate(r.createdAt, i18n.language)} · {r.id}
                </p>
              </div>
              <Status status={r.status} />
              <Button variant="outline" size="sm" onClick={() => setSelected(r)}>
                {t("common.continue")}
                <ArrowUpRight />
              </Button>
            </div>
          ))
        ) : (
          <div className="empty-state">
            <Shield />
            <h2>{t("admin.none")}</h2>
          </div>
        ))}
      {tab === "events" &&
        ["webhooks", "blockedRequests", "audit"].map((key) => (
          <div className="admin-item" key={key}>
            <div>
              <h3>{t(`admin.${key}`)}</h3>
              <p>{t("common.pendingIntegration")}</p>
            </div>
            <span className="text-warning text-xs">{t("admin.notConnected")}</span>
          </div>
        ))}
      {error ? <ErrorNotice error={error} /> : null}
      <ConfirmDialog
        open={!!selected}
        onOpenChange={(o) => {
          if (!o) setSelected(null);
        }}
        title={t("admin.reports")}
        description={selected?.reason ?? ""}
        onConfirm={() => {
          if (selected) void action(selected.id, "reviewed");
        }}
        busy={busy}
      />
    </>
  );
}
export function AdminPage() {
  return (
    <div className="page-content">
      <Gate admin>
        <AdminContent />
      </Gate>
    </div>
  );
}
