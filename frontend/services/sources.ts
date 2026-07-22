import api from "./api";
import { Source, CreateSourcePayload, CrawlStatus } from "@/types";

export const sourcesService = {
  getAll: async (): Promise<Source[]> => {
    const { data } = await api.get("/sources");
    return data;
  },

  getById: async (id: number): Promise<Source> => {
    const { data } = await api.get(`/sources/${id}`);
    return data;
  },

  create: async (payload: CreateSourcePayload): Promise<Source> => {
    const { data } = await api.post("/sources", payload);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/sources/${id}`);
  },

  startCrawl: async (id: number): Promise<{ message: string; source_id: number }> => {
    const { data } = await api.post(`/sources/crawl/${id}`);
    return data;
  },

  getCrawlStatus: async (id: number): Promise<CrawlStatus> => {
    const { data } = await api.get(`/sources/crawl/status/${id}`);
    return data;
  },
};
