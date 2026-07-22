import api from "./api";
import { Page, PageWithContent } from "@/types";

export const pagesService = {
  getAll: async (params?: {
    source_id?: number;
    skip?: number;
    limit?: number;
  }): Promise<Page[]> => {
    const { data } = await api.get("/pages", { params });
    return data;
  },

  getById: async (id: number): Promise<PageWithContent> => {
    const { data } = await api.get(`/pages/${id}`);
    return data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/pages/${id}`);
  },
};
