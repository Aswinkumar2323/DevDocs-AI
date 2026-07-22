import api from "./api";
import { SearchRequest, SearchResponse } from "@/types";

export const searchService = {
  search: async (request: SearchRequest): Promise<SearchResponse> => {
    const { data } = await api.post("/search", request);
    return data;
  },
};
