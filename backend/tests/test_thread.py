import threading
from app.crawler.parser import ParserOrchestrator
from app.models.documentation_source import DocumentationSource
from app.database.session import SessionLocal

def run_in_thread():
    try:
        db = SessionLocal()
        source = db.query(DocumentationSource).filter(DocumentationSource.id == 3).first()
        if source:
            orchestrator = ParserOrchestrator()
            orchestrator.process_source(source.id)
        db.close()
    except Exception as e:
        import traceback
        traceback.print_exc()

t = threading.Thread(target=run_in_thread)
t.start()
t.join()
