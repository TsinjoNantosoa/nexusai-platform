import { beforeEach, describe, expect, it } from "vitest";
import { MockApiClient } from "./mock";
import { ApiError } from "./types";
import { registrationSchema, authSchema } from "@/features/Auth";
import { isPreviewHost, shouldRegisterOfflineSupport } from "@/lib/offline";
let api: MockApiClient;
beforeEach(async () => {
  api = new MockApiClient();
  await api.login("demo@nexusai.app", "demo1234");
});
describe("F01 and initial offers", () => {
  it("starts a demo account with exactly 20 gems once", async () => {
    expect((await api.wallet()).balance).toBe(20);
    await api.login("demo@nexusai.app", "demo1234");
    expect((await api.wallet()).balance).toBe(20);
    expect((await api.entries()).filter((e) => e.type === "welcome")).toHaveLength(1);
  });
  it("grants a registered account 20 welcome gems", async () => {
    await api.register("fictional@example.test", "password123", true, true);
    expect((await api.wallet()).balance).toBe(20);
  });
  it("rejects duplicate email registration", async () => {
    await expect(api.register("demo@nexusai.app", "password123", true, true)).rejects.toMatchObject(
      { code: "email_taken" },
    );
  });
  it("provides a separate administrator demonstration", async () => {
    expect((await api.login("admin@nexusai.app", "demo1234")).admin).toBe(true);
  });
  it("requires valid email and eight-character password", () => {
    expect(
      authSchema.safeParse({
        email: "invalid",
        password: "1234567",
        confirmPassword: "",
        ageConfirmed: false,
        termsAccepted: false,
      }).success,
    ).toBe(false);
  });
  it("requires matching passwords", () => {
    expect(
      registrationSchema.safeParse({
        email: "a@example.test",
        password: "password123",
        confirmPassword: "different",
        ageConfirmed: true,
        termsAccepted: true,
      }).success,
    ).toBe(false);
  });
  it("requires age declaration", () => {
    expect(
      registrationSchema.safeParse({
        email: "a@example.test",
        password: "password123",
        confirmPassword: "password123",
        ageConfirmed: false,
        termsAccepted: true,
      }).success,
    ).toBe(false);
  });
  it("requires demonstration terms acceptance", () => {
    expect(
      registrationSchema.safeParse({
        email: "a@example.test",
        password: "password123",
        confirmPassword: "password123",
        ageConfirmed: true,
        termsAccepted: false,
      }).success,
    ).toBe(false);
  });
  it("uses exact Starter offer: EUR 299 cents, 100 gems, one-time", async () => {
    expect((await api.products()).find((p) => p.sku === "starter")).toMatchObject({
      priceCents: 299,
      gems: 100,
      currency: "EUR",
      subscription: false,
    });
  });
  it("uses exact Plus offer: EUR 999 cents, 500 gems, one-time", async () => {
    expect((await api.products()).find((p) => p.sku === "plus")).toMatchObject({
      priceCents: 999,
      gems: 500,
      subscription: false,
    });
  });
  it("uses exact Premium offer: EUR 1999 cents, 1500 gems per month", async () => {
    expect((await api.products()).find((p) => p.sku === "premium")).toMatchObject({
      priceCents: 1999,
      gems: 1500,
      subscription: true,
    });
  });
});
describe("FE-01 simulated financial rules — not Stripe integration", () => {
  it("creates and observes a pending order without crediting on reads", async () => {
    const o = await api.checkout("starter", "key");
    await api.order(o.id);
    await api.order(o.id);
    expect((await api.wallet()).balance).toBe(20);
    expect(o.status).toBe("pending");
  });
  it("credits Starter exactly 100 only on explicit simulated confirmation", async () => {
    const o = await api.checkout("starter", "key");
    await api.simulatePayment(o.id, "success");
    expect((await api.wallet()).balance).toBe(120);
  });
  it("does not double credit a duplicate confirmation", async () => {
    const o = await api.checkout("plus", "key");
    await api.simulatePayment(o.id, "success");
    await api.simulatePayment(o.id, "duplicate");
    expect((await api.wallet()).balance).toBe(520);
    expect((await api.entries()).filter((e) => e.type === "purchase")).toHaveLength(1);
  });
  it("does not credit declined orders", async () => {
    const o = await api.checkout("starter", "key");
    expect((await api.simulatePayment(o.id, "declined")).status).toBe("failed");
    expect((await api.wallet()).balance).toBe(20);
  });
  it("keeps delayed confirmation pending without credit", async () => {
    const o = await api.checkout("starter", "key");
    await api.simulatePayment(o.id, "pending");
    expect((await api.wallet()).balance).toBe(20);
  });
  it("reuses an order for the same checkout idempotency key", async () => {
    const a = await api.checkout("starter", "same");
    const b = await api.checkout("starter", "same");
    expect(b.id).toBe(a.id);
    expect(await api.orders()).toHaveLength(1);
  });
  it("credits Premium 1500 for activation and each paid renewal", async () => {
    const o = await api.checkout("premium", "key");
    await api.simulatePayment(o.id, "success");
    expect((await api.wallet()).balance).toBe(1520);
    await api.subscriptionAction("renew");
    expect((await api.wallet()).balance).toBe(3020);
  });
  it("does not credit an unsuccessful renewal", async () => {
    const o = await api.checkout("premium", "key");
    await api.simulatePayment(o.id, "success");
    await api.subscriptionAction("fail");
    expect((await api.wallet()).balance).toBe(1520);
    expect((await api.wallet()).subscription.status).toBe("past_due");
  });
  it("keeps acquired gems on cancellation and stops future renewal grants", async () => {
    const o = await api.checkout("premium", "key");
    await api.simulatePayment(o.id, "success");
    await api.subscriptionAction("cancel");
    expect((await api.wallet()).balance).toBe(1520);
    expect((await api.wallet()).subscription.cancelAtPeriodEnd).toBe(true);
    await expect(api.subscriptionAction("renew")).rejects.toMatchObject({
      code: "already_processed",
    });
  });
  it("makes balance exactly equal to signed completed ledger entries", async () => {
    const o = await api.checkout("starter", "key");
    await api.simulatePayment(o.id, "success");
    expect((await api.entries()).reduce((sum, e) => sum + e.amount, 0)).toBe(
      (await api.wallet()).balance,
    );
  });
  it("clears all private mock account state on logout", async () => {
    await api.createConversation("luna");
    await api.logout();
    expect(await api.me()).toBeNull();
    await expect(api.conversations()).rejects.toBeInstanceOf(ApiError);
    await api.login("demo@nexusai.app", "demo1234");
    expect(await api.conversations()).toHaveLength(0);
  });
});
describe("W02 registration boundaries", () => {
  it("refuses main and numbered preview hostnames", () => {
    expect(isPreviewHost("id-preview--abc.lovable.app")).toBe(true);
    expect(isPreviewHost("preview-2--abc.gpt-eng.com")).toBe(true);
  });
  it("keeps published and custom-domain apps eligible", () => {
    expect(isPreviewHost("nexusai.lovable.app")).toBe(false);
    expect(isPreviewHost("preview-v2--shop.example.com")).toBe(false);
    expect(
      shouldRegisterOfflineSupport({
        production: true,
        framed: false,
        hostname: "localhost",
        switchValue: "on",
      }),
    ).toBe(true);
    expect(
      shouldRegisterOfflineSupport({
        production: true,
        framed: false,
        hostname: "localhost",
        switchValue: null,
      }),
    ).toBe(false);
  });
});
