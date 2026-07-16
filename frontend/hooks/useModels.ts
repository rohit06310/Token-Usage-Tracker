import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import { buildParams } from "@/lib/utils";
import type { ModelItem } from "@/lib/types";

export function useModels(providerId?: string | null) {
  const searchParams = buildParams({ provider_id: providerId });
  const key = `/api/proxy/usage/models?${searchParams.toString()}`;

  const { data, error, isLoading } = useSWR<ModelItem[]>(key, swrFetcher, {
    revalidateOnFocus: false,
  });

  return {
    models: data ?? [],
    isLoading,
    isError: !!error,
  };
}
