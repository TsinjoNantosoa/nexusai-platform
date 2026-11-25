import { describe, expect, it } from "vitest";
import { resolveDataMode } from "./config";

describe("frontend data mode configuration", () => {
  it("defaults an unset mode to the demonstrator", () => {
    expect(resolveDataMode(undefined)).toBe("mock");
  });

  it("accepts only mock and api", () => {
    expect(resolveDataMode("mock")).toBe("mock");
    expect(resolveDataMode("api")).toBe("api");
    expect(() => resolveDataMode("fallback")).toThrow(/VITE_DATA_MODE/);
  });
});
