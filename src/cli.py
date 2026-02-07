import sys
import argparse
import logging
import asyncio
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)

from utils import sanitize_filename
from core.orchestrator import Orchestrator
from core.config import SupportedPlayers
from extractors.platforms.voiranime import VoirAnimeEpisode


class AnimeDL:
    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger(__name__)

    def _setup_logging(self, debug_mode):
        level = logging.DEBUG if debug_mode else logging.INFO
        logging.basicConfig(
            level=level,
            format="%(message)s",
            datefmt="[%X]",
            handlers=[RichHandler(console=self.console, rich_tracebacks=True)],
        )

    def _get_output_dir(self, args_output, series_name):
        if args_output:
            return args_output
        return sanitize_filename(series_name)

    def _resolve_start_episode(self, first_ep, args_start):
        if args_start is not None:
            return args_start

        try:
            val = Prompt.ask(
                "Start download from episode",
                default=str(first_ep),
                console=self.console,
            )
            return int(val)
        except ValueError:
            self.console.print("[yellow]Invalid number. Starting from first.[/]")
            return first_ep

    async def _handle_series(self, url, args):
        # Initialize Orchestrator with temporary output dir (will be updated)
        # We need to fetch episodes first to know the series name or just use URL
        orchestrator = Orchestrator(
            output_dir=".", max_concurrent=args.process, player_code=args.player
        )

        episodes = await orchestrator.get_series_episodes(url)
        if not episodes:
            self.console.print("[red]No episodes found.[/]")
            return

        first, last = episodes[0].number, episodes[-1].number
        self.console.print(
            f"Found {len(episodes)} episodes (First: {first}, Last: {last})"
        )

        start_ep = self._resolve_start_episode(first, args.start)
        to_download = [ep for ep in episodes if ep.number >= start_ep]

        series_name = args.output or url.rstrip("/").split("/")[-1] or "Anime"
        output_dir = self._get_output_dir(args.output, series_name)

        # Update orchestrator output dir
        orchestrator.output_dir = output_dir

        self.console.print(
            f"[bold]Queued {len(to_download)} episodes (Player: {args.player}).[/]"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        ) as progress:
            tasks = [orchestrator.download_episode(ep, progress) for ep in to_download]
            await asyncio.gather(*tasks)

    async def _handle_single_episode(self, url, args):
        self.console.print("[bold]Detected single episode.[/]")
        ep_num = 0
        try:
            parts = url.rstrip("/").split("-")
            for p in reversed(parts):
                if p.isdigit():
                    ep_num = int(p)
                    break
        except ValueError:
            pass

        # We construct the URL with the correct host based on player preference
        full_url = url
        host_param = ""
        if args.player == SupportedPlayers.STREAMTAPE:
            host_param = "host=LECTEUR%20Stape"

        if host_param:
            separator = "&" if "?" in url else "?"
            full_url = f"{url}{separator}{host_param}"

        episode = VoirAnimeEpisode(
            number=ep_num,
            name=f"Episode {ep_num}",
            url=full_url,
            player_code=args.player,
        )

        orchestrator = Orchestrator(
            output_dir=args.output or ".", max_concurrent=1, player_code=args.player
        )

        # We need a progress context even for single download to show bars
        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        ) as progress:
            await orchestrator.download_episode(episode, progress)

    async def run(self):
        parser = argparse.ArgumentParser(
            prog="anime-dl", description="VoirAnime Downloader CLI"
        )
        parser.add_argument("url", help="URL to anime page")
        parser.add_argument("-o", "--output", help="Output directory")
        parser.add_argument("-s", "--start", type=int, help="Start episode")
        parser.add_argument(
            "-p",
            "--process",
            type=int,
            default=3,
            help="Number of simultaneous downloads",
        )
        parser.add_argument(
            "--player",
            type=str,
            default=SupportedPlayers.STREAMTAPE.value,
            choices=[p.value for p in SupportedPlayers],
            help="Video player to use (default: streamtape)",
        )
        parser.add_argument(
            "--debug",
            action="store_true",
            help="Enable debug logs",
        )

        args = parser.parse_args()
        self._setup_logging(args.debug)

        try:
            try:
                await self._handle_series(args.url, args)
            except Exception as e:
                self.logger.debug(f"Not a series page: {e}")
                await self._handle_single_episode(args.url, args)
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.console.print("\n[red]Cancelled by user.[/]")
