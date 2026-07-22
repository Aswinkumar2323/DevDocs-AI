import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Common stop words to ignore when extracting key search tokens
STOP_WORDS = {
    "a", "an", "the", "in", "on", "of", "to", "for", "with", "at", "by", "from",
    "up", "about", "into", "over", "after", "is", "are", "was", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "how", "what",
    "why", "where", "when", "who", "which", "can", "could", "would", "should",
    "my", "your", "it", "its", "this", "that", "these", "those", "and", "or", "but"
}


def _extract_key_tokens(text: str) -> List[str]:
    """Extract lowercase word tokens from text, excluding common stopwords."""
    words = re.findall(r'\w+', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


def _calibrate_score(raw_score: float) -> float:
    """
    Calibrates composite similarity scores into intuitive confidence percentages (0.0 to 1.0).
    Maps high-dimensional embedding/composite scores (~0.35-0.65) to user-friendly (65%-98%) range.
    """
    if raw_score <= 0.20:
        # Low match threshold
        return max(0.05, round(raw_score * 1.5, 4))
    elif raw_score <= 0.40:
        # Moderate match range (maps 0.20-0.40 -> 0.30-0.70)
        calibrated = 0.30 + ((raw_score - 0.20) / 0.20) * 0.40
        return round(calibrated, 4)
    else:
        # High match range (maps 0.40-0.65+ -> 0.70-0.98)
        calibrated = 0.70 + ((raw_score - 0.40) / 0.25) * 0.28
        return round(min(0.985, calibrated), 4)


def rerank(
    results: List[Dict[str, Any]],
    query: str,
    top_n: int = 5,
) -> List[Dict[str, Any]]:
    if not results:
        return []

    # Extract key query tokens (ignoring stopwords)
    key_tokens = _extract_key_tokens(query)
    all_query_words = set(re.findall(r'\w+', query.lower()))

    scored_results = []
    for result in results:
        vector_score = result.get("score", 0.0)
        heading = result.get("heading", "")
        page_title = result.get("page_title", "")
        content = result.get("content", "")

        # 1. Heading & Title Keyword Match Ratio
        heading_text = f"{page_title} {heading}".lower()
        heading_words = set(re.findall(r'\w+', heading_text))
        if key_tokens:
            heading_match_ratio = sum(1 for t in key_tokens if t in heading_words) / len(key_tokens)
        else:
            heading_match_ratio = 0.0

        # 2. Content Body Keyword Density & Overlap
        content_lower = content.lower()
        content_words = set(re.findall(r'\w+', content_lower))
        if key_tokens:
            body_token_overlap = sum(1 for t in key_tokens if t in content_words) / len(key_tokens)
            # Count term frequencies for key tokens
            total_token_occurrences = sum(content_lower.count(t) for t in key_tokens)
            tf_boost = min(0.10, total_token_occurrences * 0.02)
        else:
            body_token_overlap = 0.0
            tf_boost = 0.0

        # 3. Exact Code Identifier / Unique Symbol Bonus
        # Rewards exact matching of technical terms (e.g. useState, useEffect, API names)
        exact_symbol_bonus = 0.0
        for token in key_tokens:
            if len(token) >= 4 and (token in heading_text or token in content_lower):
                exact_symbol_bonus += 0.04
        exact_symbol_bonus = min(0.12, exact_symbol_bonus)

        # 4. Compute Raw Composite Score
        # Weighting: 50% Vector Similarity, 20% Heading Match, 20% Body Overlap, + TF & Symbol Bonuses
        raw_composite = (
            (vector_score * 0.50) +
            (heading_match_ratio * 0.20) +
            (body_token_overlap * 0.20) +
            tf_boost +
            exact_symbol_bonus
        )

        # 5. Apply Score Calibration Curve
        calibrated_score = _calibrate_score(raw_composite)

        scored_results.append({
            **result,
            "score": calibrated_score,
            "raw_vector_score": round(vector_score, 4),
        })

    # Sort by calibrated score descending
    scored_results.sort(key=lambda x: x["score"], reverse=True)

    reranked = scored_results[:top_n]
    logger.info(
        f"Reranked {len(results)} results → top {len(reranked)} "
        f"(scores: {[r['score'] for r in reranked]})"
    )

    return reranked
