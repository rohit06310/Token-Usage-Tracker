import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import { buildParams } from "@/lib/utils";
import type { AlertsResponse } from "@/lib/types";

interface UseRecentAlertsParams {
  limit?: number;
  offset?: number;
}

export function useRecentAlerts(params: UseRecentAlertsParams = {}) {
  const { limit = 50, offset = 0 } = params;

  const searchParams = buildParams({ limit, offset });
  const key = `/api/proxy/alerts/recent?${searchParams.toString()}`;

  const { data, error, isLoading, mutate } = useSWR<AlertsResponse>(key, swrFetcher, {
    refreshInterval: 60_000, // Refresh every 60s
  });

  return {
    data,
    isLoading,
    isError: !!error,
    error,
    refresh: mutate,
  };
}
