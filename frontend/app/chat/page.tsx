"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  FileText,
  ExternalLink,
  Bot,
  User,
  Plus,
  Trash2,
  MessageSquare,
  Copy,
  Check,
  Hash,
  Zap,
  Clock,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";

import { EmptyState } from "@/components/shared/empty-state";
import { MarkdownViewer } from "@/components/shared/markdown-viewer";
import { LoadingSpinner } from "@/components/shared/loading-spinner";
import { ConfirmationModal } from "@/components/shared/confirmation-modal";

import { chatService } from "@/services/chat";
import type {
  ChatMessage,
  ChatResponse,
  Citation,
  RetrievedChunkDetail,
  Conversation,
  TokenUsage,
} from "@/types";

// ── Helpers ──────────────────────────────────────────────────────────

function formatTime(dateStr: string) {
  return new Date(dateStr).toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatDate(dateStr: string) {
  const d = new Date(dateStr);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "Just now";
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return d.toLocaleDateString();
}

function scoreColor(score: number): string {
  if (score >= 0.85) return "text-emerald-400";
  if (score >= 0.7) return "text-sky-400";
  if (score >= 0.5) return "text-amber-400";
  return "text-red-400";
}

function scoreBg(score: number): string {
  if (score >= 0.85) return "border-emerald-500/30 bg-emerald-500/10";
  if (score >= 0.7) return "border-sky-500/30 bg-sky-500/10";
  if (score >= 0.5) return "border-amber-500/30 bg-amber-500/10";
  return "border-red-500/30 bg-red-500/10";
}

// ── Main Component ───────────────────────────────────────────────────

export default function ChatPage() {
  const queryClient = useQueryClient();

  // Chat state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<string | undefined>();
  const [selectedChunks, setSelectedChunks] = useState<RetrievedChunkDetail[]>(
    []
  );
  const [lastUsage, setLastUsage] = useState<TokenUsage | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Conversation management
  const [deleteTarget, setDeleteTarget] = useState<Conversation | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // ── Queries ──────────────────────────────────────────────────────

  const { data: conversations = [], isLoading: loadingConversations } =
    useQuery({
      queryKey: ["conversations"],
      queryFn: chatService.getConversations,
    });

  // ── Mutations ────────────────────────────────────────────────────

  const chatMutation = useMutation({
    mutationFn: (payload: { message: string; conversation_id?: string }) =>
      chatService.sendMessage(payload),
    onSuccess: (data: ChatResponse) => {
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.answer,
        citations: data.citations,
        retrieved_chunks: data.retrieved_chunks,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);
      setConversationId(data.conversation_id);
      setSelectedChunks(data.retrieved_chunks || []);
      setLastUsage(data.usage);
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
    },
    onError: (err: any) => {
      console.error("Chat error:", err);
      const detail =
        err?.response?.data?.detail ||
        err?.message ||
        "Sorry, I couldn't process your request. Please check that the backend is running.";

      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: `**Error:** ${detail}`,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => chatService.deleteConversation(id),
    onSuccess: (_, deletedId) => {
      queryClient.invalidateQueries({ queryKey: ["conversations"] });
      if (conversationId === deletedId) {
        handleNewChat();
      }
      setDeleteTarget(null);
    },
  });

  // ── Handlers ─────────────────────────────────────────────────────

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const handleSend = (e?: React.FormEvent | React.KeyboardEvent) => {
    if (e) e.preventDefault();
    const messageText = input.trim();
    if (!messageText || chatMutation.isPending) return;

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      content: messageText,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");

    chatMutation.mutate({
      message: messageText,
      conversation_id: conversationId || undefined,
    });
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setConversationId(undefined);
    setSelectedChunks([]);
    setLastUsage(null);
    setInput("");
  };

  const handleLoadConversation = async (conv: Conversation) => {
    if (conv.id === conversationId) return;

    try {
      const detail = await chatService.getConversation(conv.id);
      setConversationId(detail.id);
      setMessages(
        detail.messages.map((msg) => ({
          id: String(msg.id),
          role: msg.role,
          content: msg.content,
          citations: msg.citations,
          retrieved_chunks: msg.retrieved_chunks,
          timestamp: msg.created_at,
        }))
      );

      // Show chunks from the last assistant message
      const lastAssistant = [...detail.messages]
        .reverse()
        .find((m) => m.role === "assistant");
      if (lastAssistant?.retrieved_chunks?.length) {
        setSelectedChunks(lastAssistant.retrieved_chunks);
      } else {
        setSelectedChunks([]);
      }
      setLastUsage(null);
    } catch {
      // Silently fail — conversation may have been deleted
    }
  };

  const handleCopyMessage = async (content: string, id: string) => {
    await navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  // ── Render ───────────────────────────────────────────────────────

  return (
    <TooltipProvider>
      <div className="flex flex-col h-full w-full overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 sm:px-6 border-b border-border shrink-0 flex items-center justify-between bg-card">
          <div>
            <h1 className="text-lg font-semibold tracking-tight">AI Chat</h1>
            <p className="text-xs text-muted-foreground">
              RAG-powered answers grounded in your documentation
            </p>
          </div>
          {lastUsage && (
            <div className="hidden sm:flex items-center gap-3 text-xs text-muted-foreground">
              <span className="flex items-center gap-1">
                <Zap className="h-3 w-3" />
                {lastUsage.total_tokens.toLocaleString()} tokens
              </span>
              <span>
                {lastUsage.prompt_tokens.toLocaleString()} prompt /{" "}
                {lastUsage.completion_tokens.toLocaleString()} completion
              </span>
            </div>
          )}
        </div>

        <div className="flex flex-1 overflow-hidden min-h-0">
          {/* ── Left Panel: Conversations ──────────────────────────── */}
          <div className="w-64 flex flex-col border-r border-border bg-card shrink-0 h-full">
            <div className="p-3 border-b border-border shrink-0">
              <Button
                id="new-chat-button"
                onClick={handleNewChat}
                variant="outline"
                size="sm"
                className="w-full justify-start gap-2"
              >
                <Plus className="h-3.5 w-3.5" />
                New Chat
              </Button>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-0.5 min-h-0">
              {loadingConversations ? (
                <div className="py-8 flex justify-center">
                  <LoadingSpinner size="sm" />
                </div>
              ) : conversations.length === 0 ? (
                <div className="py-8 text-center text-xs text-muted-foreground">
                  No conversations yet
                </div>
              ) : (
                conversations.map((conv) => (
                  <div
                    key={conv.id}
                    className={`group flex items-center gap-2 rounded-md px-2.5 py-2 cursor-pointer transition-colors ${
                      conversationId === conv.id
                        ? "bg-accent text-accent-foreground"
                        : "hover:bg-accent/50 text-muted-foreground hover:text-foreground"
                    }`}
                    onClick={() => handleLoadConversation(conv)}
                  >
                    <MessageSquare className="h-3.5 w-3.5 shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium truncate">
                        {conv.title}
                      </p>
                      <p className="text-[10px] text-muted-foreground">
                        {conv.message_count} msgs · {formatDate(conv.updated_at)}
                      </p>
                    </div>
                    <Tooltip>
                      <TooltipTrigger
                        className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-destructive/10 hover:text-destructive transition-all"
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteTarget(conv);
                        }}
                      >
                        <Trash2 className="h-3 w-3" />
                      </TooltipTrigger>
                      <TooltipContent side="right">Delete</TooltipContent>
                    </Tooltip>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* ── Center Panel: Chat ─────────────────────────────────── */}
          <div className="flex flex-1 flex-col h-full min-w-0 bg-background">
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-4 min-h-0">
              <div className="max-w-3xl mx-auto space-y-6">
                {messages.length === 0 && (
                  <EmptyState
                    icon={Bot}
                    title="Start a conversation"
                    description="Ask a question about your indexed documentation. The RAG pipeline will retrieve relevant chunks and generate a grounded answer."
                  />
                )}

                {messages.map((msg) => (
                  <div key={msg.id} className="flex gap-3 group">
                    <div
                      className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
                        msg.role === "user"
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      }`}
                    >
                      {msg.role === "user" ? (
                        <User className="h-4 w-4" />
                      ) : (
                        <Bot className="h-4 w-4" />
                      )}
                    </div>
                    <div className="flex-1 min-w-0 space-y-2">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">
                          {msg.role === "user" ? "You" : "DevDocs AI"}
                        </span>
                        <span className="text-xs text-muted-foreground">
                          {formatTime(msg.timestamp)}
                        </span>
                        {msg.role === "assistant" && (
                          <Tooltip>
                            <TooltipTrigger
                              className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-accent transition-all"
                              onClick={() =>
                                handleCopyMessage(msg.content, msg.id)
                              }
                            >
                              {copiedId === msg.id ? (
                                <Check className="h-3 w-3 text-emerald-400" />
                              ) : (
                                <Copy className="h-3 w-3 text-muted-foreground" />
                              )}
                            </TooltipTrigger>
                            <TooltipContent>Copy response</TooltipContent>
                          </Tooltip>
                        )}
                      </div>

                      {/* Sources badges at TOP of assistant response */}
                      {msg.role === "assistant" && msg.citations && msg.citations.length > 0 && (
                        <div className="py-1.5 px-2.5 rounded-lg bg-muted/30 border border-border/50 space-y-1 my-1">
                          <div className="flex items-center gap-1.5 text-[11px] font-medium text-muted-foreground">
                            <FileText className="h-3 w-3 text-primary" />
                            <span>Sources referenced:</span>
                          </div>
                          <div className="flex flex-wrap gap-1.5">
                            {msg.citations.map((cit, i) => (
                              <Badge
                                key={i}
                                variant="outline"
                                className="text-xs cursor-pointer hover:bg-accent transition-colors bg-background"
                                onClick={() => {
                                  if (msg.retrieved_chunks?.length) {
                                    setSelectedChunks(msg.retrieved_chunks);
                                  }
                                }}
                              >
                                {cit.page_title || cit.source_name || "Source"}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="text-sm leading-relaxed">
                        {msg.role === "assistant" ? (
                          <MarkdownViewer content={msg.content} />
                        ) : (
                          <p>{msg.content}</p>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {/* Thinking indicator */}
                {chatMutation.isPending && (
                  <div className="flex gap-3">
                    <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-muted text-muted-foreground">
                      <Bot className="h-4 w-4" />
                    </div>
                    <div className="flex items-center gap-2 py-2">
                      <LoadingSpinner size="sm" />
                      <span className="text-sm text-muted-foreground">
                        Searching docs & generating answer...
                      </span>
                    </div>
                  </div>
                )}

                <div ref={messagesEndRef} />
              </div>
            </div>

            {/* Input */}
            <div className="border-t border-border px-4 py-3 sm:px-6 lg:px-8 shrink-0 bg-card/30">
              <form
                onSubmit={handleSend}
                className="max-w-3xl mx-auto flex gap-2"
              >
                <Textarea
                  id="chat-input"
                  placeholder="Ask about your documentation..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={handleKeyDown}
                  rows={1}
                  className="min-h-[40px] max-h-32 resize-none"
                />
                <Button
                  id="send-button"
                  type="submit"
                  size="icon"
                  disabled={!input.trim() || chatMutation.isPending}
                  className="shrink-0"
                >
                  <Send className="h-4 w-4" />
                </Button>
              </form>
            </div>
          </div>

          {/* ── Right Panel: Context Inspector ─────────────────────── */}
          <div className="w-80 lg:w-96 flex flex-col border-l border-border bg-card shrink-0 h-full">
            <div className="px-4 py-3 border-b border-border shrink-0">
              <h2 className="text-sm font-semibold">Retrieved Context</h2>
              <p className="text-xs text-muted-foreground">
                {selectedChunks.length > 0
                  ? `${selectedChunks.length} chunks · ${selectedChunks.reduce((sum, c) => sum + c.token_count, 0).toLocaleString()} tokens`
                  : "Chunks sent to the LLM"}
              </p>
            </div>

            <div className="flex-1 overflow-y-auto p-3 space-y-2.5 min-h-0">
              {selectedChunks.length === 0 ? (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  Context will appear here after the AI responds.
                </div>
              ) : (
                selectedChunks.map((chunk, index) => (
                  <Card
                    key={index}
                    className={`border transition-colors ${scoreBg(chunk.similarity_score)}`}
                  >
                    <CardHeader className="pb-2 pt-3 px-3">
                      <div className="flex items-start justify-between gap-2">
                        <CardTitle className="text-xs font-medium leading-tight">
                          {chunk.page_title || "Unknown Page"}
                          {chunk.heading && (
                            <span className="text-muted-foreground font-normal">
                              {" "}
                              › {chunk.heading}
                            </span>
                          )}
                        </CardTitle>
                        <Badge
                          variant="outline"
                          className={`shrink-0 text-[10px] font-mono ${scoreColor(chunk.similarity_score)}`}
                        >
                          {(chunk.similarity_score * 100).toFixed(1)}%
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="px-3 pb-3">
                      <p className="text-xs leading-relaxed text-muted-foreground line-clamp-4">
                        {chunk.content}
                      </p>
                      <Separator className="my-2" />
                      <div className="flex items-center justify-between">
                        <a
                          href={chunk.page_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors max-w-[70%]"
                        >
                          <ExternalLink className="h-2.5 w-2.5 shrink-0" />
                          <span className="truncate">{chunk.page_url}</span>
                        </a>
                        <div className="flex items-center gap-2 text-[10px] text-muted-foreground">
                          <span className="flex items-center gap-0.5">
                            <Hash className="h-2.5 w-2.5" />
                            {chunk.chunk_index}
                          </span>
                          <span className="flex items-center gap-0.5">
                            <Clock className="h-2.5 w-2.5" />
                            {chunk.token_count}t
                          </span>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))
              )}
            </div>
          </div>
        </div>

        {/* Delete confirmation modal */}
        <ConfirmationModal
          open={!!deleteTarget}
          onOpenChange={(open) => !open && setDeleteTarget(null)}
          title="Delete Conversation"
          description={`Delete "${deleteTarget?.title}"? This will permanently remove all messages.`}
          confirmLabel="Delete"
          loading={deleteMutation.isPending}
          onConfirm={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
        />
      </div>
    </TooltipProvider>
  );
}
