import { characters, type CharacterId } from "@/lib/characters";
import {
  ApiError,
  type ApiClient,
  type User,
  type Product,
  type Wallet,
  type Entry,
  type Order,
  type Sku,
  type Conversation,
  type Message,
  type Report,
} from "./types";

export class HttpApiClient implements ApiClient {
  constructor(private base: string) {}
  private csrf: string | null = null;
  setCsrfToken(token: string | null) {
    this.csrf = token;
  }
  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Content-Type", "application/json");
    if (this.csrf && init.method && init.method !== "GET") headers.set("X-CSRF-Token", this.csrf);
    let response: Response;
    try {
      response = await fetch(this.base + path, { ...init, headers, credentials: "include" });
    } catch {
      throw new ApiError("network", 0);
    }
    if (response.status === 204) return undefined as T;
    const body = await response.json().catch(() => null);
    if (!response.ok)
      throw new ApiError(
        body?.code ?? `http_${response.status}`,
        response.status,
        body?.request_id,
      );
    return body as T;
  }
  async me() {
    try {
      return await this.request<User>("/users/me");
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) return null;
      throw e;
    }
  }
  login(email: string, password: string) {
    return this.request<User>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
  }
  register(email: string, password: string, ageConfirmed: boolean, termsAccepted: boolean) {
    return this.request<User>("/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        age_confirmed: ageConfirmed,
        terms_accepted: termsAccepted,
      }),
    });
  }
  async logout() {
    await this.request<void>("/auth/logout", { method: "POST" });
    this.csrf = null;
  }
  products() {
    return this.request<Product[]>("/billing/products");
  }
  async catalogue() {
    const rows =
      await this.request<
        Array<{ id: CharacterId; name: string; category: string; image?: string }>
      >("/characters");
    return rows.map((row) => {
      const art = characters.find((c) => c.id === row.id);
      return {
        id: row.id,
        name: row.name,
        category: row.category,
        image: row.image ?? art?.image ?? "",
        tone: art?.tone ?? "electric",
      };
    });
  }
  async wallet() {
    const wallet = await this.request<Wallet>("/wallet");
    wallet.subscription = await this.request<Wallet["subscription"]>("/billing/subscription");
    return wallet;
  }
  entries() {
    return this.request<Entry[]>("/wallet/transactions");
  }
  orders(): Promise<Order[]> {
    return this.pending();
  }
  async checkout(sku: Sku, key: string) {
    const result = await this.request<{ checkout_url: string; order_id: string }>(
      "/billing/checkout",
      {
        method: "POST",
        headers: { "Idempotency-Key": key },
        body: JSON.stringify({ sku }),
      },
    );
    const order = await this.order(result.order_id);
    return { ...order, checkoutUrl: result.checkout_url };
  }
  order(id: string) {
    return this.request<Order>(`/billing/orders/${encodeURIComponent(id)}`);
  }
  async portal() {
    const r = await this.request<{ portal_url: string }>("/billing/portal", { method: "POST" });
    return r.portal_url;
  }
  private pending<T>(): Promise<T> {
    return Promise.reject(new ApiError("integration_pending", 501));
  }
  simulatePayment(): Promise<Order> {
    return this.pending();
  }
  subscriptionAction(): Promise<Wallet> {
    return this.pending();
  }
  conversations() {
    return this.request<Conversation[]>("/conversations");
  }
  async conversation(id: string) {
    const c = await this.request<Conversation>(`/conversations/${encodeURIComponent(id)}`);
    c.messages = await this.request<Message[]>(`/conversations/${encodeURIComponent(id)}/messages`);
    return c;
  }
  createConversation(characterId: CharacterId) {
    return this.request<Conversation>("/conversations", {
      method: "POST",
      body: JSON.stringify({ character_id: characterId }),
    });
  }
  deleteConversation(id: string) {
    return this.request<void>(`/conversations/${encodeURIComponent(id)}`, { method: "DELETE" });
  }
  async send(
    id: string,
    content: string,
    key: string,
    signal: AbortSignal,
    onChunk: (text: string) => void,
  ): Promise<Message> {
    const headers = new Headers({
      "Content-Type": "application/json",
      Accept: "text/event-stream",
      "Idempotency-Key": key,
    });
    if (this.csrf) headers.set("X-CSRF-Token", this.csrf);
    let res: Response;
    try {
      res = await fetch(`${this.base}/conversations/${encodeURIComponent(id)}/messages`, {
        method: "POST",
        credentials: "include",
        headers,
        signal,
        body: JSON.stringify({ content }),
      });
    } catch {
      throw new ApiError("network", 0);
    }
    if (!res.ok) {
      const error = await res.json().catch(() => null);
      throw new ApiError(error?.code ?? `http_${res.status}`, res.status, error?.request_id);
    }
    if (!res.body) throw new ApiError("network", 0);
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let text = "";
    let final: Message | null = null;
    try {
      while (true) {
        const { done, value } = await reader.read();
        buffer += decoder.decode(value, { stream: !done }).replace(/\r\n/g, "\n");
        let split: number;
        while ((split = buffer.indexOf("\n\n")) >= 0) {
          const block = buffer.slice(0, split);
          buffer = buffer.slice(split + 2);
          const data = block
            .split("\n")
            .filter((l) => l.startsWith("data:"))
            .map((l) => l.slice(5).trimStart())
            .join("\n");
          if (!data) continue;
          const event = block
            .split("\n")
            .find((l) => l.startsWith("event:"))
            ?.slice(6)
            .trim();
          let payload: { delta?: string; message?: Message; code?: string; request_id?: string };
          try {
            payload = JSON.parse(data);
          } catch {
            throw new ApiError("stream_invalid", 503);
          }
          if (event === "error")
            throw new ApiError(payload.code ?? "ai_failure", 503, payload.request_id);
          if (payload.delta) {
            text += payload.delta;
            onChunk(text);
          }
          if (event === "done" && payload.message) final = payload.message;
        }
        if (done) break;
      }
    } finally {
      reader.releaseLock();
    }
    if (!final) throw new ApiError("stream_incomplete", 503);
    return final;
  }
  memory(): Promise<Conversation> {
    return this.pending();
  }
  report(characterId: CharacterId, reason: string) {
    return this.request<Report>("/reports", {
      method: "POST",
      body: JSON.stringify({ character_id: characterId, reason }),
    });
  }
  block(): Promise<void> {
    return this.pending();
  }
  blocked(): Promise<CharacterId[]> {
    return this.pending();
  }
  reports() {
    return this.request<Report[]>("/admin/reports");
  }
  moderate(): Promise<void> {
    return this.pending();
  }
  reset(): Promise<void> {
    return this.pending();
  }
}
