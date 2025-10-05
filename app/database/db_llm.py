from __future__ import annotations

import asyncio
import re
from collections import Counter
from typing import List

from app.database.db_helper import DatabaseManager

_STOPWORDS = {
    "the",
    "and",
    "for",
    "that",
    "with",
    "from",
    "this",
    "have",
    "will",
    "about",
    "there",
    "their",
    "would",
    "could",
    "should",
    "while",
    "where",
    "which",
    "these",
    "those",
}


class DatabaseLlmManager:
    @staticmethod
    async def llm_rate_post(text: str) -> int:
        """Return a deterministic rating in the range 1..5."""

        def _score() -> int:
            words = re.findall(r"[\w']+", text.lower())
            if not words:
                return 1
            unique_ratio = len(set(words)) / len(words)
            length_bonus = min(2, len(words) // 120)
            vocab_bonus = 2 if unique_ratio > 0.6 else 1 if unique_ratio > 0.4 else 0
            base = 2 if len(words) > 40 else 1
            score = base + length_bonus + vocab_bonus
            return max(1, min(5, score))

        return await asyncio.to_thread(_score)

    @staticmethod
    async def process_text_with_hashtags(text: str, post_id: int, table_name: str = "posts_hashtags") -> List[str]:
        """Generate and store hashtags for the provided text."""

        def _extract_hashtags() -> List[str]:
            words = [w.lower() for w in re.findall(r"[\w']+", text)]
            filtered = [w for w in words if len(w) > 3 and w not in _STOPWORDS]
            counts = Counter(filtered)
            hashtags = [f"#{word}" for word, _ in counts.most_common(8)]
            return hashtags

        hashtags = await asyncio.to_thread(_extract_hashtags)

        if not hashtags:
            return []

        DatabaseManager.execute(f"DELETE FROM {table_name} WHERE post_id = ?", (post_id,))
        rows = [(post_id, tag) for tag in hashtags]
        DatabaseManager.executemany(
            f"INSERT INTO {table_name}(post_id, hashtag) VALUES(?, ?)",
            rows,
        )
        return hashtags


__all__ = ["DatabaseLlmManager"]
