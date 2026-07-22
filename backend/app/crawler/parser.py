import logging
from sqlalchemy.orm import Session
from app.models.page import Page
from app.models.documentation_source import DocumentationSource
from app.crawler.discovery import Discovery
from app.crawler.crawler import Downloader
from app.crawler.extractor import Extractor
from app.crawler.markdown import MarkdownConverter
from app.crawler.checksum import ChecksumGenerator
from app.database.session import SessionLocal

logger = logging.getLogger(__name__)

class ParserOrchestrator:
    def __init__(self):
        self.downloader = None
        self.extractor = Extractor()
        self.markdown_converter = MarkdownConverter()

    def process_source(self, source_id: int):
        db: Session = SessionLocal()
        try:
            source = db.query(DocumentationSource).filter(DocumentationSource.id == source_id).first()
            if not source:
                logger.error(f"Source with id {source_id} not found.")
                return

            source.status = "crawling"
            db.commit()

            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                page = context.new_page()
                discovery = Discovery(source.base_url, page)
                self.downloader = Downloader(page)
                
                # Check for sitemap.xml first
                logger.info(f"Checking for sitemap.xml at {source.base_url}")
                urls = discovery.discover_via_sitemap()
                
                if urls:
                    logger.info(f"Sitemap found. Processing {len(urls)} URLs sequentially...")
                    for url in urls:
                        self.process_page(db, source_id, url)
                else:
                    logger.info(f"No sitemap found. Initiating single-pass BFS crawl...")
                    queue = [source.base_url]
                    visited = set()
                    max_pages = 500  # Default limit to prevent runaway crawling
                    
                    while queue and len(visited) < max_pages:
                        current_url = queue.pop(0)
                        if current_url in visited:
                            continue
                        visited.add(current_url)
                        
                        logger.info(f"Crawl Progress: {len(visited)} pages visited. Processing: {current_url}")
                        
                        # Process and save the page immediately
                        self.process_page(db, source_id, current_url)
                        
                        # Fetch the processed page html to extract further links
                        page_obj = db.query(Page).filter(Page.url == current_url).first()
                        if page_obj and page_obj.status == "processed" and page_obj.html:
                            # Parse page links from the downloaded HTML, enforcing path prefix matching
                            new_links = discovery.extract_links_from_html(
                                page_obj.html, 
                                current_url, 
                                check_path_prefix=True
                            )
                            for link in new_links:
                                if link not in visited and link not in queue:
                                    queue.append(link)
                    
                    logger.info(f"BFS Crawl finished. Visited {len(visited)} pages total.")

                browser.close()
                
            source.status = "processed"
            db.commit()
            logger.info(f"Successfully processed source {source_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error processing source {source_id}: {e}")
            import traceback
            with open("crawler_error.log", "w", encoding="utf-8") as f:
                f.write(traceback.format_exc())
                
            source = db.query(DocumentationSource).filter(DocumentationSource.id == source_id).first()
            if source:
                source.status = "failed"
                db.commit()
        finally:
            db.close()

    def process_page(self, db: Session, source_id: int, url: str):
        try:
            logger.info(f"Processing URL: {url}")
            
            # Check if page exists globally (since URL is unique in the DB)
            page = db.query(Page).filter(Page.url == url).first()
            if not page:
                page = Page(source_id=source_id, url=url, status="pending")
                db.add(page)
                db.commit()
                db.refresh(page)

            # Download
            page.status = "downloading"
            db.commit()
            
            raw_html = self.downloader.download_page(url)
            if not raw_html:
                page.status = "failed"
                db.commit()
                return

            # Extract
            cleaned_html = self.extractor.extract_main_content(raw_html)
            
            # Markdown
            markdown_content = self.markdown_converter.convert(cleaned_html)
            
            # Checksum
            checksum = ChecksumGenerator.generate(markdown_content)
            
            # Update DB if changed
            if page.checksum == checksum:
                logger.info(f"Page {url} unchanged. Skipping update.")
                page.status = "processed"
                db.commit()
                return
                
            page.html = raw_html
            page.markdown = markdown_content
            page.checksum = checksum
            
            # Try to extract title
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(raw_html, "html.parser")
            title_tag = soup.find("title")
            if title_tag:
                page.title = title_tag.text.strip()
                
            page.status = "processed"
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to process page {url}: {e}")
            page = db.query(Page).filter(Page.url == url).first()
            if page:
                page.status = "failed"
                db.commit()

# Expose a simple function for background tasks
def start_crawl(source_id: int):
    import sys
    import asyncio
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    orchestrator = ParserOrchestrator()
    orchestrator.process_source(source_id)
