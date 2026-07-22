import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

from playwright.sync_api import Page, Error

class Downloader:
    def __init__(self, page: Page):
        self.page = page

    def download_page(self, url: str) -> Optional[str]:
        try:
            # wait_until='domcontentloaded' waits for the HTML to be loaded and parsed
            response = self.page.goto(url, wait_until="domcontentloaded")
            if not response or response.status >= 400:
                logger.error(f"HTTP error {response.status if response else 'Unknown'} when downloading {url}")
                return None
            
            # Briefly wait for JS framework content to mount/render
            self.page.wait_for_timeout(1500)
            
            return self.page.content()
        except Error as e:
            logger.error(f"Playwright error when downloading {url}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error when downloading {url}: {e}")
        return None
