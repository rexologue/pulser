from __future__ import annotations

from typing import List, Sequence, Tuple

from app.database.db_helper import Channel, DatabaseManager


class ChannelManager:
    @staticmethod
    def get_channels_by_type(channel_type: int) -> List[Tuple[int, str]]:
        rows = DatabaseManager.fetchall(
            "SELECT channel_id, url FROM channels WHERE channel_type = ? ORDER BY channel_id",
            (channel_type,),
        )
        return [(int(row["channel_id"]), row["url"]) for row in rows]

    @staticmethod
    def add_channel(title: str, url: str, channel_type: int = 1) -> int:
        channel = Channel(title=title, url=url, channel_type=channel_type)
        return channel.save()

    @staticmethod
    def list_channels() -> Sequence[Channel]:
        rows = DatabaseManager.fetchall("SELECT channel_id, title, url, channel_type FROM channels ORDER BY channel_id")
        return [
            Channel(
                channel_id=int(row["channel_id"]),
                title=row["title"],
                url=row["url"],
                channel_type=int(row["channel_type"]),
            )
            for row in rows
        ]

    @staticmethod
    def remove_channel(channel_id: int) -> None:
        DatabaseManager.execute("DELETE FROM channels WHERE channel_id = ?", (channel_id,))


__all__ = ["ChannelManager"]
