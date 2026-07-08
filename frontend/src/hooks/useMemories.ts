import type { CreateMemoryRequest, MemoryState, UpdateMemoryRequest } from "@mip/sdk";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getClient } from "../api/client";

export interface MemoriesListParams {
  namespace?: string;
  state?: MemoryState;
  limit?: number;
  continuationToken?: string;
}

export function useMemoriesList(params: MemoriesListParams) {
  return useQuery({
    queryKey: ["memories", "list", params],
    queryFn: () => getClient().memories.list(params),
  });
}

export function useMemory(memoryId: string | undefined, version?: number) {
  return useQuery({
    queryKey: ["memories", "detail", memoryId, version ?? "latest"],
    queryFn: () => getClient().memories.get(memoryId as string, { version }),
    enabled: memoryId !== undefined,
  });
}

export function useMemoryVersions(memoryId: string | undefined) {
  return useQuery({
    queryKey: ["memories", "versions", memoryId],
    queryFn: () => getClient().memories.listVersions(memoryId as string),
    enabled: memoryId !== undefined,
  });
}

export function useCreateMemory() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (request: CreateMemoryRequest) => getClient().memories.create(request),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["memories", "list"] });
    },
  });
}

export function useUpdateMemory(memoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      request,
      expectedVersion,
    }: {
      request: UpdateMemoryRequest;
      expectedVersion: number;
    }) => getClient().memories.update(memoryId, request, { expectedVersion }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["memories", "detail", memoryId] });
      void queryClient.invalidateQueries({ queryKey: ["memories", "versions", memoryId] });
      void queryClient.invalidateQueries({ queryKey: ["memories", "list"] });
    },
  });
}

function invalidateAfterLifecycleChange(
  queryClient: ReturnType<typeof useQueryClient>,
  memoryId: string,
): void {
  void queryClient.invalidateQueries({ queryKey: ["memories", "detail", memoryId] });
  void queryClient.invalidateQueries({ queryKey: ["memories", "list"] });
}

export function useArchiveMemory(memoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => getClient().memories.archive(memoryId),
    onSuccess: () => invalidateAfterLifecycleChange(queryClient, memoryId),
  });
}

export function useRestoreMemory(memoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => getClient().memories.restore(memoryId),
    onSuccess: () => invalidateAfterLifecycleChange(queryClient, memoryId),
  });
}

export function useDeleteMemory(memoryId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => getClient().memories.delete(memoryId),
    onSuccess: () => invalidateAfterLifecycleChange(queryClient, memoryId),
  });
}
