import api from "./api";
import {
  ChatRequest,
  ChatResponse,
  Conversation,
  ConversationDetail,
} from "@/types";

export const chatService = {
  /** Send a chat message through the RAG pipeline. */
  sendMessage: async (payload: ChatRequest): Promise<ChatResponse> => {
    const { data } = await api.post("/chat", payload);
    return data;
  },

  /** List all conversations (most recent first). */
  getConversations: async (): Promise<Conversation[]> => {
    const { data } = await api.get("/chat/conversations");
    return data;
  },

  /** Get a conversation with all its messages. */
  getConversation: async (id: string): Promise<ConversationDetail> => {
    const { data } = await api.get(`/chat/conversations/${id}`);
    return data;
  },

  /** Rename a conversation. */
  updateConversation: async (
    id: string,
    title: string
  ): Promise<Conversation> => {
    const { data } = await api.patch(`/chat/conversations/${id}`, { title });
    return data;
  },

  /** Delete a conversation and all its messages. */
  deleteConversation: async (id: string): Promise<void> => {
    await api.delete(`/chat/conversations/${id}`);
  },
};
