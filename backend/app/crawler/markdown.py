from markdownify import markdownify as md

class MarkdownConverter:
    def convert(self, html: str) -> str:
        if not html:
            return ""
        # Convert HTML to markdown, preserving headers, lists, code blocks
        return md(html, heading_style="ATX", code_language="python").strip()
