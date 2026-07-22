import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
import httpx
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger(__name__)


from playwright.sync_api import Page

class Discovery:
    def __init__(self, base_url: str, page: Page):
        self.base_url = base_url.rstrip("/")
        self.domain = urlparse(self.base_url).netloc
        # Setup synchronous client for simplicity since crawl runs in background job
        self.client = httpx.Client(timeout=10.0, follow_redirects=True)
        self.page = page

    def _is_valid_url(self, url: str, check_path_prefix: bool = False) -> bool:
        parsed = urlparse(url)
        # Only allow same domain and http/https
        if parsed.scheme not in ["http", "https"]:
            return False
        if parsed.netloc != self.domain:
            return False
        # Avoid common non-html files
        if any(url.lower().endswith(ext) for ext in [".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip", ".tar.gz"]):
            return False
        
        if check_path_prefix:
            base_path = urlparse(self.base_url).path.rstrip("/")
            if base_path and not parsed.path.startswith(base_path):
                return False
                
        return True

    def extract_links_from_html(self, html: str, current_url: str, check_path_prefix: bool = True) -> set[str]:
        if not html:
            return set()
        soup = BeautifulSoup(html, "html.parser")
        urls = set()
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            # Resolve relative URLs
            full_url = urljoin(current_url, href)
            normalized = self._normalize_url(full_url)
            
            if self._is_valid_url(normalized, check_path_prefix=check_path_prefix):
                urls.add(normalized)
        return urls


    def _normalize_url(self, url: str) -> str:
        # Remove fragments
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    def discover_via_sitemap(self) -> set[str]:
        urls = set()
        sitemap_url = f"{self.base_url}/sitemap.xml"
        try:
            response = self.client.get(sitemap_url)
            if response.status_code == 200:
                root = ET.fromstring(response.content)
                # sitemap namespace can vary, so we search generically
                for loc in root.iter():
                    if "loc" in loc.tag and loc.text:
                        url = self._normalize_url(loc.text.strip())
                        if self._is_valid_url(url):
                            urls.add(url)
                logger.info(f"Discovered {len(urls)} URLs via sitemap.")
            else:
                logger.info(f"Sitemap not found at {sitemap_url}")
        except Exception as e:
            logger.warning(f"Failed to fetch or parse sitemap: {e}")
        return urls

    def discover_via_bfs(self, max_pages: int = 500) -> set[str]:
        visited = set()
        queue = [self.base_url]
        urls = set([self.base_url])
        
        while queue and len(visited) < max_pages:
            current_url = queue.pop(0)
            if current_url in visited:
                continue
                
            visited.add(current_url)
            logger.info(f"BFS discovery: Visiting page {len(visited)} - {current_url}")
            try:
                response = self.page.goto(current_url, wait_until="domcontentloaded")
                if not response or response.status >= 400:
                    continue
                
                # Wait for potential JS rendering
                self.page.wait_for_timeout(1000)
                
                soup = BeautifulSoup(self.page.content(), "html.parser")
                for a_tag in soup.find_all("a", href=True):
                    href = a_tag["href"]
                    # Resolve relative URLs
                    full_url = urljoin(current_url, href)
                    normalized = self._normalize_url(full_url)
                    
                    if self._is_valid_url(normalized) and normalized not in urls:
                        urls.add(normalized)
                        queue.append(normalized)
            except Exception as e:
                logger.warning(f"Error fetching {current_url} during BFS: {e}")
                
        logger.info(f"Discovered {len(urls)} URLs via BFS.")
        return urls

    def discover(self) -> list[str]:
        urls = self.discover_via_sitemap()
        if not urls:
            urls = self.discover_via_bfs()
        return list(urls)
