import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import type { Provider } from "@/lib/types";

export function useProviders() {
  const { data, error, isLoading } = useSWR<Provider[]>(
    "/api/proxy/providers/",
    swrFetcher,
    { revalidateOnFocus: false }
  );

  return {
    providers: data ?? [],
    isLoading,
    isError: !!error,
    error,
  };
}
