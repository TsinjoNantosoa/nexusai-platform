import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "@tanstack/react-router";
import { useTranslation } from "react-i18next";
import {
  MessageSquare,
  Plus,
  Trash2,
  ArrowUpRight,
  Send,
  Square,
  Brain,
  Gem,
  Settings2,
  RotateCcw,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Dialog, DialogContent, DialogTitle, DialogDescription } from "@/components/ui/dialog";
import {
  Gate,
  Loading,
  PageTitle,
  SearchInput,
  ErrorNotice,
  ConfirmDialog,
  formatDate,
} from "@/components/shared";
import { characters } from "@/lib/characters";
import { getApi, isMock } from "@/services/api";
import { ApiError, type Conversation, type AiScenario } from "@/services/types";
import { useWallet, useOnline, useRefresh } from "@/services/hooks";
function ConversationList() {
  const { t, i18n } = useTranslation();
  const query = useQuery({ queryKey: ["conversations"], queryFn: () => getApi().conversations() });
  const [search, setSearch] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const refresh = useRefresh();
  const remove = async () => {
    if (!deleting) return;
    setBusy(true);
    try {
      await getApi().deleteConversation(deleting);
      await refresh();
      setDeleting(null);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  if (query.isPending) return <Loading />;
  if (query.error) return <ErrorNotice error={query.error} retry={() => void query.refetch()} />;
  const rows = query.data.filter((c) => {
    const char = characters.find((x) => x.id === c.characterId);
    return `${char?.name} ${c.messages.at(-1)?.content ?? ""}`
      .toLowerCase()
      .includes(search.toLowerCase());
  });
  return (
    <>
      <PageTitle title={t("conversations.title")} subtitle={t("conversations.subtitle")}>
        <Button asChild>
          <Link to="/explore">
            <Plus />
            {t("conversations.new")}
          </Link>
        </Button>
      </PageTitle>
      <SearchInput value={search} onChange={setSearch} placeholder={t("conversations.search")} />
      {rows.length ? (
        <div className="mt-6">
          {rows.map((c) => {
            const char = characters.find((x) => x.id === c.characterId);
            return (
              <article className="conversation-row" key={c.id}>
                <img src={char?.image} alt={char?.name} />
                <Link to="/chat/$id" params={{ id: c.id }} className="conversation-info">
                  <h3>
                    {char?.name}{" "}
                    <span className="text-muted-foreground text-[10px] ml-2">
                      {t(`character.${c.characterId}.role`)}
                    </span>
                  </h3>
                  <p>{c.messages.at(-1)?.content ?? t("conversations.untitled")}</p>
                </Link>
                <time dateTime={c.updatedAt}>{formatDate(c.updatedAt, i18n.language)}</time>
                <Button
                  variant="ghost"
                  size="icon"
                  aria-label={`${t("common.delete")} ${char?.name}`}
                  title={t("common.delete")}
                  onClick={() => setDeleting(c.id)}
                >
                  <Trash2 />
                </Button>
                <Button
                  asChild
                  variant="ghost"
                  size="icon"
                  aria-label={`${t("common.continue")} ${char?.name}`}
                >
                  <Link to="/chat/$id" params={{ id: c.id }}>
                    <ArrowUpRight />
                  </Link>
                </Button>
              </article>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          <MessageSquare />
          <h2>{t(search ? "common.empty" : "conversations.empty")}</h2>
          <p>{t("conversations.emptySub")}</p>
          <Button asChild>
            <Link to="/explore">{t("nav.explore")}</Link>
          </Button>
        </div>
      )}
      {error ? <ErrorNotice error={error} /> : null}
      <ConfirmDialog
        open={!!deleting}
        onOpenChange={(o) => {
          if (!o) setDeleting(null);
        }}
        title={t("conversations.deleteTitle")}
        description={t("conversations.deleteDesc")}
        onConfirm={() => void remove()}
        destructive
        busy={busy}
      />
    </>
  );
}
export function ConversationsPage() {
  return (
    <div className="page-content">
      <Gate>
        <ConversationList />
      </Gate>
    </div>
  );
}
function MemoryPanel({ conversation }: { conversation: Conversation }) {
  const { t } = useTranslation();
  const refresh = useRefresh();
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const action = async (kind: "toggle" | "clear" | "reset") => {
    setBusy(true);
    setError(null);
    try {
      await getApi().memory(conversation.id, kind);
      await refresh();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <section>
        <h2 className="flex items-center gap-2">
          <Brain size={16} />
          {t("chat.memory")}
        </h2>
        <div className="memory-switch">
          <label htmlFor="memory-toggle">{t("chat.memoryEnabled")}</label>
          <Switch
            id="memory-toggle"
            checked={conversation.memoryEnabled}
            disabled={busy}
            onCheckedChange={() => void action("toggle")}
          />
        </div>
        <p className="break-words">{conversation.summary || t("chat.memoryEmpty")}</p>
        <Button
          variant="outline"
          size="sm"
          disabled={busy || !conversation.summary}
          onClick={() => void action("clear")}
        >
          <Trash2 />
          {t("common.clear")}
        </Button>
      </section>
      <section>
        <h2>
          {t("character.affinity")} <span className="text-violet">{conversation.affinity}/100</span>
        </h2>
        <div className="affinity-bar">
          <progress value={conversation.affinity} max={100} aria-label={t("character.affinity")} />
        </div>
        <p>{t("character.affinityNote")}</p>
        <Button variant="ghost" size="sm" disabled={busy} onClick={() => void action("reset")}>
          <RotateCcw />
          {t("chat.resetAffinity")}
        </Button>
      </section>
      {error ? <ErrorNotice error={error} /> : null}
    </>
  );
}
function ChatContent({ id }: { id: string }) {
  const { t, i18n } = useTranslation();
  const query = useQuery({
    queryKey: ["conversation", id],
    queryFn: () => getApi().conversation(id),
  });
  const wallet = useWallet();
  const online = useOnline();
  const refresh = useRefresh();
  const [input, setInput] = useState("");
  const [stream, setStream] = useState("");
  const [pendingContent, setPendingContent] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [refunded, setRefunded] = useState(false);
  const [scenario, setScenario] = useState<AiScenario>("success");
  const [memoryOpen, setMemoryOpen] = useState(false);
  const controller = useRef<AbortController | null>(null);
  const bottom = useRef<HTMLDivElement | null>(null);
  useEffect(
    () => () => {
      controller.current?.abort();
    },
    [],
  );
  useEffect(() => {
    bottom.current?.scrollIntoView({ block: "end", behavior: "auto" });
  }, [stream, query.data?.messages.length]);
  const send = async () => {
    if (!input.trim() || busy || !online || input.length > 2000) return;
    const text = input;
    setInput("");
    setPendingContent(text);
    setBusy(true);
    setError(null);
    setRefunded(false);
    controller.current = new AbortController();
    try {
      await getApi().send(
        id,
        text,
        crypto.randomUUID(),
        controller.current.signal,
        setStream,
        i18n.language,
        scenario,
      );
    } catch (e) {
      setBusy(false);
      setStream("");
      setPendingContent("");
      setError(e);
      setRefunded(
        isMock &&
          e instanceof ApiError &&
          ["ai_failure", "network", "generation_canceled"].includes(e.code),
      );
    } finally {
      await refresh();
      setBusy(false);
      setStream("");
      setPendingContent("");
      controller.current = null;
    }
  };
  if (query.isPending || wallet.isPending) return <Loading />;
  if (query.error || wallet.error)
    return (
      <div className="page-content">
        <ErrorNotice
          error={query.error ?? wallet.error}
          retry={() => {
            void query.refetch();
            void wallet.refetch();
          }}
        />
      </div>
    );
  const c = query.data;
  const character = characters.find((char) => char.id === c.characterId);
  if (!character) return null;
  const balance = wallet.data.balance;
  return (
    <div className="chat-layout" data-operation-active={busy}>
      <div className="chat-main">
        <header className="chat-heading">
          <Link to="/characters/$id" params={{ id: c.characterId }}>
            <img src={character.image} alt={character.name} />
          </Link>
          <div>
            <h1>{character.name}</h1>
            <p>
              {t(`character.${c.characterId}.role`)} · {t("character.ai")}
            </p>
          </div>
          <div className="chat-tools">
            <Button
              variant="ghost"
              size="icon"
              className="chat-mobile-memory"
              title={t("chat.memory")}
              aria-label={t("chat.memory")}
              onClick={() => setMemoryOpen(true)}
            >
              <Settings2 />
            </Button>
          </div>
        </header>
        <div className="messages" aria-live="polite" aria-relevant="additions text">
          {!c.messages.length && !busy && (
            <div className="empty-state">
              <img
                src={character.image}
                className="w-20 h-20 rounded-full object-cover object-top mx-auto"
                alt={character.name}
              />
              <h2>{character.name}</h2>
              <p>{t(`character.${c.characterId}.desc`)}</p>
              <Button
                variant="outline"
                onClick={() => setInput(t(`character.${c.characterId}.starter`))}
              >
                {t("character.starters")}
                <ArrowUpRight />
              </Button>
            </div>
          )}
          {c.messages.map((m) => (
            <div className={`message ${m.role}`} key={m.id}>
              {m.role === "assistant" ? (
                <img src={character.image} alt={character.name} />
              ) : (
                <div className="user-avatar">
                  <MessageSquare size={14} />
                </div>
              )}
              <div>
                <div className="message-label">
                  {m.role === "assistant" ? character.name : t("demo.account")}
                </div>
                <div className="message-text">{m.content}</div>
              </div>
            </div>
          ))}
          {busy && (
            <>
              {!c.messages.some((m) => m.role === "user" && m.content === pendingContent) && (
                <div className="message user">
                  <div className="message-text">{pendingContent}</div>
                </div>
              )}
              <div className="message assistant">
                <img src={character.image} alt={character.name} />
                <div className="message-text">
                  {stream || t("chat.thinking")}
                  <span className="text-violet animate-pulse ml-1">▍</span>
                </div>
              </div>
            </>
          )}
          {refunded && (
            <div className="notice success" role="status">
              {t("chat.refund")}
            </div>
          )}
          {error && !refunded ? <ErrorNotice error={error} /> : null}
          {!!error && !isMock && <div className="notice warning">{t("chat.apiRefund")}</div>}
          <div ref={bottom} />
        </div>
        <div className="composer-area">
          {balance < 2 && (
            <div className="notice warning mb-3">
              {t("chat.insufficient")}{" "}
              <Link to="/pricing" className="text-violet">
                {t("wallet.buy")}
              </Link>
            </div>
          )}
          <form
            onSubmit={(e) => {
              e.preventDefault();
              void send();
            }}
          >
            <div className="composer">
              <textarea
                aria-label={t("chat.placeholder")}
                placeholder={t("chat.placeholder")}
                value={input}
                maxLength={2000}
                rows={2}
                disabled={busy || !online}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
                    e.preventDefault();
                    void send();
                  }
                }}
              />
              {busy ? (
                <Button
                  type="button"
                  size="icon"
                  variant="destructive"
                  title={t("chat.stop")}
                  aria-label={t("chat.stop")}
                  onClick={() => controller.current?.abort()}
                >
                  <Square />
                </Button>
              ) : (
                <Button
                  type="submit"
                  size="icon"
                  title={t("chat.send")}
                  aria-label={t("chat.send")}
                  disabled={!input.trim() || !online || balance < 2 || wallet.data.inReview}
                >
                  <Send />
                </Button>
              )}
            </div>
          </form>
          <div className="composer-footer">
            <span>{t("chat.disclaimer")}</span>
            <span>
              {input.length}/2000 · {t("explore.cost")}
            </span>
          </div>
        </div>
      </div>
      <aside className="chat-side">
        <section>
          <h2>{t("chat.balance")}</h2>
          <div className="text-2xl font-display text-violet flex items-center gap-2">
            <Gem size={22} />
            {balance}
          </div>
          <p>{t("explore.cost")}</p>
        </section>
        <MemoryPanel conversation={c} />
        {isMock && (
          <section>
            <label className="text-[10px] block mb-3" htmlFor="ai-scenario">
              {t("demo.scenario")}
            </label>
            <select
              id="ai-scenario"
              className="w-full text-xs"
              value={scenario}
              disabled={busy}
              onChange={(e) => {
                const v = e.target.value;
                if (v === "success" || v === "failure" || v === "network") setScenario(v);
              }}
            >
              {["success", "failure", "network"].map((s) => (
                <option key={s} value={s}>
                  {t(`chat.${s}`)}
                </option>
              ))}
            </select>
          </section>
        )}
      </aside>
      <Dialog open={memoryOpen} onOpenChange={setMemoryOpen}>
        <DialogContent className="dialog-content">
          <DialogTitle>{t("chat.memory")}</DialogTitle>
          <DialogDescription>{t("character.affinityNote")}</DialogDescription>
          <MemoryPanel conversation={c} />
          {isMock && (
            <select
              aria-label={t("demo.scenario")}
              value={scenario}
              disabled={busy}
              onChange={(e) => {
                const v = e.target.value;
                if (v === "success" || v === "failure" || v === "network") setScenario(v);
              }}
            >
              {["success", "failure", "network"].map((s) => (
                <option key={s} value={s}>
                  {t(`chat.${s}`)}
                </option>
              ))}
            </select>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
export function ChatPage({ id }: { id: string }) {
  return (
    <Gate>
      <ChatContent id={id} />
    </Gate>
  );
}
