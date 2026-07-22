from bs4 import BeautifulSoup

class Extractor:
    def __init__(self):
        # Tags that typically contain the main content
        self.main_content_tags = ["main", "article"]
        # Elements to strip out because they are noise
        self.noise_tags = ["nav", "footer", "script", "style", "noscript", "aside", "header", "form", "iframe", "svg", "button"]
        self.noise_classes_ids = ["sidebar", "cookie", "banner", "ad", "comments", "menu", "navigation", "toc", "footer"]

    def extract_main_content(self, html: str) -> str:
        if not html:
            return ""

        soup = BeautifulSoup(html, "html.parser")
        
        # 1. Try to find the primary content container
        main_content = None
        for tag in self.main_content_tags:
            main_content = soup.find(tag)
            if main_content:
                break
        
        # 1b. Try finding role="main"
        if not main_content:
            main_content = soup.find(attrs={"role": "main"})
            
        # 1c. Fallback to body
        if not main_content:
            main_content = soup.find("body")
            
        # 1d. Fallback to whole document if no body
        if not main_content:
            main_content = soup

        # 2. Clean up noise
        for tag_name in self.noise_tags:
            for el in main_content.find_all(tag_name):
                el.decompose()

        # 3. Clean up by classes/ids heuristically
        for element in main_content.find_all(True):
            if element.attrs is None:
                continue
            
            cls = element.get('class', [])
            id_val = element.get('id', '')
            
            # Convert list of classes to a single string for easy checking
            cls_str = " ".join(cls).lower()
            id_str = str(id_val).lower()
            
            for noise_word in self.noise_classes_ids:
                if noise_word in cls_str or noise_word in id_str:
                    element.decompose()
                    break

        return str(main_content)
