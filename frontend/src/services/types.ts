import type { Character, CharacterId } from "@/lib/characters";

export type Sku = "free" | "starter" | "plus" | "premium";
export type PaymentScenario = "success" | "pending" | "declined" | "duplicate" | "canceled";
export interface Product {
  sku: Sku;
  name: string;
  priceCents: number;
  currency: "EUR";
  gems: number;
  subscription: boolean;
}
export interface User {
  id: string;
  email: string;
  admin: boolean;
}
export interface Subscription {
  status: "free" | "active" | "past_due" | "canceled";
  renewsAt: string | null;
  cancelAtPeriodEnd: boolean;
}
export interface Wallet {
  balance: number;
  subscription: Subscription;
  inReview: boolean;
}
export interface Entry {
  id: string;
  type: "welcome" | "purchase" | "subscription" | "message" | "restitution";
  amount: number;
  reference: string;
  createdAt: string;
  status: "completed";
}
export interface Order {
  id: string;
  sku: Sku;
  status: "pending" | "paid" | "failed" | "canceled" | "expired";
  gems: number;
  priceCents: number;
  checkoutUrl: string;
  createdAt: string;
}
export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  createdAt: string;
}
export interface Conversation {
  id: string;
  characterId: CharacterId;
  messages: Message[];
  updatedAt: string;
  memoryEnabled: boolean;
  summary: string;
  affinity: number;
  lastAffinityDay: string | null;
}
export interface Report {
  id: string;
  characterId: CharacterId;
  reason: string;
  status: "pending" | "reviewed" | "dismissed";
  createdAt: string;
}
export type AiScenario = "success" | "failure" | "network";
export class ApiError extends Error {
  constructor(
    public code: string,
    public status = 0,
    public requestId?: string,
  ) {
    super(code);
    this.name = "ApiError";
  }
}
export interface ApiClient {
  me(): Promise<User | null>;
  login(email: string, password: string): Promise<User>;
  register(
    email: string,
    password: string,
    ageConfirmed: boolean,
    termsAccepted: boolean,
  ): Promise<User>;
  logout(): Promise<void>;
  products(): Promise<Product[]>;
  catalogue(): Promise<Character[]>;
  wallet(): Promise<Wallet>;
  entries(): Promise<Entry[]>;
  orders(): Promise<Order[]>;
  checkout(sku: Sku, key: string): Promise<Order>;
  order(id: string): Promise<Order>;
  simulatePayment(id: string, scenario: PaymentScenario): Promise<Order>;
  subscriptionAction(action: "renew" | "fail" | "cancel"): Promise<Wallet>;
  portal(): Promise<string>;
  conversations(): Promise<Conversation[]>;
  conversation(id: string): Promise<Conversation>;
  createConversation(characterId: CharacterId): Promise<Conversation>;
  deleteConversation(id: string): Promise<void>;
  send(
    id: string,
    content: string,
    key: string,
    signal: AbortSignal,
    onChunk: (text: string) => void,
    lang: string,
    scenario?: AiScenario,
  ): Promise<Message>;
  memory(id: string, action: "toggle" | "clear" | "reset"): Promise<Conversation>;
  report(characterId: CharacterId, reason: string): Promise<Report>;
  block(characterId: CharacterId): Promise<void>;
  blocked(): Promise<CharacterId[]>;
  reports(): Promise<Report[]>;
  moderate(id: string, status: Report["status"]): Promise<void>;
  reset(): Promise<void>;
}
