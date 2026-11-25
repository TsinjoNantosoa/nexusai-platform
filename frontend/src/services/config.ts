export type DataMode = "mock" | "api";

export function resolveDataMode(value: unknown): DataMode {
  if (value === undefined) return "mock";
  if (value === "mock" || value === "api") return value;
  throw new Error(`Invalid VITE_DATA_MODE: expected "mock" or "api", received ${String(value)}`);
}

export const dataMode = resolveDataMode(import.meta.env["VITE_DATA_MODE"]);
