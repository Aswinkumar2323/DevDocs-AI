// ── Documentation Source ──────────────────────────────────────────────
export interface Source {
  id: number;
  name: string;
  base_url: string;
  status: string;
  technology?: string;
  version?: string;
  page_count?: number;
  last_crawl?: string;
  created_at?: string;
  updated_at?: string;
}

export interface CreateSourcePayload {
  name: string;
  base_url: string;
  technology?: string;
  version?: string;
}

export interface CrawlStatus {
  source_id: number;
  status: string;
  total_discovered_pages: number;
  processed_pages: number;
  failed_pages: number;
}

// ── Pages ─────────────────────────────────────────────────────────────
export interface Page {
  id: number;
  source_id: number;
  url: string;
  title: string | null;
  checksum: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface PageWithContent extends Page {
  markdown: string | null;
  html: string | null;
}

// ── Indexing ──────────────────────────────────────────────────────────
export interface IndexingStatus {
  source_id: number;
  source_name: string;
  status: string;
  total_pages: number;
  processed_pages: number;
  indexed_pages: number;
  total_chunks: number;
}

// ── Retrieval / Search ───────────────────────────────────────────────
export type SearchMode = "vector" | "hybrid";

export interface SearchRequest {
  query: string;
  source_id?: number | null;
  top_k: number;
  search_type: SearchMode;
}

export interface SearchResult {
  score: number;
  page_title: string | null;
  heading: string | null;
  url: string;
  content: string;
  source_name: string | null;
  chunk_index: number;
}

export interface SearchResponse {
  query: string;
  results: SearchResult[];
  total: number;
}

export interface RetrievalChunk {
  id?: string | number;
  content: string;
  similarity_score: number;
  page_title: string | null;
  page_url: string;
  heading?: string | null;
  metadata?: Record<string, unknown>;
}

// ── Chat ──────────────────────────────────────────────────────────────
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  citations?: Citation[];
  retrieved_chunks?: RetrievedChunkDetail[];
  timestamp: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface Citation {
  source_name: string | null;
  page_title: string | null;
  page_url: string;
  heading: string | null;
  content_snippet: string;
}

export interface RetrievedChunkDetail {
  content: string;
  page_title: string | null;
  page_url: string;
  heading: string | null;
  similarity_score: number;
  chunk_index: number;
  token_count: number;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatResponse {
  answer: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunkDetail[];
  conversation_id: string;
  usage: TokenUsage;
}

// ── Conversations ────────────────────────────────────────────────────
export interface Conversation {
  id: string;
  title: string;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface ConversationMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  citations: Citation[];
  retrieved_chunks: RetrievedChunkDetail[];
  created_at: string;
}

export interface ConversationDetail {
  id: string;
  title: string;
  messages: ConversationMessage[];
  created_at: string;
  updated_at: string;
}

// ── Dashboard ─────────────────────────────────────────────────────────
export interface DashboardStats {
  total_sources: number;
  total_pages: number;
  total_chunks: number;
  total_embeddings: number;
  last_crawl_time: string | null;
  vector_db_status: "healthy" | "offline" | "unknown";
}

export interface ChunkData {
  id: number;
  page_id: number;
  heading: string | null;
  content: string;
  chunk_index: number;
  token_count: number;
  created_at: string;
}

export interface CrawlJob {
  id: number;
  source_name: string;
  status: string;
  pages_processed: number;
  total_pages: number;
  started_at: string;
}
