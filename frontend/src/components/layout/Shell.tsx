import { useState } from "react";
import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";
import {
  Compass,
  MessageSquare,
  Gem,
  CreditCard,
  Settings,
  Shield,
  PanelLeftClose,
  PanelLeftOpen,
  ArrowUpRight,
  LogOut,
  ChevronRight,
  Globe,
  FlaskConical,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Brand } from "@/components/shared";
import { useOnline, useSession, useWallet } from "@/services/hooks";
import { getApi, isMock } from "@/services/api";
import { toast } from "sonner";
import type { ReactNode } from "react";
const nav = [
  { path: "/explore", key: "explore", icon: Compass },
  { path: "/conversations", key: "conversations", icon: MessageSquare },
  { path: "/wallet", key: "wallet", icon: Gem },
  { path: "/pricing", key: "pricing", icon: CreditCard },
  { path: "/settings", key: "settings", icon: Settings },
] as const;
export function Shell({ children }: { children: ReactNode }) {
  const { t, i18n } = useTranslation();
  const path = useRouterState({ select: (s) => s.location.pathname });
  const session = useSession();
  const wallet = useWallet(!!session.data);
  const online = useOnline();
  const qc = useQueryClient();
  const navigate = useNavigate();
  const [collapsed, setCollapsed] = useState(false);
  const isPublic = ["/", "/login", "/register"].includes(path);
  const active = path.startsWith("/chat")
    ? "conversations"
    : path.startsWith("/characters")
      ? "explore"
      : (nav.find((n) => n.path === path)?.key ?? (path === "/admin" ? "admin" : "wallet"));
  const logout = async () => {
    try {
      await getApi().logout();
      qc.clear();
      await navigate({ to: "/" });
    } catch {
      toast.error(t("error.unknown"));
    }
  };
  const language = () => {
    void i18n.changeLanguage(i18n.language === "fr" ? "en" : "fr");
  };
  const user = session.data;
  return (
    <>
      <div className="demo-strip">
        <FlaskConical size={12} />
        <span>{t("demo.banner")}</span>
        {isMock && <span className="demo-detail">{t("demo.disconnected")}</span>}
      </div>
      {!online && (
        <div className="offline-strip" role="status">
          {t("network.offline")}
        </div>
      )}
      {isPublic ? (
        <>
          <header className="public-header">
            <Brand />
            <nav>
              <Link to="/explore">{t("nav.explore")}</Link>
              <Link to="/pricing">{t("nav.pricing")}</Link>
            </nav>
            <div className="public-actions">
              <Button
                variant="ghost"
                size="icon"
                title={t("settings.language")}
                aria-label={t("settings.language")}
                onClick={language}
              >
                <Globe />
              </Button>
              <Button asChild variant="ghost" size="sm">
                <Link to="/login">{t("auth.login")}</Link>
              </Button>
              <Button asChild size="sm">
                <Link to="/register">
                  {t("auth.register")}
                  <ArrowUpRight />
                </Link>
              </Button>
            </div>
          </header>
          {children}
          <footer className="public-footer">
            <span>NexusAI</span>
            <span>{t("landing.footer")}</span>
            <span>{t("demo.banner")}</span>
          </footer>
        </>
      ) : (
        <div className={`app-frame ${collapsed ? "collapsed" : ""}`}>
          <aside className="sidebar">
            <Brand />
            <nav className="side-nav" aria-label={t("nav.explore")}>
              <div className="nav-section">{t("nav.workspace")}</div>
              {nav.map((n) => (
                <Link
                  key={n.key}
                  to={n.path}
                  title={t(`nav.${n.key}`)}
                  data-active={active === n.key}
                >
                  <n.icon />
                  <span className="side-label">{t(`nav.${n.key}`)}</span>
                </Link>
              ))}
              {user?.admin && (
                <Link to="/admin" data-active={active === "admin"}>
                  <Shield />
                  <span className="side-label">{t("nav.admin")}</span>
                </Link>
              )}
            </nav>
            <div className="sidebar-bottom">
              <div className="sidebar-plan">
                <strong className="flex items-center gap-2">
                  <Gem size={15} className="text-violet" />
                  {t("pricing.title")}
                </strong>
                <p>{t("pricing.starter")}</p>
                <Button asChild variant="outline" size="sm" className="w-full">
                  <Link to="/pricing">
                    {t("wallet.buy")}
                    <ArrowUpRight />
                  </Link>
                </Button>
              </div>
              <div className="sidebar-user">
                <div className="user-avatar">
                  {user ? user.email.slice(0, 1).toUpperCase() : "N"}
                </div>
                <div className="user-info">
                  <span>{user?.email ?? t("demo.account")}</span>
                  <span className="text-muted-foreground mt-1">
                    {wallet.data?.subscription.status === "free" || !wallet.data
                      ? "Free"
                      : "Premium"}
                  </span>
                </div>
                {user && (
                  <Button
                    variant="ghost"
                    size="icon"
                    title={t("auth.logout")}
                    aria-label={t("auth.logout")}
                    onClick={() => void logout()}
                  >
                    <LogOut size={14} />
                  </Button>
                )}
              </div>
            </div>
          </aside>
          <div className="workspace">
            <header className="workspace-header">
              <div className="header-path">
                <Button
                  variant="ghost"
                  size="icon"
                  title={t(collapsed ? "nav.expand" : "nav.collapse")}
                  aria-label={t(collapsed ? "nav.expand" : "nav.collapse")}
                  onClick={() => setCollapsed(!collapsed)}
                >
                  {collapsed ? <PanelLeftOpen /> : <PanelLeftClose />}
                </Button>
                <span>NexusAI</span>
                <ChevronRight size={12} />
                <span>{t(`nav.${active}`)}</span>
              </div>
              <div className="header-actions">
                <span className="mobile-logo">
                  <Brand />
                </span>
                {user ? (
                  <Link to="/wallet" className="balance-chip">
                    <Gem size={15} />
                    <strong>{wallet.data?.balance ?? "—"}</strong>
                    <span className="hidden sm:inline">{t("pricing.gems")}</span>
                  </Link>
                ) : (
                  <Button asChild size="sm">
                    <Link to="/login">{t("auth.login")}</Link>
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label={t("settings.language")}
                  title={t("settings.language")}
                  onClick={language}
                >
                  {i18n.language.toUpperCase()}
                  <Globe size={13} />
                </Button>
                {user && (
                  <Button asChild variant="ghost" size="icon" aria-label={t("nav.settings")}>
                    <Link to="/settings">
                      <div className="user-avatar">{user.email.slice(0, 1).toUpperCase()}</div>
                    </Link>
                  </Button>
                )}
              </div>
            </header>
            <main>{children}</main>
          </div>
          <nav className="mobile-nav" aria-label={t("nav.home")}>
            {nav.map((n) => (
              <Link key={n.key} to={n.path} data-active={active === n.key}>
                <n.icon />
                <span>{t(`nav.${n.key}`)}</span>
              </Link>
            ))}
          </nav>
        </div>
      )}
    </>
  );
}
