from app.crawler.parser import ParserOrchestrator
from app.models.documentation_source import DocumentationSource
from app.database.session import SessionLocal

db = SessionLocal()
source = db.query(DocumentationSource).filter(DocumentationSource.id == 3).first()
if not source:
    print("Source 3 not found. Creating it.")
    source = DocumentationSource(name="devdocs", base_url="https://devdocs.io/javascript")
    db.add(source)
    db.commit()
    db.refresh(source)
    print(f"Created source {source.id}")

db.close()

try:
    orchestrator = ParserOrchestrator()
    print("Starting process_source...")
    orchestrator.process_source(source.id)
    print("process_source finished")
except Exception as e:
    import traceback
    traceback.print_exc()
