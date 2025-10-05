from __future__ import annotations

import re
from typing import List

from app.pipelines.pipes.parser.parser_web.web_abstract import AbstractCommonWeb


class Bloomberg(AbstractCommonWeb):
    __url: str = "https://www.bloomberg.com"
    __topics: List[str] = ["articles", "features"]

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def sites_filter(cls, criteria: int = 0) -> List[str]:
        links: List[str] = []
        topics_pattern = "|".join(cls.__topics)
        pattern = rf"({topics_pattern})/(\d{{4}})-(\d{{2}})-(\d{{2}})"
        for link in cls.get_all_links(cls.__url):
            candidate = link if link.startswith("http") else cls.__url + link
            if cls.verify_url(candidate)[0] and re.search(pattern, candidate):
                links.append(candidate)
        return links


if __name__ == "__main__":
    print(*Bloomberg.sites_filter(), sep="\n")
