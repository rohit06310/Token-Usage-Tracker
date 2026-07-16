import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import { buildParams } from "@/lib/utils";
import type { CostBreakdownResponse } from "@/lib/types";

interface UseCostBreakdownParams {
  dateFrom?: string | null;
  dateTo?: string | null;
  projectTag?: string | null;
}

export function useCostBreakdown(params: UseCostBreakdownParams = {}) {
  const { dateFrom, dateTo, projectTag } = params;

  const searchParams = buildParams({
    date_from: dateFrom,
    date_to: dateTo,
    project_tag: projectTag,
  });

  const key = `/api/proxy/usage/cost-breakdown?${searchParams.toString()}`;

  const { data, error, isLoading } = useSWR<CostBreakdownResponse>(key, swrFetcher);

  return {
    data,
    isLoading,
    isError: !!error,
    error,
  };
}
