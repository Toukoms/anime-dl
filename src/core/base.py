from abc import ABC, abstractmethod
from typing import List, Optional


class VideoPlayer(ABC):
    """Abstract base class for video players (e.g., Streamtape)."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def extract_direct_url(self, url: str) -> Optional[str]:
        """Extracts the direct download URL from the player page."""
        pass


class BaseEpisode(ABC):
    """Abstract base class for an anime episode."""

    def __init__(self, number: int, name: str, url: str):
        self.number = number
        self.name = name
        self.url = url

    @abstractmethod
    async def get_player_url(self) -> Optional[str]:
        """Fetches the player URL (e.g. streamtape url) from the episode page."""
        pass


class Platform(ABC):
    """Abstract base class for streaming platforms."""

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    async def get_episodes(self, series_url: str) -> List[BaseEpisode]:
        """Fetches the list of episodes for a series."""
        pass
