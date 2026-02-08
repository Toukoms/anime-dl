import asyncio
import logging
from typing import List, Optional

from core.base import BaseEpisode, Platform, VideoPlayer
from core.downloader import SmartDownloader
from core.config import SupportedPlayers
from extractors.platforms.voiranime import VoirAnimePlatform
from extractors.players.streamtape import StreamtapePlayer
from rich.console import Console

logger = logging.getLogger(__name__)
_console = Console()


class Orchestrator:
    def __init__(
        self,
        output_dir: str,
        max_concurrent: int = 3,
        player_code: str = SupportedPlayers.STREAMTAPE,
    ):
        self.output_dir = output_dir
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.player_code = player_code

        # Registry of available platforms and players
        self.platform: Platform = VoirAnimePlatform(preferred_player=player_code)

        # Load available players
        # Ideally this should be dynamic, but for now we register manually
        self.players: List[VideoPlayer] = []

        # Register Streamtape player
        if player_code == SupportedPlayers.STREAMTAPE:
            self.players.append(StreamtapePlayer())
        # Add other players here if selected

        if not self.players:
            logger.warning(f"No player implementation found for code: {player_code}")

    async def get_series_episodes(self, url: str) -> List[BaseEpisode]:
        """
        Fetches episodes from the configured platform.
        """
        return await self.platform.get_episodes(url)

    async def download_episode(self, episode: BaseEpisode, progress=None) -> bool:
        """
        Orchestrates the download of a single episode.
        """
        current_console = progress.console if progress else _console
        async with self.semaphore:
            try:
                # 1. Get player URL
                status = current_console.status(
                    f"[bold]Fetching player URL for {episode.name}...[/]"
                )
                status.start()
                player_url = await episode.get_player_url()
                if not player_url:
                    logger.error(f"Could not find player URL for {episode.name}")
                    status.stop()
                    return False

                status.update(f"[bold]Extracting direct URL for {episode.name}...[/]")
                # 2. Find compatible player and extract direct URL
                direct_url = await self._extract_direct_url(player_url)
                if not direct_url:
                    logger.error(
                        f"Could not extract direct URL for {episode.name} from {player_url}"
                    )
                    status.stop()
                    return False
                status.stop()

                # 3. Download
                downloader = SmartDownloader(self.output_dir)
                path, skipped = await downloader.download(
                    direct_url, episode.number, progress
                )

                if skipped:
                    if progress:
                        progress.console.print(
                            f"[yellow]⚠[/] {episode.name} already exists."
                        )
                    else:
                        logger.info(f"Skipped {episode.name} (already exists): {path}")
                else:
                    if progress:
                        progress.console.print(f"[green]✔[/] {episode.name} finished.")
                    else:
                        logger.info(f"Downloaded {episode.name}: {path}")

                return True

            except Exception as e:
                logger.error(f"Failed to download {episode.name}: {e}", exc_info=True)
                return False

    async def _extract_direct_url(self, player_url: str) -> Optional[str]:
        """
        Iterates through registered players to find one that can handle the URL.
        """
        for player in self.players:
            # We check if the player name matches the preference or if it can handle the URL
            # For now, simple check based on URL content vs player type
            if (
                isinstance(player, StreamtapePlayer)
                and "streamtape" in player_url.lower()
            ):
                return await player.extract_direct_url(player_url)
            # Future players logic

        logger.warning(
            f"No suitable player found for URL: {player_url} (Configured player: {self.player_code})"
        )
        return None
