import asyncio
from fastapi import BackgroundTasks
from starlette.concurrency import run_in_threadpool
from app.crawler.parser import start_crawl
from app.models.documentation_source import DocumentationSource
from app.database.session import SessionLocal

async def simulate_background_task():
    db = SessionLocal()
    source = db.query(DocumentationSource).filter(DocumentationSource.id == 3).first()
    db.close()
    
    if source:
        await run_in_threadpool(start_crawl, source.id)

if __name__ == "__main__":
    asyncio.run(simulate_background_task())
