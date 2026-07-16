import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import { buildParams } from "@/lib/utils";
import type { UsageHistoryResponse } from "@/lib/types";

interface UseUsageHistoryParams {
  range?: string;
  groupBy?: string;
  providerId?: string | null;
  projectTag?: string | null;
  model?: string | null;
  dateFrom?: string | null;
  dateTo?: string | null;
}

export function useUsageHistory(params: UseUsageHistoryParams = {}) {
  const { range = "7d", groupBy = "day", providerId, projectTag, model, dateFrom, dateTo } = params;

  const searchParams = buildParams({
    range,
    group_by: groupBy,
    provider_id: providerId,
    project_tag: projectTag,
    model,
    date_from: dateFrom,
    date_to: dateTo,
  });

  const key = `/api/proxy/usage/history?${searchParams.toString()}`;

  const { data, error, isLoading } = useSWR<UsageHistoryResponse>(key, swrFetcher);

  return {
    data,
    isLoading,
    isError: !!error,
    error,
  };
}
