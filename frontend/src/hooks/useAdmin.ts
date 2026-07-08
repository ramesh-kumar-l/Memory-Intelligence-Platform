import { useQuery } from "@tanstack/react-query";

import { getClient } from "../api/client";

export function useHealth(enabled: boolean) {
  return useQuery({
    queryKey: ["admin", "health"],
    queryFn: () => getClient().admin.health(),
    enabled,
    retry: false,
  });
}
