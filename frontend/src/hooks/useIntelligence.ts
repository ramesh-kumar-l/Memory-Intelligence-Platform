import type { ConsolidateRequestBody, ExportBundle, LearnRequestBody } from "@mip/sdk";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getClient } from "../api/client";

/** Graph edges touching one memory, outbound and inbound (Phase 4 task 1, ADR-0006). */
export function useRelationships(memoryId: string | undefined) {
  return useQuery({
    queryKey: ["memories", "relationships", memoryId],
    queryFn: () => getClient().memories.relationships(memoryId as string),
    enabled: memoryId !== undefined,
  });
}

/** Consolidate (Phase 4 task 2): merges duplicates into a primary memory. */
export function useConsolidate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: ConsolidateRequestBody) => getClient().consolidate.consolidate(request),
    onSuccess: (memory) => {
      void queryClient.invalidateQueries({ queryKey: ["memories"] });
      void queryClient.invalidateQueries({
        queryKey: ["memories", "relationships", memory.memory_id],
      });
    },
  });
}

/** Learn (Phase 4 task 3): derived semantics + trust maturation. */
export function useLearn() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: LearnRequestBody) => getClient().learn.learn(request),
    onSuccess: (memory) => {
      void queryClient.invalidateQueries({ queryKey: ["memories", "detail", memory.memory_id] });
      void queryClient.invalidateQueries({ queryKey: ["memories", "versions", memory.memory_id] });
    },
  });
}

/** Export (Phase 4 task 4): triggered on demand, not a background query. */
export function useExportBundle() {
  return useMutation({
    mutationFn: (namespace: string | undefined) => getClient().portability.export({ namespace }),
  });
}

/** Import (Phase 4 task 4): accepts a previously-exported bundle. */
export function useImportBundle() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (bundle: ExportBundle | Record<string, unknown>) =>
      getClient().portability.import_(bundle),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["memories"] });
    },
  });
}
