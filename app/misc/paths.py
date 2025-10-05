from __future__ import annotations

from pathlib import Path


class Paths:
    ROOT_DIR: Path = Path(__file__).resolve().parents[2]
    DATA_DIR: Path = ROOT_DIR / "data"

    @classmethod
    def ensure_directories(cls) -> None:
        cls.DATA_DIR.mkdir(parents=True, exist_ok=True)


__all__ = ["Paths"]
