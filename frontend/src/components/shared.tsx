import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import { AlertCircle, LoaderCircle, Sparkles, Search } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { ApiError } from "@/services/types";
import { useSession } from "@/services/hooks";
import type { ReactNode } from "react";
export function Brand() {
  return (
    <Link to="/" className="logo" aria-label="NexusAI">
      <span className="logo-mark">
        <Sparkles size={20} />
      </span>
      <span className="logo-word">
        Nexus<em>AI</em>
      </span>
    </Link>
  );
}
export function Loading() {
  const { t } = useTranslation();
  return (
    <div className="empty-state" role="status">
      <LoaderCircle className="animate-spin" />
      <p>{t("common.loading")}</p>
    </div>
  );
}
export function ErrorNotice({ error, retry }: { error: unknown; retry?: () => void }) {
  const { t } = useTranslation();
  const code = error instanceof ApiError ? error.code : "unknown";
  return (
    <div className="notice error" role="alert">
      <div className="flex items-center gap-2">
        <AlertCircle size={17} />
        {t(`error.${code}`, { defaultValue: t("error.unknown") })}
      </div>
      {error instanceof ApiError && error.requestId && (
        <p className="table-ref">{error.requestId}</p>
      )}
      {retry && (
        <Button onClick={retry} variant="outline" size="sm" className="mt-3">
          {t("common.retry")}
        </Button>
      )}
    </div>
  );
}
export function Gate({ children, admin = false }: { children: ReactNode; admin?: boolean }) {
  const s = useSession();
  const { t } = useTranslation();
  if (s.isPending) return <Loading />;
  if (s.error) return <ErrorNotice error={s.error} retry={() => void s.refetch()} />;
  if (!s.data)
    return (
      <div className="empty-state">
        <Sparkles />
        <h2>{t("auth.required")}</h2>
        <p>{t("demo.notice")}</p>
        <Button asChild>
          <Link to="/login">{t("auth.login")}</Link>
        </Button>
      </div>
    );
  if (admin && !s.data.admin)
    return (
      <div className="empty-state">
        <AlertCircle />
        <h2>{t("admin.denied")}</h2>
      </div>
    );
  return children;
}
export function PageTitle({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle?: string;
  children?: ReactNode;
}) {
  return (
    <div className="page-title-row">
      <div>
        <h1 className="page-title">{title}</h1>
        {subtitle && <p className="page-subtitle">{subtitle}</p>}
      </div>
      {children}
    </div>
  );
}
export function SearchInput({
  value,
  onChange,
  placeholder,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder: string;
}) {
  return (
    <div className="search-field">
      <Search />
      <input
        aria-label={placeholder}
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
      />
    </div>
  );
}
export function ConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  destructive = false,
  busy = false,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  title: string;
  description: string;
  onConfirm: () => void;
  destructive?: boolean;
  busy?: boolean;
}) {
  const { t } = useTranslation();
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="dialog-content">
        <DialogTitle>{title}</DialogTitle>
        <DialogDescription>{description}</DialogDescription>
        <div className="flex justify-end gap-2 mt-4">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            {t("common.cancel")}
          </Button>
          <Button
            variant={destructive ? "destructive" : "default"}
            disabled={busy}
            onClick={onConfirm}
          >
            {t("common.confirm")}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
export function Status({ status }: { status: string }) {
  const { t } = useTranslation();
  return (
    <span className={`status-tag ${status}`}>
      <span className="status-dot" />
      {t(`status.${status}`)}
    </span>
  );
}
export function formatMoney(cents: number, lang: string) {
  return new Intl.NumberFormat(lang, { style: "currency", currency: "EUR" }).format(cents / 100);
}
export function formatDate(value: string, lang: string) {
  return new Intl.DateTimeFormat(lang, { day: "numeric", month: "short", year: "numeric" }).format(
    new Date(value),
  );
}
