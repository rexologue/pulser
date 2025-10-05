from __future__ import annotations

from typing import List, Tuple
import urllib.parse
import urllib.request

import requests
from bs4 import BeautifulSoup

from app.misc.log_helper import LogHelper

_LOGGER = LogHelper(__name__, "WebParser").logger
_USER_AGENT = "Mozilla/5.0 (compatible; PulserBot/1.0; +https://example.com/bot)"


class AbstractCommonWeb:
    __url = ""

    def __init__(self) -> None:
        pass

    @classmethod
    def get_all_links(cls, site: str) -> List[str]:
        headers = {"User-Agent": _USER_AGENT}
        try:
            response = requests.get(site, headers=headers, timeout=10)
        except requests.RequestException as exc:
            _LOGGER.warning("Request failed for %s: %s", site, exc)
            return []

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            links = [a.get("href") for a in soup.find_all("a") if a.get("href")]
            if len(links) < 10:
                return cls._extremely_hard_getter(site)
            return links
        if response.status_code == 401:
            return cls._extremely_hard_getter(site)

        raise RuntimeError(f"Failed to retrieve the webpage. Status code: {response.status_code}")

    @classmethod
    def _extremely_hard_getter(cls, site: str) -> List[str]:
        _LOGGER.warning("Falling back to simplified parser for %s", site)
        try:
            response = requests.get(site, headers={"User-Agent": _USER_AGENT}, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            return [a.get("href") for a in soup.find_all("a", href=True)]
        except requests.RequestException as exc:
            _LOGGER.error("Fallback parser failed for %s: %s", site, exc)
            return []

    @classmethod
    def sites_filter(cls, criteria: int = 0):
        raise RuntimeError(
            f"Instances of the {cls.__name__} class cannot call the method sites_filter directly."
        )

    @staticmethod
    def verify_url(url: str) -> Tuple[bool, str]:
        result = urllib.parse.urlparse(url)
        is_valid = all([result.scheme, result.netloc])
        if not is_valid:
            return False, "URL isn't correct"
        try:
            with urllib.request.urlopen(url) as response:
                if response.status == 200:
                    return True, "URL is correct and accessible"
                return False, "Web page unavailable"
        except Exception as exc:  # pragma: no cover - network defensive
            return False, f"Error when accessing URL: {exc}"


if __name__ == "__main__":
    pass
