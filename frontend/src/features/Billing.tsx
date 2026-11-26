import { useEffect, useRef, useState } from "react";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  Check,
  Gem,
  ArrowUpRight,
  CreditCard,
  CheckCircle2,
  Clock3,
  XCircle,
  LoaderCircle,
  RotateCcw,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import {
  PageTitle,
  Gate,
  Loading,
  ErrorNotice,
  Status,
  SearchInput,
  formatDate,
  formatMoney,
} from "@/components/shared";
import { getApi, productsOptions, isMock } from "@/services/api";
import { useOnline, useSession, useWallet, useRefresh } from "@/services/hooks";
import type { Order, PaymentScenario, Product, Wallet } from "@/services/types";
export function SubscriptionPanel({ wallet }: { wallet: Wallet }) {
  const { t, i18n } = useTranslation();
  const online = useOnline();
  const refresh = useRefresh();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const action = async (kind: "renew" | "fail" | "cancel" | "portal") => {
    setBusy(true);
    setError(null);
    try {
      if (kind === "portal") {
        const url = await getApi().portal();
        const parsed = new URL(url);
        if (parsed.protocol !== "https:" || parsed.hostname !== "billing.stripe.com")
          throw new Error("invalid_portal_url");
        window.location.assign(url);
      } else {
        await getApi().subscriptionAction(kind);
        await refresh();
      }
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <section className="subscription-band">
      <h2>{t("pricing.manage")}</h2>
      <div className="flex items-center flex-wrap gap-3">
        <strong>{wallet.subscription.status === "free" ? "Free" : "Premium"}</strong>
        <Status status={wallet.subscription.status} />
        {wallet.subscription.cancelAtPeriodEnd && (
          <span className="text-warning text-xs">{t("pricing.ends")}</span>
        )}
      </div>
      {wallet.subscription.renewsAt && (
        <p className="text-xs text-muted-foreground mt-4">
          {t("pricing.renewDate")} : {formatDate(wallet.subscription.renewsAt, i18n.language)}
        </p>
      )}
      {wallet.subscription.status !== "free" && (
        <div className="subscription-actions">
          {isMock ? (
            <>
              <Button
                variant="outline"
                size="sm"
                disabled={busy || !online || wallet.subscription.cancelAtPeriodEnd}
                onClick={() => void action("renew")}
              >
                <RotateCcw />
                {t("pricing.renew")}
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={busy || !online}
                onClick={() => void action("fail")}
              >
                {t("pricing.fail")}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                disabled={busy || !online || wallet.subscription.cancelAtPeriodEnd}
                onClick={() => void action("cancel")}
              >
                {t("pricing.cancel")}
              </Button>
            </>
          ) : null}
          <Button
            variant="outline"
            size="sm"
            disabled={busy || !online}
            onClick={() => void action("portal")}
          >
            <CreditCard />
            {t("pricing.portal")}
          </Button>
        </div>
      )}
      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}
    </section>
  );
}
export function PricingPage() {
  const { t, i18n } = useTranslation();
  const { data: products } = useSuspenseQuery(productsOptions);
  const session = useSession();
  const wallet = useWallet(!!session.data);
  const online = useOnline();
  const navigate = useNavigate();
  const refresh = useRefresh();
  const [selected, setSelected] = useState<Product | null>(null);
  const [scenario, setScenario] = useState<PaymentScenario>("success");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const key = useRef<string | null>(null);
  const choose = async (product: Product) => {
    if (!session.data) {
      await navigate({ to: "/login" });
      return;
    }
    setSelected(product);
    setError(null);
    key.current = crypto.randomUUID();
  };
  const checkout = async () => {
    if (!selected || !key.current || busy || !online) return;
    setBusy(true);
    setError(null);
    try {
      const order = await getApi().checkout(selected.sku, key.current);
      if (isMock) {
        await getApi().simulatePayment(order.id, scenario);
        if (scenario === "duplicate") await getApi().simulatePayment(order.id, scenario);
        await refresh();
        setSelected(null);
        await navigate({ to: "/billing/success", search: { order: order.id } });
      } else {
        if (!order.checkoutUrl) throw new Error("invalid_checkout_url");
        const parsed = new URL(order.checkoutUrl);
        if (parsed.protocol !== "https:" || parsed.hostname !== "checkout.stripe.com")
          throw new Error("invalid_checkout_url");
        window.location.assign(order.checkoutUrl);
      }
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="page-content">
      <span className="eyebrow">{t("pricing.kicker")}</span>
      <h1 className="page-title mt-3">{t("pricing.title")}</h1>
      <p className="page-subtitle">{t("pricing.subtitle")}</p>
      <div className="pricing-grid">
        {products.map((p) => (
          <article key={p.sku} className={`price-card ${p.sku === "plus" ? "featured" : ""}`}>
            <div className="popular">{p.sku === "plus" ? t("pricing.popular") : "\u00a0"}</div>
            <div className="flex items-center justify-between">
              <h2>{p.name}</h2>
              {p.subscription && <SparkleGem />}
            </div>
            <div className="price">{formatMoney(p.priceCents, i18n.language)}</div>
            <div className="price-note">
              {p.subscription
                ? t("pricing.month")
                : p.sku === "free"
                  ? t("pricing.welcome")
                  : t("pricing.oneTime")}
            </div>
            <div className="gems">
              <Gem size={20} />
              {p.gems.toLocaleString(i18n.language)} <span>{t("pricing.gems")}</span>
            </div>
            <p className="price-desc">
              {t(p.sku === "free" ? "pricing.welcome" : `pricing.${p.sku}`)}
            </p>
            <ul>
              <li>
                <Check />
                {t("pricing.included")}
              </li>
              <li>
                <Check />
                {t("pricing.memory")}
              </li>
              <li>
                <Check />
                {t(p.subscription ? "pricing.perPaidPeriod" : "pricing.noExpiry")}
              </li>
            </ul>
            <Button
              disabled={
                !online ||
                busy ||
                wallet.data?.inReview ||
                (!isMock && p.sku === "premium") ||
                (p.subscription && wallet.data?.subscription.status === "active")
              }
              variant={p.sku === "plus" || p.subscription ? "default" : "outline"}
              onClick={() => {
                if (p.sku === "free") void navigate({ to: session.data ? "/wallet" : "/register" });
                else void choose(p);
              }}
            >
              {p.sku === "free"
                ? session.data
                  ? t("pricing.current")
                  : t("auth.register")
                : p.subscription && !isMock
                  ? t("pricing.unavailable")
                  : p.subscription
                    ? wallet.data?.subscription.status === "active"
                      ? t("pricing.current")
                      : t("pricing.subscribe")
                    : t("pricing.choose")}
              <ArrowUpRight />
            </Button>
          </article>
        ))}
      </div>
      <p className="text-xs text-muted-foreground leading-7 flex items-center gap-2">
        <CreditCard size={16} />
        {t("pricing.noReal")}
      </p>
      {wallet.data && <SubscriptionPanel wallet={wallet.data} />}
      <Dialog
        open={!!selected}
        onOpenChange={(open) => {
          if (!open && !busy) setSelected(null);
        }}
      >
        <DialogContent className="dialog-content" data-operation-active={busy}>
          <DialogTitle>{t(isMock ? "checkout.title" : "pricing.choose")}</DialogTitle>
          <DialogDescription>{t(isMock ? "checkout.desc" : "billing.observe")}</DialogDescription>
          {selected && (
            <div className="flex justify-between items-center border-y border-border py-5">
              <div>
                <strong>{selected.name}</strong>
                <p className="text-xs text-violet mt-2">
                  {selected.gems} {t("pricing.gems")}
                </p>
              </div>
              <strong className="text-xl font-display">
                {formatMoney(selected.priceCents, i18n.language)}
              </strong>
            </div>
          )}
          {isMock && (
            <fieldset>
              <legend className="text-xs mb-3">{t("demo.scenario")}</legend>
              <div className="grid grid-cols-2 gap-3">
                {(["success", "pending", "declined", "duplicate", "canceled"] as const).map((s) => (
                  <label key={s} className="flex items-center gap-2 text-xs cursor-pointer">
                    <input
                      type="radio"
                      name="scenario"
                      checked={scenario === s}
                      onChange={() => setScenario(s)}
                      disabled={busy}
                    />
                    {t(`checkout.${s}`)}
                  </label>
                ))}
              </div>
            </fieldset>
          )}
          {error ? <ErrorNotice error={error} /> : null}
          <Button onClick={() => void checkout()} disabled={busy || !online}>
            {busy ? <LoaderCircle className="animate-spin" /> : <CreditCard />}
            {t(isMock ? "checkout.action" : "common.continue")}
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  );
}
function SparkleGem() {
  return <Gem size={19} className="text-violet" />;
}
function WalletContent() {
  const { t, i18n } = useTranslation();
  const wallet = useWallet();
  const entries = useQuery({ queryKey: ["entries"], queryFn: () => getApi().entries() });
  const orders = useQuery({
    queryKey: ["orders"],
    queryFn: () => getApi().orders(),
    enabled: isMock,
  });
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(0);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const online = useOnline();
  const refresh = useRefresh();
  if (wallet.isPending || entries.isPending) return <Loading />;
  if (wallet.error || entries.error)
    return (
      <ErrorNotice
        error={wallet.error ?? entries.error}
        retry={() => {
          void wallet.refetch();
          void entries.refetch();
        }}
      />
    );
  const rows = (entries.data ?? []).filter(
    (e) =>
      (filter === "all" || filter === e.type) &&
      e.reference.toLowerCase().includes(search.toLowerCase()),
  );
  const pages = Math.max(1, Math.ceil(rows.length / 5));
  const visible = rows.slice(page * 5, page * 5 + 5);
  const w = wallet.data;
  const simulate = async (id: string, scenario: PaymentScenario) => {
    setBusy(true);
    setError(null);
    try {
      await getApi().simulatePayment(id, scenario);
      await refresh();
      if (scenario === "duplicate") toast.success(t("billing.duplicateNotice"));
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div data-operation-active={busy}>
      <PageTitle title={t("wallet.title")} subtitle={t("wallet.subtitle")}>
        <Button asChild disabled={!online}>
          <Link to="/pricing">
            <Gem />
            {t("wallet.buy")}
            <ArrowUpRight />
          </Link>
        </Button>
      </PageTitle>
      {w.inReview && <div className="notice warning">{t("wallet.review")}</div>}
      <section className="wallet-overview">
        <div>
          <span className="eyebrow">{t("wallet.available")}</span>
          <div className="wallet-total">
            <Gem />
            <span data-testid="wallet-balance">{w.balance.toLocaleString(i18n.language)}</span>
            <small>{t("pricing.gems")}</small>
          </div>
          <p className="text-xs text-muted-foreground">
            {Math.floor(w.balance / 2)} {t("wallet.messages")}
          </p>
        </div>
        <div className="self-center">
          <div className="flex items-center gap-3">
            <CreditCard className="text-electric" size={20} />
            <strong className="text-lg">
              {w.subscription.status === "free" ? "Free" : "Premium"}
            </strong>
            <Status status={w.subscription.status} />
          </div>
          <p className="text-xs text-muted-foreground leading-7 mt-4">
            {w.subscription.cancelAtPeriodEnd ? t("pricing.ends") : t("pricing.noExpiry")}
          </p>
          <Button asChild variant="ghost" size="sm">
            <Link to="/pricing">
              {t("pricing.manage")}
              <ArrowUpRight />
            </Link>
          </Button>
        </div>
      </section>
      <div className="section-heading">
        <h2>{t("wallet.history")}</h2>
        <span>{t("demo.banner")}</span>
      </div>
      <div className="explore-tools">
        <SearchInput
          value={search}
          onChange={(v) => {
            setSearch(v);
            setPage(0);
          }}
          placeholder={t("wallet.referenceSearch")}
        />
        <select
          aria-label={t("common.type")}
          value={filter}
          onChange={(e) => {
            setFilter(e.target.value);
            setPage(0);
          }}
        >
          <option value="all">{t("common.all")}</option>
          {["welcome", "purchase", "subscription", "message", "restitution"].map((v) => (
            <option key={v} value={v}>
              {t(`entry.${v}`)}
            </option>
          ))}
        </select>
      </div>
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              {["type", "date", "amount", "reference", "status"].map((c) => (
                <th key={c}>{t(`common.${c}`)}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {visible.map((e) => (
              <tr key={e.id}>
                <td>
                  <span className="flex items-center gap-2">
                    <Gem
                      size={14}
                      className={e.amount > 0 ? "text-violet" : "text-muted-foreground"}
                    />
                    {t(`entry.${e.type}`)}
                  </span>
                </td>
                <td>{formatDate(e.createdAt, i18n.language)}</td>
                <td className={e.amount > 0 ? "text-success" : "text-muted-foreground"}>
                  {e.amount > 0 ? "+" : ""}
                  {e.amount}
                </td>
                <td className="table-ref">{e.reference}</td>
                <td>
                  <Status status={e.status} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!rows.length && (
        <p className="text-muted-foreground text-xs py-10 text-center">
          {t("wallet.noTransactions")}
        </p>
      )}
      <div className="pagination">
        <span>
          {page + 1} / {pages}
        </span>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 0}
            onClick={() => setPage(page - 1)}
          >
            {t("common.previous")}
          </Button>
          <Button
            variant="outline"
            size="sm"
            disabled={page + 1 >= pages}
            onClick={() => setPage(page + 1)}
          >
            {t("common.next")}
          </Button>
        </div>
      </div>
      {isMock && (
        <section className="mt-10">
          <div className="section-heading">
            <h2>{t("wallet.pending")}</h2>
          </div>
          {orders.data
            ?.filter((o) => o.status === "pending")
            .map((o) => (
              <div className="admin-item" key={o.id}>
                <div>
                  <strong>{o.sku.toUpperCase()}</strong>
                  <p className="table-ref mt-2">{o.id}</p>
                  <Status status={o.status} />
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={busy || !online}
                    onClick={() => void simulate(o.id, "success")}
                  >
                    {t("billing.confirmDemo")}
                  </Button>
                  <Button asChild variant="ghost" size="sm">
                    <Link to="/billing/success" search={{ order: o.id }}>
                      {t("common.status")}
                      <ArrowUpRight />
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          {!orders.data?.some((o) => o.status === "pending") && (
            <p className="text-xs text-muted-foreground">{t("wallet.noOrders")}</p>
          )}
        </section>
      )}
      {isMock && orders.data?.some((o) => o.status === "paid") && (
        <section className="mt-6">
          {orders.data
            .filter((o) => o.status === "paid")
            .slice(0, 1)
            .map((o) => (
              <Button
                key={o.id}
                variant="ghost"
                size="sm"
                disabled={busy || !online}
                onClick={() => void simulate(o.id, "duplicate")}
              >
                <RotateCcw />
                {t("billing.duplicate")}
              </Button>
            ))}
        </section>
      )}
      {error ? <ErrorNotice error={error} /> : null}
    </div>
  );
}
export function WalletPage() {
  return (
    <div className="page-content">
      <Gate>
        <WalletContent />
      </Gate>
    </div>
  );
}
function BillingSuccessContent({ orderId }: { orderId: string }) {
  const { t } = useTranslation();
  const [order, setOrder] = useState<Order | null>(null);
  const [phase, setPhase] = useState<"verifying" | "pending" | "confirmed" | "failed" | "notFound">(
    "verifying",
  );
  const [error, setError] = useState<unknown>(null);
  const [retry, setRetry] = useState(0);
  const refresh = useRefresh();
  const refreshRef = useRef(refresh);
  refreshRef.current = refresh;
  useEffect(() => {
    let canceled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let polls = 0;
    setPhase("verifying");
    setError(null);
    const tick = async () => {
      if (!orderId) {
        setPhase("notFound");
        return;
      }
      try {
        const o = await getApi().order(orderId);
        if (canceled) return;
        setOrder(o);
        if (o.status === "paid") {
          setPhase("confirmed");
          await refreshRef.current();
          return;
        }
        if (["failed", "canceled", "expired"].includes(o.status)) {
          setPhase("failed");
          return;
        }
        setPhase("pending");
        polls++;
        if (polls < 12) timer = setTimeout(() => void tick(), 2500);
      } catch (e) {
        if (!canceled) {
          setError(e);
          setPhase("notFound");
        }
      }
    };
    void tick();
    return () => {
      canceled = true;
      if (timer) clearTimeout(timer);
    };
  }, [orderId, retry]);
  const Icon =
    phase === "confirmed"
      ? CheckCircle2
      : phase === "failed" || phase === "notFound"
        ? XCircle
        : phase === "verifying"
          ? LoaderCircle
          : Clock3;
  return (
    <section
      className="billing-result"
      data-operation-active={phase === "verifying" || phase === "pending"}
    >
      <Icon
        className={
          phase === "confirmed"
            ? "text-success"
            : phase === "failed"
              ? "text-destructive"
              : "text-warning"
        }
      />
      <h1 aria-live="polite">{t(`billing.${phase}`)}</h1>
      <p>
        {t(
          phase === "confirmed"
            ? isMock
              ? "billing.confirmedDesc"
              : "billing.apiConfirmed"
            : phase === "failed"
              ? "billing.failedDesc"
              : "billing.pendingDesc",
        )}
      </p>
      {phase === "confirmed" && order && isMock && (
        <div className="confirmed-gems">
          +{order.gems} {t("pricing.gems")}
        </div>
      )}
      <div className="notice mt-6">{t("billing.observe")}</div>
      {error ? (
        <div className="mt-4">
          <ErrorNotice error={error} />
        </div>
      ) : null}
      <div className="billing-actions">
        <Button asChild>
          <Link to="/wallet">{t("billing.backWallet")}</Link>
        </Button>
        <Button asChild variant="outline">
          <Link to="/pricing">{t("billing.backPricing")}</Link>
        </Button>
        {phase !== "confirmed" && (
          <Button variant="ghost" onClick={() => setRetry(retry + 1)}>
            {t("common.retry")}
          </Button>
        )}
      </div>
    </section>
  );
}
export function BillingSuccessPage({ orderId }: { orderId: string }) {
  return (
    <div className="page-content">
      <Gate>
        <BillingSuccessContent orderId={orderId} />
      </Gate>
    </div>
  );
}
export function BillingCancelPage() {
  const { t } = useTranslation();
  return (
    <div className="page-content">
      <section className="billing-result">
        <XCircle className="text-warning" />
        <h1>{t("billing.cancelTitle")}</h1>
        <p>{t("billing.cancelDesc")}</p>
        <div className="billing-actions">
          <Button asChild>
            <Link to="/pricing">{t("billing.backPricing")}</Link>
          </Button>
          <Button asChild variant="outline">
            <Link to="/wallet">{t("billing.backWallet")}</Link>
          </Button>
        </div>
      </section>
    </div>
  );
}
