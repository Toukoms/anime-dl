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

from extractors.streamtape import extract as extract_streamtape
from extractors.voiranime import get_streamtape_url, get_anime_episodes
from utils import sanitize_filename
from core.downloader import SmartDownloader


class AnimeDL:
    def __init__(self):
        self.console = Console()
        self.logger = logging.getLogger("anime-dl")

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

    async def _process_episode(
        self, ep_data, output_dir, debug, progress=None, semaphore=None
    ):
        ep_num, url = ep_data

        if semaphore:
            async with semaphore:
                return await self._do_process_episode(
                    ep_num, url, output_dir, debug, progress
                )
        else:
            return await self._do_process_episode(
                ep_num, url, output_dir, debug, progress
            )

    async def _do_process_episode(self, ep_num, url, output_dir, debug, progress=None):
        try:
            st_url = await get_streamtape_url(url)
            direct_url = await extract_streamtape(st_url, debug)

            if not direct_url:
                self.console.print(
                    f"[red]Failed to extract direct URL for Episode {ep_num}.[/]"
                )
                raise RuntimeError(f"Direct URL not found for Episode {ep_num}")

            dl = SmartDownloader(output_dir)
            path, skipped = await dl.download(direct_url, ep_num, progress)

            if skipped:
                self.console.print(f"[yellow]Skipped (Exists): {path}[/]")
            else:
                self.console.print(f"[green]Downloaded: {path}[/]")
            return True
        except Exception as e:
            self.logger.error(f"Failed Ep {ep_num}: {e}")
            self.logger.debug(e, exc_info=True)
            return False

    async def _handle_series(self, url, args):
        episodes = await get_anime_episodes(url)
        if not episodes:
            self.console.print("[red]No episodes found.[/]")
            return

        first, last = episodes[0][0], episodes[-1][0]
        self.console.print(
            f"Found {len(episodes)} episodes (First: {first}, Last: {last})"
        )

        start_ep = self._resolve_start_episode(first, args.start)
        to_download = [ep for ep in episodes if ep[0] >= start_ep]

        series_name = args.output or url.rstrip("/").split("/")[-1] or "Anime"
        output_dir = self._get_output_dir(args.output, series_name)

        self.console.print(f"[bold]Queued {len(to_download)} episodes.[/]")

        semaphore = asyncio.Semaphore(args.process)

        with Progress(
            SpinnerColumn(),
            TextColumn("{task.description}"),
            BarColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn(),
            console=self.console,
        ) as progress:
            tasks = [
                self._process_episode(ep, output_dir, args.debug, progress, semaphore)
                for ep in to_download
            ]
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

        full_url = url + (
            "&host=LECTEUR%20Stape" if "?" in url else "?host=LECTEUR%20Stape"
        )
        await self._process_episode((ep_num, full_url), args.output or ".", args.debug)

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
            "--debug",
            type=bool,
            default=False,
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
        except KeyboardInterrupt:
            self.console.print("\n[red]Cancelled by user.[/]")
            sys.exit(0)
