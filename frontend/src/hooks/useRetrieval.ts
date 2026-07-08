import type { ContextRequestBody, ExplainRequestBody, SearchRequestBody } from "@mip/sdk";
import { useQuery } from "@tanstack/react-query";

import { getClient } from "../api/client";

export function useSearch(request: SearchRequestBody, enabled: boolean) {
  return useQuery({
    queryKey: ["search", request],
    queryFn: () => getClient().search.search(request),
    enabled,
  });
}

export function useExplain(request: ExplainRequestBody | undefined) {
  return useQuery({
    queryKey: ["explain", request],
    queryFn: () => getClient().explain.explain(request as ExplainRequestBody),
    enabled: request !== undefined,
  });
}

export function useContextPackage(request: ContextRequestBody, enabled: boolean) {
  return useQuery({
    queryKey: ["context", request],
    queryFn: () => getClient().context.build(request),
    enabled,
  });
}
