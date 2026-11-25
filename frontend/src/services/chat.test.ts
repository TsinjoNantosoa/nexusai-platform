import { beforeEach, describe, expect, it } from "vitest";
import { MockApiClient } from "./mock";
let api: MockApiClient;
beforeEach(async () => {
  api = new MockApiClient();
  await api.login("demo@nexusai.app", "demo1234");
});
describe("FE-02 simulated rules, not server validation", () => {
  it("charges exactly 2 gems on success", async () => {
    const c = await api.createConversation("luna");
    await api.send(c.id, "Idée", "k", new AbortController().signal, () => {}, "fr");
    expect((await api.wallet()).balance).toBe(18);
  });
  it("rejects messages longer than 2000 characters without a charge", async () => {
    const c = await api.createConversation("luna");
    await expect(
      api.send(c.id, "a".repeat(2001), "k", new AbortController().signal, () => {}, "fr"),
    ).rejects.toMatchObject({ code: "validation" });
    expect((await api.wallet()).balance).toBe(20);
  });
  it("refunds a terminal failure once while preserving debit history", async () => {
    const c = await api.createConversation("atlas");
    await expect(
      api.send(c.id, "Question", "k", new AbortController().signal, () => {}, "fr", "failure"),
    ).rejects.toMatchObject({ code: "ai_failure" });
    await expect(
      api.send(c.id, "Question", "k", new AbortController().signal, () => {}, "fr", "failure"),
    ).rejects.toMatchObject({ code: "already_processed" });
    expect((await api.wallet()).balance).toBe(20);
    expect((await api.entries()).filter((e) => e.type === "restitution")).toHaveLength(1);
    expect((await api.entries()).filter((e) => e.type === "message")).toHaveLength(1);
  });
  it("permits only one active generation per account", async () => {
    const c = await api.createConversation("luna");
    const first = api.send(c.id, "Question", "one", new AbortController().signal, () => {}, "fr");
    await expect(
      api.send(c.id, "Question", "two", new AbortController().signal, () => {}, "fr"),
    ).rejects.toMatchObject({ code: "generation_active" });
    await first;
    expect((await api.wallet()).balance).toBe(18);
  });
  it("does not increase affinity through gem purchases", async () => {
    const c = await api.createConversation("luna");
    const o = await api.checkout("premium", "k");
    await api.simulatePayment(o.id, "success");
    expect((await api.conversation(c.id)).affinity).toBe(0);
  });
  it("blocks messages to a blocked character without charging", async () => {
    const c = await api.createConversation("echo");
    await api.block("echo");
    await expect(
      api.send(c.id, "Question", "k", new AbortController().signal, () => {}, "fr"),
    ).rejects.toMatchObject({ code: "character_blocked" });
    expect((await api.wallet()).balance).toBe(20);
  });
  it("prevents non-admin access to reports", async () => {
    await expect(api.reports()).rejects.toMatchObject({ code: "forbidden" });
  });
  it("does not credit canceled payments", async () => {
    const o = await api.checkout("starter", "k");
    await api.simulatePayment(o.id, "canceled");
    expect((await api.wallet()).balance).toBe(20);
  });
});
