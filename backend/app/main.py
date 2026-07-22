from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database.session import engine
from app.database.base import Base
import app.models  # ensure models are imported before create_all

Base.metadata.create_all(bind=engine)

from app.api.sources import router as sources_router
from app.api.pages import router as pages_router
from app.api.indexing import router as indexing_router
from app.api.search import router as search_router
from app.chat.api import router as chat_router

app = FastAPI(
    title="DevDocs AI",
    version="1.0.0",
    description="Self-Improving Documentation RAG Platform"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sources_router)
app.include_router(pages_router)
app.include_router(indexing_router)
app.include_router(search_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {
        "message": "DevDocs AI Backend Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }