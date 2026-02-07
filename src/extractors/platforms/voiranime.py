import httpx
import logging
from typing import List, Optional, Set, Tuple
from bs4 import BeautifulSoup
from core.base import Platform, BaseEpisode
from core.config import SupportedPlayers

logger = logging.getLogger(__name__)


class VoirAnimeEpisode(BaseEpisode):
    def __init__(self, number: int, name: str, url: str, player_code: str):
        super().__init__(number, name, url)
        self.player_code = player_code

    async def get_player_url(self) -> Optional[str]:
        """
        Scrapes the VoirAnime episode page to find the iframe URL for the selected player.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with httpx.AsyncClient(
                headers=headers, follow_redirects=True
            ) as client:
                resp = await client.get(self.url)
                resp.raise_for_status()
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")

            # Strategy 1: Look for id="chapter-video-frame"
            # This is usually the main container for the active player (selected by host param)
            container = soup.find(id="chapter-video-frame")
            if container:
                iframe = container.find("iframe")
                if iframe and iframe.get("src"):
                    return iframe["src"]

            # Strategy 2: Fallback based on player code if the main container strategy fails
            # or if the host param didn't work as expected
            if self.player_code == SupportedPlayers.STREAMTAPE:
                iframe = soup.select_one("iframe[src*='streamtape']")
                if iframe:
                    return iframe["src"]

            # Future players fallback
            # elif self.player_code == SupportedPlayers.VIDMOLY:
            #     ...

            logger.warning(
                f"Could not find player iframe for episode {self.number} (player: {self.player_code})"
            )
            return None

        except Exception as e:
            logger.error(
                f"Error extracting player URL for episode {self.number}: {e}",
                exc_info=True,
            )
            return None


class VoirAnimePlatform(Platform):
    def __init__(self, preferred_player: str = SupportedPlayers.STREAMTAPE):
        self.preferred_player = preferred_player

    @property
    def name(self) -> str:
        return "VoirAnime"

    async def get_episodes(self, series_url: str) -> List[BaseEpisode]:
        """
        Parses the VoirAnime series page and returns a list of episodes.
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            async with httpx.AsyncClient(
                headers=headers, follow_redirects=True
            ) as client:
                resp = await client.get(series_url)
                resp.raise_for_status()
                html = resp.text

            soup = BeautifulSoup(html, "html.parser")

            if series_url.endswith("/"):
                series_url = series_url[:-1]

            episodes_data: List[Tuple[int, str]] = []
            seen_urls: Set[str] = set()

            for a in soup.find_all("a", href=True):
                url = a["href"]
                # Basic validation to ensure it belongs to the same series structure
                if not url.startswith(series_url) or url in seen_urls:
                    continue

                num = self._extract_episode_number(url)
                if num is not None:
                    full_url = self._format_url(url)
                    episodes_data.append((num, full_url))
                    seen_urls.add(url)

            episodes_data.sort(key=lambda x: x[0])

            return [
                VoirAnimeEpisode(
                    number=num,
                    name=f"Episode {num}",
                    url=url,
                    player_code=self.preferred_player,
                )
                for num, url in episodes_data
            ]

        except Exception as e:
            logger.error(
                f"Error fetching episodes from {series_url}: {e}", exc_info=True
            )
            return []

    def _extract_episode_number(self, url: str) -> Optional[int]:
        clean_url = url.rstrip("/")
        parts = clean_url.split("-")
        for part in reversed(parts):
            if part.isdigit():
                return int(part)
        return None

    def _format_url(self, url: str) -> str:
        """
        Formats the URL with the correct host parameter for the selected player.
        """
        host_param = ""
        if self.preferred_player == SupportedPlayers.STREAMTAPE:
            host_param = "host=LECTEUR%20Stape"
        # elif self.preferred_player == SupportedPlayers.VIDMOLY:
        #     host_param = "host=..."

        if not host_param:
            return url

        separator = "&" if "?" in url else "?"
        return f"{url}{separator}{host_param}"
