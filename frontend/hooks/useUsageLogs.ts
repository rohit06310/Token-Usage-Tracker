import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import { buildParams } from "@/lib/utils";

export interface UsageLogItem {
  id: string;
  provider_id: string;
  model: string;
  tokens_in: number;
  tokens_out: number;
  cost: string;
  status: string;
  project_tag: string | null;
  created_at: string;
}

interface UseUsageLogsParams {
  providerId?: string | null;
  projectTag?: string | null;
  model?: string | null;
  dateFrom?: string | null;
  dateTo?: string | null;
  limit?: number;
  offset?: number;
}

interface UsageLogsResponse {
  items: UsageLogItem[];
  total: number;
}

export function useUsageLogs(params: UseUsageLogsParams = {}) {
  const { providerId, projectTag, model, dateFrom, dateTo, limit = 50, offset = 0 } = params;

  const searchParams = buildParams({
    provider_id: providerId,
    project_tag: projectTag,
    model,
    date_from: dateFrom,
    date_to: dateTo,
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const key = `/api/proxy/usage/?${searchParams.toString()}`;

  const { data, error, isLoading } = useSWR<UsageLogsResponse>(key, swrFetcher);

  return {
    data: data?.items,
    total: data?.total || 0,
    isLoading,
    isError: !!error,
    error,
  };
}
