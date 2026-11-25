import { useState } from "react";
import { useQuery, useSuspenseQuery } from "@tanstack/react-query";
import { Link, useNavigate } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  ArrowRight,
  ArrowUpRight,
  Gem,
  Sparkles,
  Check,
  Brain,
  Compass,
  Flag,
  Ban,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import { PageTitle, SearchInput, Loading, ErrorNotice, Gate } from "@/components/shared";
import { characters, type Character } from "@/lib/characters";
import { catalogueOptions, productsOptions, getApi } from "@/services/api";
import { useOnline, useSession, useRefresh } from "@/services/hooks";
import { toast } from "sonner";
export function CharacterCard({ character }: { character: Character }) {
  const { t } = useTranslation();
  return (
    <article className="character-card">
      <Link to="/characters/$id" params={{ id: character.id }} className="block character-image">
        <img
          src={character.image}
          alt={`${character.name} — ${t("character.ai")}`}
          loading="lazy"
        />
        <span className="ai-label">
          <Sparkles size={9} />
          {t("character.ai")}
        </span>
        <div className="character-name">
          <h3>{character.name}</h3>
          <p className={`tone-${character.tone}`}>{t(`character.${character.id}.role`)}</p>
        </div>
      </Link>
      <div className="character-body">
        <p>{t(`character.${character.id}.desc`)}</p>
        <div className="character-tags">{t(`character.${character.id}.tags`)}</div>
        <Button asChild className="w-full start-button" variant="secondary" size="sm">
          <Link to="/characters/$id" params={{ id: character.id }}>
            {t("explore.profile")}
            <ArrowUpRight />
          </Link>
        </Button>
        <div className="character-card-footer">
          <span>
            <Gem size={10} />
            {t("explore.cost")}
          </span>
          <span>
            <Brain size={10} />
            {t("chat.memory")}
          </span>
        </div>
      </div>
    </article>
  );
}
export function LandingPage() {
  const { t, i18n } = useTranslation();
  const { data } = useSuspenseQuery(catalogueOptions);
  const { data: products } = useSuspenseQuery(productsOptions);
  return (
    <main>
      <section className="hero">
        <div className="hero-art">
          {data.map((c) => (
            <img key={c.id} src={c.image} alt={`${c.name} — ${t("character.ai")}`} />
          ))}
        </div>
        <div className="hero-inner">
          <div className="eyebrow">{t("landing.kicker")}</div>
          <h1>{t("landing.title")}</h1>
          <h2>{t("landing.subtitle")}</h2>
          <p>{t("landing.description")}</p>
          <div className="hero-buttons">
            <Button size="lg" asChild>
              <Link to="/login">
                {t("landing.start")}
                <ArrowRight />
              </Link>
            </Button>
            <Button size="lg" variant="outline" asChild>
              <Link to="/explore">{t("landing.discover")}</Link>
            </Button>
          </div>
          <div className="hero-facts">
            <span>
              <Check size={13} />
              {t("landing.welcome")}
            </span>
            <span>
              <Check size={13} />
              {t("landing.noCard")}
            </span>
          </div>
        </div>
      </section>
      <section className="public-section">
        <span className="eyebrow">{t("explore.catalogue")}</span>
        <h2>{t("landing.characters")}</h2>
        <p>{t("landing.charactersSub")}</p>
        <div className="character-grid">
          {data.map((c) => (
            <CharacterCard key={c.id} character={c} />
          ))}
        </div>
      </section>
      <section className="public-section">
        <span className="eyebrow">NEXUSAI</span>
        <h2>{t("landing.workflow")}</h2>
        <div className="steps">
          {[1, 2, 3].map((i) => (
            <div key={i}>
              <span>0{i}</span>
              <h3>{t(`landing.step${i}`)}</h3>
            </div>
          ))}
        </div>
      </section>
      <section className="public-section border-t border-border">
        <h2>{t("pricing.title")}</h2>
        <p>{t("pricing.noReal")}</p>
        <div className="flex flex-wrap gap-x-12 gap-y-5 my-7">
          {products
            .filter((p) => p.sku !== "free")
            .map((p) => (
              <div key={p.sku}>
                <strong className="text-violet">{p.name}</strong>
                <p className="mt-2">
                  {new Intl.NumberFormat(i18n.language, {
                    style: "currency",
                    currency: p.currency,
                  }).format(p.priceCents / 100)}{" "}
                  {p.subscription ? t("pricing.month") : ""} ·{" "}
                  {p.gems.toLocaleString(i18n.language)} {t("pricing.gems")}
                </p>
              </div>
            ))}
        </div>
        <Button asChild variant="outline">
          <Link to="/pricing">
            {t("nav.pricing")}
            <ArrowRight />
          </Link>
        </Button>
      </section>
      <section className="public-section">
        <h2>{t("landing.faq")}</h2>
        {[1, 2, 3, 4].map((i) => (
          <details className="faq-item" key={i}>
            <summary>{t(`landing.q${i}`)}</summary>
            <p>{t(`landing.a${i}`)}</p>
          </details>
        ))}
      </section>
    </main>
  );
}
export function ExplorePage() {
  const { t } = useTranslation();
  const { data } = useSuspenseQuery(catalogueOptions);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const luna = data.find((c) => c.id === "luna");
  const filtered = data.filter(
    (c) =>
      (category === "all" || category === c.category) &&
      `${c.name} ${t(`character.${c.id}.role`)} ${t(`character.${c.id}.desc`)}`
        .toLowerCase()
        .includes(search.toLowerCase()),
  );
  return (
    <div className="page-content">
      <span className="eyebrow">{t("explore.kicker")}</span>
      <h1 className="page-title mt-3">{t("explore.title")}</h1>
      <p className="page-subtitle">{t("explore.subtitle")}</p>
      <section className="spotlight">
        {luna && <img src={luna.image} alt="Luna" />}
        <div className="spotlight-content">
          <span className="eyebrow flex items-center gap-2">
            <Sparkles size={12} />
            {t("explore.featured")}
          </span>
          <h2>{t("explore.spotlight")}</h2>
          <p>{t("explore.spotlightSub")}</p>
          <Button asChild size="sm">
            <Link to="/characters/$id" params={{ id: "luna" }}>
              {t("explore.startLuna")}
              <ArrowUpRight />
            </Link>
          </Button>
        </div>
      </section>
      <div className="explore-tools">
        <SearchInput value={search} onChange={setSearch} placeholder={t("explore.search")} />
        <div className="category-tabs" role="group" aria-label={t("explore.catalogue")}>
          {["all", "tech", "creative", "productivity", "story"].map((key) => (
            <Button
              key={key}
              size="sm"
              variant={category === key ? "secondary" : "ghost"}
              aria-pressed={category === key}
              onClick={() => setCategory(key)}
            >
              {t(key === "all" ? "common.all" : `category.${key}`)}
            </Button>
          ))}
        </div>
      </div>
      <div className="section-heading">
        <h2>{t("explore.catalogue")}</h2>
        <span>{t("explore.count")}</span>
      </div>
      {filtered.length ? (
        <div className="character-grid">
          {filtered.map((c) => (
            <CharacterCard key={c.id} character={c} />
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <Compass />
          <h2>{t("common.empty")}</h2>
          <p>{t("explore.noResult")}</p>
          <Button
            variant="outline"
            onClick={() => {
              setSearch("");
              setCategory("all");
            }}
          >
            {t("common.clear")}
          </Button>
        </div>
      )}
      <p className="text-[10px] text-muted-foreground mt-7 flex items-center gap-2">
        <Sparkles size={12} />
        {t("chat.disclaimer")}
      </p>
    </div>
  );
}
export function CharacterPage({ id }: { id: string }) {
  const { t } = useTranslation();
  const character = characters.find((c) => c.id === id);
  const session = useSession();
  const online = useOnline();
  const navigate = useNavigate();
  const refresh = useRefresh();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [dialog, setDialog] = useState<"report" | "block" | null>(null);
  const [reason, setReason] = useState("");
  const blocked = useQuery({
    queryKey: ["blocked"],
    queryFn: () => getApi().blocked(),
    enabled: !!session.data,
    retry: false,
  });
  if (!character)
    return (
      <div className="page-content">
        <ErrorNotice error={new Error("not_found")} />
      </div>
    );
  const start = async () => {
    if (!session.data) {
      await navigate({ to: "/login" });
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const c = await getApi().createConversation(character.id);
      await refresh();
      await navigate({ to: "/chat/$id", params: { id: c.id } });
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  const act = async () => {
    setBusy(true);
    try {
      if (dialog === "report") {
        await getApi().report(character.id, reason);
        toast.success(t("character.reportSent"));
      } else await getApi().block(character.id);
      await refresh();
      setDialog(null);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <div className="page-content">
      <Button asChild variant="ghost" size="sm">
        <Link to="/explore">← {t("nav.explore")}</Link>
      </Button>
      <div className="character-profile">
        <img
          className="profile-image"
          src={character.image}
          alt={`${character.name} — ${t("character.ai")}`}
        />
        <div>
          <span className="eyebrow">{t("character.ai")}</span>
          <h1>{character.name}</h1>
          <div className={`tone-${character.tone}`}>{t(`character.${id}.role`)}</div>
          <p>{t(`character.${id}.desc`)}</p>
          <h2>{t("character.personality")}</h2>
          <p>{t(`character.${id}.personality`)}</p>
          <h2>{t("character.starters")}</h2>
          <p>{t(`character.${id}.starter`)}</p>
          <div className="profile-actions">
            <Button
              disabled={busy || !online || blocked.data?.includes(character.id)}
              onClick={() => void start()}
            >
              {blocked.data?.includes(character.id) ? t("explore.blocked") : t("explore.start")}
              <ArrowRight />
            </Button>
            {session.data && (
              <>
                <Button variant="outline" onClick={() => setDialog("report")}>
                  <Flag />
                  {t("character.report")}
                </Button>
                <Button
                  variant="ghost"
                  aria-label={t("character.block")}
                  title={t("character.block")}
                  onClick={() => setDialog("block")}
                >
                  <Ban />
                </Button>
              </>
            )}
          </div>
          <p className="text-xs flex items-center gap-2">
            <Gem size={15} />
            {t("explore.cost")}
          </p>
          {error ? <ErrorNotice error={error} /> : null}
          <p className="text-[10px]">{t("chat.disclaimer")}</p>
        </div>
      </div>
      <Dialog
        open={dialog !== null}
        onOpenChange={(open) => {
          if (!open) setDialog(null);
        }}
      >
        <DialogContent className="dialog-content">
          <DialogTitle>
            {t(dialog === "report" ? "character.report" : "character.block")}
          </DialogTitle>
          <DialogDescription>
            {t(dialog === "report" ? "character.reportPlaceholder" : "character.blockNote")}
          </DialogDescription>
          {dialog === "report" && (
            <div>
              <label className="text-xs block mb-2" htmlFor="reason">
                {t("character.reportReason")}
              </label>
              <textarea
                id="reason"
                className="w-full"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                maxLength={1000}
              />
            </div>
          )}
          <Button
            disabled={busy || (dialog === "report" && !reason.trim())}
            onClick={() => void act()}
          >
            {t("common.confirm")}
          </Button>
        </DialogContent>
      </Dialog>
    </div>
  );
}
