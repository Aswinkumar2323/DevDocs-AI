import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { indexingService } from "@/services/indexing";

export function useIndexingStatus(sourceId: number, enabled = false) {
  return useQuery({
    queryKey: ["indexing-status", sourceId],
    queryFn: () => indexingService.getStatus(sourceId),
    enabled,
    refetchInterval: enabled ? 3000 : false,
  });
}

export function useStartIndexing() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sourceId: number) => indexingService.indexSource(sourceId),
    onSuccess: (_, sourceId) => {
      queryClient.invalidateQueries({ queryKey: ["sources", sourceId] });
      queryClient.invalidateQueries({
        queryKey: ["indexing-status", sourceId],
      });
    },
  });
}

export function useIndexPage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (pageId: number) => indexingService.indexPage(pageId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["indexing-status"] });
    },
  });
}
