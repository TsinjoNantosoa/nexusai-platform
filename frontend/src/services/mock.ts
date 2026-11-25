import fr from "@/i18n/fr.json";
import en from "@/i18n/en.json";
import { characters, type CharacterId } from "@/lib/characters";
import {
  ApiError,
  type ApiClient,
  type User,
  type Wallet,
  type Entry,
  type Order,
  type Product,
  type Sku,
  type PaymentScenario,
  type Conversation,
  type Message,
  type AiScenario,
  type Report,
} from "./types";

export const PRODUCTS: Product[] = [
  { sku: "free", name: "Free", priceCents: 0, currency: "EUR", gems: 20, subscription: false },
  {
    sku: "starter",
    name: "Starter",
    priceCents: 299,
    currency: "EUR",
    gems: 100,
    subscription: false,
  },
  { sku: "plus", name: "Plus", priceCents: 999, currency: "EUR", gems: 500, subscription: false },
  {
    sku: "premium",
    name: "Premium",
    priceCents: 1999,
    currency: "EUR",
    gems: 1500,
    subscription: true,
  },
];
const date = () => new Date().toISOString();
const delay = (ms = 140) => new Promise<void>((resolve) => setTimeout(resolve, ms));
interface Account {
  user: User;
  wallet: Wallet;
  entries: Entry[];
  orders: Order[];
  chats: Conversation[];
  blocked: CharacterId[];
}
export class MockApiClient implements ApiClient {
  private accounts = new Map<string, Account>();
  private current: Account | null = null;
  private serial = 0;
  private active = false;
  private attempts = new Map<
    string,
    { state: "active" | "complete" | "failed"; message?: Message }
  >();
  private checkoutKeys = new Map<string, string>();
  private reportRows: Report[] = [];
  private renewals = 0;
  private affinity = new Map<string, { score: number; day: string | null }>();
  private id(prefix: string) {
    return `${prefix}_${++this.serial}`;
  }
  private require() {
    if (!this.current) throw new ApiError("auth_required", 401);
    return this.current;
  }
  private writable() {
    const a = this.require();
    if (a.wallet.inReview) throw new ApiError("account_review", 403);
    return a;
  }
  private entry(a: Account, type: Entry["type"], amount: number, reference: string) {
    if (a.entries.some((e) => e.reference === reference)) return;
    if (a.wallet.balance + amount < 0) throw new ApiError("insufficient_balance", 409);
    a.entries.unshift({
      id: this.id("tx"),
      type,
      amount,
      reference,
      createdAt: date(),
      status: "completed",
    });
    a.wallet.balance += amount;
  }
  private newAccount(email: string): Account {
    const id = this.id("user");
    const a: Account = {
      user: { id, email, admin: email === "admin@nexusai.app" },
      wallet: {
        balance: 0,
        subscription: { status: "free", renewsAt: null, cancelAtPeriodEnd: false },
        inReview: false,
      },
      entries: [],
      orders: [],
      chats: [],
      blocked: [],
    };
    this.entry(a, "welcome", 20, `WELCOME-${id}`);
    this.accounts.set(email, a);
    return a;
  }
  async me() {
    await delay();
    return this.current ? { ...this.current.user } : null;
  }
  async login(email: string, password: string) {
    await delay();
    email = email.toLowerCase().trim();
    if (
      password.length < 8 ||
      (!["demo@nexusai.app", "admin@nexusai.app"].includes(email) && !this.accounts.has(email))
    )
      throw new ApiError("invalid_credentials", 401);
    this.current = this.accounts.get(email) ?? this.newAccount(email);
    return { ...this.current.user };
  }
  async register(email: string, password: string, age: boolean, terms: boolean) {
    await delay();
    email = email.toLowerCase().trim();
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || password.length < 8 || !age || !terms)
      throw new ApiError("validation", 422);
    if (this.accounts.has(email) || ["demo@nexusai.app", "admin@nexusai.app"].includes(email))
      throw new ApiError("email_taken", 409);
    this.current = this.newAccount(email);
    return { ...this.current.user };
  }
  async logout() {
    this.current = null;
    this.accounts.clear();
    this.attempts.clear();
    this.checkoutKeys.clear();
    this.reportRows = [];
    this.active = false;
    this.affinity.clear();
  }
  async products() {
    return PRODUCTS.map((p) => ({ ...p }));
  }
  async catalogue() {
    return characters;
  }
  async wallet() {
    await delay();
    const w = this.require().wallet;
    return { ...w, subscription: { ...w.subscription } };
  }
  async entries() {
    return this.require().entries.map((e) => ({ ...e }));
  }
  async orders() {
    return this.require().orders.map((o) => ({ ...o }));
  }
  async checkout(sku: Sku, key: string) {
    const a = this.writable();
    if (!key) throw new ApiError("validation", 422);
    const compound = `${a.user.id}:${key}`;
    const previous = this.checkoutKeys.get(compound);
    if (previous) return this.order(previous);
    const p = PRODUCTS.find((p) => p.sku === sku);
    if (!p || sku === "free") throw new ApiError("validation", 422);
    const id = this.id("order");
    const o: Order = {
      id,
      sku,
      status: "pending",
      gems: p.gems,
      priceCents: p.priceCents,
      checkoutUrl: `/billing/success?order=${id}`,
      createdAt: date(),
    };
    a.orders.unshift(o);
    this.checkoutKeys.set(compound, id);
    await delay(250);
    return { ...o };
  }
  async order(id: string) {
    const o = this.require().orders.find((o) => o.id === id);
    if (!o) throw new ApiError("not_found", 404);
    return { ...o };
  }
  async simulatePayment(id: string, scenario: PaymentScenario) {
    const a = this.writable();
    const o = a.orders.find((o) => o.id === id);
    if (!o) throw new ApiError("not_found", 404);
    if (o.status === "paid") return { ...o };
    if (o.status !== "pending") throw new ApiError("already_processed", 409);
    if (scenario === "pending") return { ...o };
    if (scenario === "canceled") {
      o.status = "canceled";
      return { ...o };
    }
    if (scenario === "declined") {
      o.status = "failed";
      return { ...o };
    }
    o.status = "paid";
    this.entry(a, o.sku === "premium" ? "subscription" : "purchase", o.gems, `PAID-${o.id}`);
    if (o.sku === "premium")
      a.wallet.subscription = {
        status: "active",
        renewsAt: new Date(Date.now() + 30 * 86400000).toISOString(),
        cancelAtPeriodEnd: false,
      };
    return { ...o };
  }
  async subscriptionAction(action: "renew" | "fail" | "cancel") {
    const a = this.require();
    if (a.wallet.subscription.status === "free") throw new ApiError("no_subscription", 409);
    if (action === "cancel") a.wallet.subscription.cancelAtPeriodEnd = true;
    if (action === "fail") a.wallet.subscription.status = "past_due";
    if (action === "renew") {
      if (a.wallet.subscription.cancelAtPeriodEnd) throw new ApiError("already_processed", 409);
      this.entry(a, "subscription", 1500, `INVOICE-${a.user.id}-${++this.renewals}`);
      a.wallet.subscription.status = "active";
      a.wallet.subscription.renewsAt = new Date(Date.now() + 30 * 86400000).toISOString();
    }
    return this.wallet();
  }
  async portal(): Promise<string> {
    throw new ApiError("integration_pending", 501);
  }
  async conversations() {
    return this.require().chats.map((c) => ({ ...c, messages: c.messages.map((m) => ({ ...m })) }));
  }
  private chat(id: string) {
    const c = this.require().chats.find((c) => c.id === id);
    if (!c) throw new ApiError("not_found", 404);
    return c;
  }
  async conversation(id: string) {
    const c = this.chat(id);
    return { ...c, messages: c.messages.map((m) => ({ ...m })) };
  }
  async createConversation(characterId: CharacterId) {
    const a = this.require();
    if (a.blocked.includes(characterId)) throw new ApiError("character_blocked", 403);
    if (!characters.some((c) => c.id === characterId)) throw new ApiError("not_found", 404);
    const c: Conversation = {
      id: this.id("chat"),
      characterId,
      messages: [],
      updatedAt: date(),
      memoryEnabled: true,
      summary: "",
      affinity: this.affinity.get(`${a.user.id}:${characterId}`)?.score ?? 0,
      lastAffinityDay: this.affinity.get(`${a.user.id}:${characterId}`)?.day ?? null,
    };
    a.chats.unshift(c);
    return { ...c };
  }
  async deleteConversation(id: string) {
    const a = this.require();
    this.chat(id);
    if (this.active) throw new ApiError("generation_active", 409);
    a.chats = a.chats.filter((c) => c.id !== id);
  }
  async send(
    id: string,
    content: string,
    key: string,
    signal: AbortSignal,
    onChunk: (t: string) => void,
    lang: string,
    scenario: AiScenario = "success",
  ) {
    const a = this.writable();
    const c = this.chat(id);
    const request = `${a.user.id}:${key}`;
    const old = this.attempts.get(request);
    if (old?.state === "complete" && old.message) {
      onChunk(old.message.content);
      return old.message;
    }
    if (old) throw new ApiError("already_processed", 409);
    if (this.active) throw new ApiError("generation_active", 409);
    if (a.blocked.includes(c.characterId)) throw new ApiError("character_blocked", 403);
    if (!content.trim() || content.length > 2000 || !key) throw new ApiError("validation", 422);
    if (/\b(porn|explicit sexual|contenu sexuel explicite)\b/i.test(content))
      throw new ApiError("content_blocked", 422);
    this.entry(a, "message", -2, `RESERVE-${request}`);
    this.active = true;
    this.attempts.set(request, { state: "active" });
    c.messages.push({
      id: this.id("msg"),
      role: "user",
      content: content.trim(),
      createdAt: date(),
    });
    const responses = lang === "fr" ? fr : en;
    const response = responses[`mock.response.${c.characterId}`];
    try {
      let text = "";
      const words = response.split(" ");
      for (let i = 0; i < words.length; i++) {
        await delay(24);
        if (signal.aborted) throw new ApiError("generation_canceled", 499);
        if (scenario !== "success" && i === 8)
          throw new ApiError(scenario === "failure" ? "ai_failure" : "network", 503);
        text += (i ? " " : "") + words[i];
        onChunk(text);
      }
      const message: Message = {
        id: this.id("msg"),
        role: "assistant",
        content: response,
        createdAt: date(),
      };
      c.messages.push(message);
      c.updatedAt = date();
      if (c.memoryEnabled) c.summary = content.slice(0, 180);
      const today = date().slice(0, 10);
      const affinityKey = `${a.user.id}:${c.characterId}`;
      const affinity = this.affinity.get(affinityKey) ?? { score: 0, day: null };
      if (affinity.day !== today) {
        affinity.score = Math.min(100, affinity.score + 1);
        affinity.day = today;
        this.affinity.set(affinityKey, affinity);
      }
      for (const chat of a.chats.filter((chat) => chat.characterId === c.characterId)) {
        chat.affinity = affinity.score;
        chat.lastAffinityDay = affinity.day;
      }
      this.attempts.set(request, { state: "complete", message });
      return message;
    } catch (e) {
      this.entry(a, "restitution", 2, `REFUND-${request}`);
      this.attempts.set(request, { state: "failed" });
      throw e;
    } finally {
      this.active = false;
    }
  }
  async memory(id: string, action: "toggle" | "clear" | "reset") {
    const c = this.chat(id);
    if (action === "toggle") c.memoryEnabled = !c.memoryEnabled;
    if (action === "clear") c.summary = "";
    if (action === "reset") {
      const a = this.require();
      this.affinity.set(`${a.user.id}:${c.characterId}`, { score: 0, day: null });
      for (const chat of a.chats.filter((chat) => chat.characterId === c.characterId)) {
        chat.affinity = 0;
        chat.lastAffinityDay = null;
      }
    }
    return this.conversation(id);
  }
  async report(characterId: CharacterId, reason: string) {
    this.require();
    if (!reason.trim()) throw new ApiError("validation", 422);
    const r: Report = {
      id: this.id("report"),
      characterId,
      reason,
      status: "pending",
      createdAt: date(),
    };
    this.reportRows.unshift(r);
    return { ...r };
  }
  async block(characterId: CharacterId) {
    const a = this.require();
    if (!a.blocked.includes(characterId)) a.blocked.push(characterId);
  }
  async blocked() {
    return [...this.require().blocked];
  }
  async reports() {
    if (!this.require().user.admin) throw new ApiError("forbidden", 403);
    return this.reportRows.map((r) => ({ ...r }));
  }
  async moderate(id: string, status: Report["status"]) {
    if (!this.require().user.admin) throw new ApiError("forbidden", 403);
    const r = this.reportRows.find((r) => r.id === id);
    if (!r) throw new ApiError("not_found", 404);
    r.status = status;
  }
  async reset() {
    await this.logout();
    this.serial = 0;
    this.renewals = 0;
  }
}
