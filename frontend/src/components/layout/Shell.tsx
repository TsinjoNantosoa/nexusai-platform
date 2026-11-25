import { useEffect, useRef, useState } from "react";
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
  Menu,
  X,
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
const publicNav = [
  { path: "/explore", key: "explore" },
  { path: "/pricing", key: "pricing" },
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
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const mobileMenuRef = useRef<HTMLElement>(null);
  const mobileMenuButtonRef = useRef<HTMLButtonElement>(null);
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
  const closeMobileMenu = () => setMobileMenuOpen(false);
  useEffect(() => {
    if (!mobileMenuOpen) return;
    const menu = mobileMenuRef.current;
    const trigger = mobileMenuButtonRef.current;
    const previous = document.activeElement as HTMLElement | null;
    const focusable = menu
      ? Array.from(
          menu.querySelectorAll<HTMLElement>(
            'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])',
          ),
        )
      : [];
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        closeMobileMenu();
        return;
      }
      if (event.key !== "Tab" || focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (!first || !last) return;
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);
    focusable[0]?.focus();
    return () => {
      document.body.style.overflow = "";
      document.removeEventListener("keydown", onKeyDown);
      if (previous?.isConnected) previous.focus();
      else trigger?.focus();
    };
  }, [mobileMenuOpen]);
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
            <nav className="public-desktop-nav" aria-label={t("nav.home")}>
              {publicNav.map((item) => (
                <Link key={item.key} to={item.path}>
                  {t(`nav.${item.key}`)}
                </Link>
              ))}
            </nav>
            <div className="public-actions public-desktop-actions">
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
            <Button
              ref={mobileMenuButtonRef}
              className="public-menu-trigger"
              variant="outline"
              size="icon"
              aria-label={t(mobileMenuOpen ? "nav.collapse" : "nav.expand")}
              aria-expanded={mobileMenuOpen}
              aria-controls="public-mobile-menu"
              onClick={() => setMobileMenuOpen((open) => !open)}
            >
              {mobileMenuOpen ? <X /> : <Menu />}
            </Button>
          </header>
          {mobileMenuOpen && (
            <div className="mobile-menu-layer">
              <button
                type="button"
                className="mobile-menu-backdrop"
                aria-label={t("common.close")}
                onClick={closeMobileMenu}
              />
              <nav
                ref={mobileMenuRef}
                id="public-mobile-menu"
                className="mobile-menu"
                aria-label={t("nav.home")}
                role="dialog"
                aria-modal="true"
              >
                {publicNav.map((item) => (
                  <Link
                    key={item.key}
                    to={item.path}
                    className="mobile-menu-link"
                    onClick={closeMobileMenu}
                  >
                    {t(`nav.${item.key}`)}
                    <ChevronRight size={16} />
                  </Link>
                ))}
                <div className="mobile-menu-actions">
                  <Button
                    variant="ghost"
                    onClick={() => {
                      language();
                      closeMobileMenu();
                    }}
                  >
                    <Globe />
                    {t("settings.language")}
                    <span className="mobile-menu-language">{i18n.language.toUpperCase()}</span>
                  </Button>
                  <Button asChild variant="outline" onClick={closeMobileMenu}>
                    <Link to="/login">{t("auth.login")}</Link>
                  </Button>
                  <Button asChild onClick={closeMobileMenu}>
                    <Link to="/register">
                      {t("auth.register")}
                      <ArrowUpRight />
                    </Link>
                  </Button>
                </div>
              </nav>
            </div>
          )}
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
                  className="language-toggle"
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
                  <span className="language-code">{i18n.language.toUpperCase()}</span>
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
