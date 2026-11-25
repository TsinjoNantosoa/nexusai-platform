import { describe, expect, it } from "vitest";
import { SseParser } from "./sse";

describe("SseParser", () => {
  it("reassembles fragmented and multiple events", () => {
    const parser = new SseParser();
    expect(parser.push('event: delta\ndata: {"delta":"é')).toEqual([]);
    expect(parser.push('clair"}\n\nevent: done\ndata: {"message":{}}\n\n')).toEqual([
      { event: "delta", data: '{"delta":"éclair"}' },
      { event: "done", data: '{"message":{}}' },
    ]);
  });

  it("flushes a final event without a trailing blank line", () => {
    const parser = new SseParser();
    expect(parser.push('event: error\r\ndata: {"code":"ai_failure"}', true)).toEqual([
      { event: "error", data: '{"code":"ai_failure"}' },
    ]);
  });
});
