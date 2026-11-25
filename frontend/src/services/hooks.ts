import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { getApi } from "./api";
export function useSession() {
  return useQuery({
    queryKey: ["session"],
    queryFn: () => getApi().me(),
    retry: false,
    staleTime: Infinity,
  });
}
export function useWallet(enabled = true) {
  return useQuery({
    queryKey: ["wallet"],
    queryFn: () => getApi().wallet(),
    enabled,
    retry: false,
  });
}
export function useRefresh() {
  const qc = useQueryClient();
  return async () => {
    await Promise.all(
      ["wallet", "entries", "orders", "conversations", "conversation", "reports", "blocked"].map(
        (key) => qc.invalidateQueries({ queryKey: [key] }),
      ),
    );
  };
}
export function useOnline() {
  const [online, setOnline] = useState(true);
  const qc = useQueryClient();
  useEffect(() => {
    const update = () => {
      setOnline(navigator.onLine);
      if (navigator.onLine) void qc.invalidateQueries();
    };
    setOnline(navigator.onLine);
    window.addEventListener("online", update);
    window.addEventListener("offline", update);
    return () => {
      window.removeEventListener("online", update);
      window.removeEventListener("offline", update);
    };
  }, [qc]);
  return online;
}
