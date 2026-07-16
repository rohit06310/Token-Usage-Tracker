import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import type { DashboardSummaryResponse } from "@/lib/types";

export function useDashboardSummary() {
  const { data, error, isLoading, mutate } = useSWR<DashboardSummaryResponse>(
    "/api/proxy/dashboard/summary",
    swrFetcher,
    {
      refreshInterval: 30_000, // Live quota refresh every 30s
      revalidateOnFocus: true,
    }
  );

  return {
    data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
}
