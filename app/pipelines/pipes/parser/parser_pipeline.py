from __future__ import annotations

import asyncio
import csv
import logging
from pathlib import Path
from typing import Iterable, List, Tuple

import aiohttp
import feedparser
from bs4 import BeautifulSoup

from app.database.db_channel import ChannelManager
from app.database.db_helper import DatabaseManager, Post
from app.database.db_llm import DatabaseLlmManager
from app.misc.log_helper import LogHelper
from app.misc.paths import Paths
from app.pipelines.pipeline import Pipeline

LOG_PARSER = LogHelper(__name__, "Parser")


class Parser(Pipeline):
    def __init__(self, pipeline_tag: str = "parser_pipeline") -> None:
        super().__init__(pipeline_tag)

    def main(self, *args, **kwargs):
        asyncio.run(Parser.rss_parser())
        return 0

    async def main_async(self, *args, **kwargs):
        await Parser.rss_parser()
        return 0

    @staticmethod
    async def rss_parser() -> None:
        rss_channels = ChannelManager.get_channels_by_type(1)
        await Parser.__rss_channel_parsing(rss_channels)

    @staticmethod
    async def __rss_channel_parsing(rss_channels: Iterable[Tuple[int, str]]) -> None:
        for channel_id, rss_url in rss_channels:
            try:
                LOG_PARSER.log(logging.INFO, "start parsing channel: %s", rss_url)
                feed = feedparser.parse(rss_url)
                total_entries = len(feed.entries)
            except Exception as exc:  # pragma: no cover - defensive logging
                LOG_PARSER.log(logging.ERROR, "Error processing feed from %s: %s", rss_url, exc)
                continue

            processed_entries = 0
            for entry in feed.entries:
                try:
                    if DatabaseManager.is_exists("posts", "link", entry.link):
                        LOG_PARSER.log(logging.DEBUG, "Post '%s' already processed", getattr(entry, "title", ""))
                        continue

                    description = Parser._extract_description(entry)
                    post_text = f"{getattr(entry, 'title', '')} {description}".strip()
                    rating = await DatabaseLlmManager.llm_rate_post(post_text)

                    new_post = Post(
                        channel_id=channel_id,
                        title=getattr(entry, "title", "Untitled"),
                        content=description,
                        link=entry.link,
                        rating=rating,
                    )
                    new_post.save()

                    if rating >= 4 and new_post.post_id:
                        await DatabaseLlmManager.process_text_with_hashtags(
                            post_text,
                            new_post.post_id,
                            "posts_hashtags",
                        )

                    processed_entries += 1
                    LOG_PARSER.log(
                        logging.INFO,
                        "Parsed posts: %s/%s from %s",
                        processed_entries,
                        total_entries,
                        rss_url,
                    )

                except Exception as exc:  # pragma: no cover - defensive logging
                    LOG_PARSER.log(
                        logging.WARNING,
                        "Error processing post from %s in %s: %s",
                        getattr(entry, "title", "<no title>"),
                        entry.link,
                        exc,
                    )

    @staticmethod
    def _extract_description(entry) -> str:
        if hasattr(entry, "description"):
            return entry.description
        if hasattr(entry, "summary"):
            return entry.summary
        if hasattr(entry, "title"):
            return entry.title
        return ""

    @staticmethod
    async def rss_bridge_parser() -> None:
        csv_file = Paths.ROOT_DIR / "app" / "pipelines" / "pipes" / "parser" / "sites_with_rss_bridges.csv"
        if not csv_file.exists():
            LOG_PARSER.log(logging.WARNING, "RSS bridges file %s not found", csv_file)
            return
        rss_bridges_channels = Parser.__read_all_bridges_from_csv(csv_file)
        await Parser.__rss_channel_parsing(rss_bridges_channels)

    @staticmethod
    def __read_all_bridges_from_csv(file: Path) -> List[Tuple[int, str]]:
        all_bridges: List[Tuple[int, str]] = []
        with file.open(newline="", encoding="utf-8") as csvfile:
            csvreader = csv.reader(csvfile, delimiter=";")
            for row in csvreader:
                try:
                    channel_id = int(row[0])
                    url = row[1]
                    all_bridges.append((channel_id, url))
                except (ValueError, IndexError):
                    LOG_PARSER.log(logging.WARNING, "Invalid row in RSS bridges file: %s", row)
        return all_bridges

    @staticmethod
    async def fetch_full_post_content(url: str) -> str | None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as response:
                    response.raise_for_status()
                    content = await response.text()

            soup = BeautifulSoup(content, "html.parser")
            for unwanted in soup(["script", "style", "header", "footer", "nav", "aside", "form"]):
                unwanted.decompose()

            main_content = soup.find("main") or soup.find("article") or soup.find("div", {"role": "main"})
            content_to_use = main_content if main_content else soup.body

            if not content_to_use:
                LOG_PARSER.log(logging.WARNING, "Content not found when fetching %s", url)
                return None

            clean_text = content_to_use.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in clean_text.splitlines() if line.strip()]

            start_word_count = 6
            filtered_lines: List[str] = []
            while not filtered_lines and start_word_count >= 2:
                filtered_lines = [line for line in lines if len(line.split()) >= start_word_count]
                start_word_count -= 1

            return "\n".join(filtered_lines)

        except aiohttp.ClientError as exc:
            LOG_PARSER.log(logging.ERROR, "HTTP error while fetching from %s: %s", url, exc)
            return None
        except Exception as exc:  # pragma: no cover - network defensive
            LOG_PARSER.log(logging.ERROR, "Error while processing content from %s: %s", url, exc)
            return None


async def main() -> None:
    await Parser.rss_parser()


if __name__ == "__main__":
    asyncio.run(main())
