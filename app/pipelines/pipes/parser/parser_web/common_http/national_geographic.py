from __future__ import annotations

from typing import List

from app.pipelines.pipes.parser.parser_web.web_abstract import AbstractCommonWeb


class NationalGeographic(AbstractCommonWeb):
    __url: str = "https://www.nationalgeographic.com"
    topics = ["animals", "environment", "history", "science", "travel"]
    gen_ = ["premium"]

    def __init__(self) -> None:
        super().__init__()

    @classmethod
    def sites_filter(cls, criteria: int = 0) -> List[str]:
        links: List[str] = []
        for topic in cls.topics:
            for link in cls.get_all_links(f"{cls.__url}/{topic}"):
                candidate = link if link.startswith("http") else cls.__url + link
                if cls.verify_url(candidate)[0]:
                    if f"/{topic}/article/" in candidate:
                        links.append(candidate)
                    else:
                        for item in cls.gen_:
                            if f"/{item}/article/" in candidate:
                                links.append(candidate)
                                break
        return links


if __name__ == "__main__":
    print(*NationalGeographic.sites_filter(), sep="\n")
