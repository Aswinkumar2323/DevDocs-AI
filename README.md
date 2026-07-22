# DevDocs AI — Self-Improving Documentation RAG Platform

DevDocs AI is a production-grade **Retrieval-Augmented Generation (RAG) platform** designed specifically for developer documentation. It crawls documentation websites, parses and chunks markdown content, generates vector embeddings, stores them in Qdrant, and provides a RAG answer generation engine with inline source citations and multi-turn conversation support.

---

## 🌟 Architecture & RAG Pipeline

```text
                                  ┌────────────────────────┐
                                  │   Web Documentation    │
                                  └───────────┬────────────┘
                                              │
                                     Playwright Crawler
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │  Page Markdown & DB    │
                                  └───────────┬────────────┘
                                              │
                                      Tiktoken Chunking
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │   OpenAI Embeddings    │
                                  │(text-embedding-3-small)│
                                  └───────────┬────────────┘
                                              │
                                              ▼
                                  ┌────────────────────────┐
                                  │ Vector Store (Qdrant)  │
                                  └───────────┬────────────┘
                                              │
                                              │
User Question ──► Hybrid Search (Vector + Full-Text RRF) ──► Candidate Chunks
                                                                 │
                                                          Heuristic Reranker
                                                                 │
                                                          Context Builder
                                                                 │
                                                          Prompt Builder
                                                                 │
                                                       OpenAI GPT-4o-mini
                                                                 │
                                                          Citation Engine
                                                                 │
                                                                 ▼
                                                       Grounded AI Answer
```

---

## ✨ Features

- **🕸️ Automated Documentation Crawler**: Headless Playwright + BeautifulSoup4 crawler with depth limit, URL deduplication, and checksum tracking.
- **📄 Markdown Parser & Token-Aware Chunking**: Hierarchical section splitting preserving headers and token budgeting using `tiktoken`.
- **🔍 Hybrid Retrieval Engine**: Vector similarity search + Qdrant full-text payload search combined via **Reciprocal Rank Fusion (RRF)**.
- **🎯 Contextual Reranker**: Multi-factor reranking based on vector similarity, title/heading token overlap, term frequency, and exact symbol matching.
- **🤖 Grounded RAG Generation**: Hallucination-prevention prompts, structured markdown responses, and automatic inline source citation tracking.
- **💬 Conversation Management**: Multi-turn chat persistence with PostgreSQL cascade deletion, auto-title generation, and conversation history replay.
- **🖥️ 3-Panel Admin & Chat UI**: Built with Next.js 16, React 19, TailwindCSS v4, Base UI, and TanStack Query. Includes a live **Retrieved Context Inspector** panel showing relevance scores and token counts.

---

