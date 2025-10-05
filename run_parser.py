from __future__ import annotations

import argparse
import asyncio
import logging
from typing import List, Tuple

from app.database.db_channel import ChannelManager
from app.database.db_helper import DatabaseManager
from app.misc.log_helper import LogHelper
from app.pipelines.pipes.parser.parser_pipeline import Parser

LOGGER = LogHelper("run_parser", "Runner")

SAMPLE_CHANNELS: List[Tuple[str, str]] = [
    ("BBC World", "http://feeds.bbci.co.uk/news/world/rss.xml"),
    ("Reuters Top", "http://feeds.reuters.com/reuters/topNews"),
    ("Hacker News", "https://hnrss.org/frontpage"),
]


def bootstrap_channels() -> None:
    if ChannelManager.get_channels_by_type(1):
        LOGGER.log(logging.INFO, "Channels already exist; skipping bootstrap")
        return

    for title, url in SAMPLE_CHANNELS:
        ChannelManager.add_channel(title, url, channel_type=1)
        LOGGER.log(logging.INFO, "Added sample channel %s", title)


async def run_pipeline() -> None:
    parser_pipeline = Parser()
    await parser_pipeline.run_async()


def list_channels() -> None:
    rows = ChannelManager.list_channels()
    if not rows:
        print("No channels configured. Use --bootstrap or --add-channel to add one.")
        return
    for channel in rows:
        print(f"[{channel.channel_id}] ({channel.channel_type}) {channel.title}: {channel.url}")


def add_channel(args: argparse.Namespace) -> None:
    channel_id = ChannelManager.add_channel(args.title, args.url, channel_type=args.channel_type)
    LOGGER.log(logging.INFO, "Channel '%s' stored with id %s", args.title, channel_id)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pulser news aggregation service")
    parser.add_argument("--bootstrap", action="store_true", help="Insert a set of sample RSS channels")
    parser.add_argument("--list", action="store_true", dest="list_channels", help="List configured channels")
    parser.add_argument("--add-channel", dest="add_channel", action="store_true", help="Add a channel")
    parser.add_argument("--title", type=str, help="Channel title")
    parser.add_argument("--url", type=str, help="Channel URL")
    parser.add_argument(
        "--channel-type", type=int, default=1, help="Channel type (1 = RSS, 3 = Telegram, etc.)"
    )
    parser.add_argument("--run", action="store_true", help="Run the parser pipeline once")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    DatabaseManager.initialize()

    if args.bootstrap:
        bootstrap_channels()

    if args.list_channels:
        list_channels()

    if args.add_channel:
        if not args.title or not args.url:
            raise SystemExit("--add-channel requires --title and --url")
        add_channel(args)

    if args.run or (not args.list_channels and not args.add_channel and not args.bootstrap):
        asyncio.run(run_pipeline())


if __name__ == "__main__":
    main()
