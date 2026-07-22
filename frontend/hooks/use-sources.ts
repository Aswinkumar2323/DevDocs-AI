import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { sourcesService } from "@/services/sources";
import { CreateSourcePayload } from "@/types";

export function useSources() {
  return useQuery({
    queryKey: ["sources"],
    queryFn: sourcesService.getAll,
  });
}

export function useSource(id: number) {
  return useQuery({
    queryKey: ["sources", id],
    queryFn: () => sourcesService.getById(id),
    enabled: !!id,
  });
}

export function useCrawlStatus(id: number, enabled = false) {
  return useQuery({
    queryKey: ["crawl-status", id],
    queryFn: () => sourcesService.getCrawlStatus(id),
    enabled,
    refetchInterval: enabled ? 3000 : false,
  });
}

export function useCreateSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: CreateSourcePayload) => sourcesService.create(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
  });
}

export function useDeleteSource() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => sourcesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["sources"] });
    },
  });
}

export function useStartCrawl() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => sourcesService.startCrawl(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ["sources", id] });
      queryClient.invalidateQueries({ queryKey: ["crawl-status", id] });
    },
  });
}
