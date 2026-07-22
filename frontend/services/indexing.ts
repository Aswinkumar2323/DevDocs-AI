import api from "./api";
import { IndexingStatus } from "@/types";

export const indexingService = {
  indexSource: async (
    id: number
  ): Promise<{ message: string; source_id: number; source_name: string }> => {
    const { data } = await api.post(`/indexing/source/${id}`);
    return data;
  },

  indexPage: async (
    id: number
  ): Promise<{ message: string; page_id: number; page_url: string }> => {
    const { data } = await api.post(`/indexing/page/${id}`);
    return data;
  },

  getStatus: async (sourceId: number): Promise<IndexingStatus> => {
    const { data } = await api.get(`/indexing/status/${sourceId}`);
    return data;
  },
};
