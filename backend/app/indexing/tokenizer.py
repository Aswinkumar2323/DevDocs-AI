import tiktoken

# cl100k_base is the encoding used by:
# - text-embedding-3-small
# - text-embedding-3-large
# - gpt-4, gpt-3.5-turbo
# We load it once at module level (it's fast and thread-safe)
_encoding = tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str) -> int:
    if not text:
        return 0
    return len(_encoding.encode(text))


def validate_chunk_size(text: str, max_tokens: int = 8191) -> bool:
    return count_tokens(text) <= max_tokens


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    if not text:
        return ""
    tokens = _encoding.encode(text)
    if len(tokens) <= max_tokens:
        return text
    return _encoding.decode(tokens[:max_tokens])