## 🛠️ Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.12)
- **Database**: PostgreSQL with [SQLAlchemy 2.0](https://www.sqlalchemy.org/) ORM & `psycopg` driver
- **Vector Database**: [Qdrant](https://qdrant.tech/) (Vector similarity + Full-text payload index)
- **Embeddings & LLM**: OpenAI (`text-embedding-3-small`, `gpt-4o-mini`)
- **Tokenizer**: `tiktoken` (`cl100k_base`)
- **Crawler & Parser**: Playwright, BeautifulSoup4, Markdownify

### Frontend
- **Framework**: [Next.js 16](https://nextjs.org/) (App Router, React 19)
- **Styling**: Tailwind CSS v4, Base UI, Lucide Icons
- **State & Data Fetching**: TanStack Query (`@tanstack/react-query`), Axios
- **Markdown & Code Display**: `react-markdown`, `remark-gfm`, `rehype-highlight`, `highlight.js` (GitHub Dark theme)

---

## 📁 Repository Structure

```text
DevDocs-AI/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI routers (sources, pages, indexing, search)
│   │   ├── chat/            # RAG Chat Module (service, context, prompt, LLM, citations)
│   │   ├── core/            # App configuration & environment settings
│   │   ├── crawler/         # Playwright crawler & parser orchestrator
│   │   ├── database/        # SQLAlchemy session & base models
│   │   ├── indexing/        # Chunking, embeddings, vector store, reranker
│   │   ├── models/          # SQLAlchemy DB models (Source, Page, Chunk, Conversation, Message)
│   │   ├── schemas/         # Pydantic request/response models
│   │   └── main.py          # FastAPI application entry point
│   ├── .env                 # Backend environment variables
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile
│
├── frontend/
│   ├── app/
│   │   ├── chat/            # 3-Panel AI Chat & Context Inspector page
│   │   ├── dashboard/       # System metrics & statistics
│   │   ├── pages/           # Crawled page inspector
│   │   ├── retrieval/       # Search playground
│   │   ├── sources/         # Source management & crawler trigger
│   │   └── layout.tsx       # App layout & providers
│   ├── components/
│   │   ├── layout/          # Navbar, Sidebar, AppLayout
│   │   ├── shared/          # MarkdownViewer, StatusBadge, PageHeader, EmptyState
│   │   └── ui/              # Button, Card, Dialog, ScrollArea, Input
│   ├── hooks/               # React Query hooks
│   ├── services/            # Axios API client services
│   ├── types/               # TypeScript type definitions
│   └── package.json
└── README.md
```

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.12+**
- **Node.js 18+** & `npm`
- **Docker** & **Docker Compose** (for PostgreSQL & Qdrant)
- **OpenAI API Key**

---

### 1. Database & Infrastructure Setup

Launch PostgreSQL and Qdrant using Docker:

```bash
cd backend
docker-compose up -d
```

This starts:
- **PostgreSQL**: `localhost:5433` (or `5432` depending on configuration)
- **Qdrant Vector DB**: `http://localhost:6333`

---

### 2. Backend Setup

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .venv\Scripts\Activate.ps1

   # Linux/macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Configure Environment Variables (`.env`)**:
   Create a `.env` file in the `backend` directory:
   ```ini
   DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5433/devdocs
   QDRANT_URL=http://localhost:6333
   OPENAI_API_KEY=sk-proj-your-openai-api-key
   SECRET_KEY=your_secret_key
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   ```

5. **Start the backend server**:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
   *FastAPI Interactive Docs will be available at `http://localhost:8000/docs`.*

---

### 3. Frontend Setup

1. **Navigate to the frontend directory**:
   ```bash
   cd frontend
   ```

2. **Install Node dependencies**:
   ```bash
   npm install
   ```

3. **Start the Next.js development server**:
   ```bash
   npm run dev
   ```
   *The Web UI will be available at `http://localhost:3000`.*

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server health check |
| `POST` | `/sources` | Add a new documentation source |
| `GET` | `/sources` | List all documentation sources |
| `POST` | `/sources/crawl/{id}` | Start crawler job for a source |
| `POST` | `/indexing/source/{id}` | Chunk, embed, and index a source in Qdrant |
| `POST` | `/search` | Search vector database (vector or hybrid mode) |
| `POST` | `/chat` | RAG Answer Pipeline (query → hybrid search → rerank → context → LLM → citations) |
| `GET` | `/chat/conversations` | List conversation threads |
| `GET` | `/chat/conversations/{id}` | Get full conversation thread with message history |
| `PATCH` | `/chat/conversations/{id}` | Rename a conversation |
| `DELETE` | `/chat/conversations/{id}` | Permanently delete a conversation and its messages |

---

## 🧪 Coding Standards & Best Practices

- **Strict Type Hints**: Full type annotation across FastAPI schemas (`Pydantic v2`) and TypeScript interfaces.
- **Dependency Injection**: Database sessions managed cleanly via `Depends(get_db)`.
- **Hallucination Prevention**: Prompts explicitly constrain the LLM to answered content only and require inline `[Source: Title](url)` citations.
- **Atomic Operations & Cascading**: Foreign key cascade deletes ensure clean storage management without orphan rows.
- **Responsive Layout Architecture**: Flex containers with `overflow-y-auto` preventing viewport collapse and double-scrollbar defects.

---

## 📄 License

This project is licensed under the MIT License.
