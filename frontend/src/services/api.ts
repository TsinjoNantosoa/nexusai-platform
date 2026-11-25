import { MockApiClient } from "./mock";
import { HttpApiClient } from "./http";
import { dataMode } from "./config";
import type { ApiClient } from "./types";
export const isMock = dataMode === "mock";
let browserMock: MockApiClient | undefined;
let browserHttp: HttpApiClient | undefined;
export function getApi(): ApiClient {
  if (isMock) {
    if (typeof window === "undefined") return new MockApiClient();
    browserMock ??= new MockApiClient();
    return browserMock;
  }
  if (typeof window === "undefined")
    return new HttpApiClient(import.meta.env["VITE_API_BASE_URL"] ?? "/api/v1");
  browserHttp ??= new HttpApiClient(import.meta.env["VITE_API_BASE_URL"] ?? "/api/v1");
  return browserHttp;
}
export const catalogueOptions = {
  queryKey: ["catalogue"],
  queryFn: () => getApi().catalogue(),
  staleTime: 60000,
};
export const productsOptions = {
  queryKey: ["products"],
  queryFn: () => getApi().products(),
  staleTime: 60000,
};
