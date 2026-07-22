import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pagesService } from "@/services/pages";

export function usePages(params?: { source_id?: number; skip?: number; limit?: number }) {
  return useQuery({
    queryKey: ["pages", params],
    queryFn: () => pagesService.getAll(params),
  });
}

export function usePage(id: number | null) {
  return useQuery({
    queryKey: ["pages", id],
    queryFn: () => pagesService.getById(id!),
    enabled: id !== null && id !== undefined,
  });
}

export function useDeletePage() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => pagesService.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["pages"] });
    },
  });
}
