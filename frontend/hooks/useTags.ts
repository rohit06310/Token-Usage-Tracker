import useSWR from "swr";
import { swrFetcher } from "@/lib/api";
import type { TagItem } from "@/lib/types";

export function useTags() {
  const { data, error, isLoading } = useSWR<TagItem[]>(
    "/api/proxy/usage/tags",
    swrFetcher,
    { revalidateOnFocus: false }
  );

  return {
    tags: data ?? [],
    isLoading,
    isError: !!error,
  };
}
