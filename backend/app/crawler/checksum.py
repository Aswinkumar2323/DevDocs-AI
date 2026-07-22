import hashlib

class ChecksumGenerator:
    @staticmethod
    def generate(content: str) -> str:
        if not content:
            return ""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
