import sys
import argparse
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.prompt import Prompt

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

    def _process_episode(self, ep_data, output_dir, debug):
        ep_num, url = ep_data
        status = self.console.status(f"[cyan]Processing Episode {ep_num}[/]")
        try:
            status.start()
            st_url = get_streamtape_url(url)
            direct_url = extract_streamtape(st_url, debug)

            if not direct_url:
                self.console.print(
                    f"[red]Failed to extract direct URL for Episode {ep_num}.[/]"
                )
                raise RuntimeError(f"Direct URL not found for Episode {ep_num}")

            self.console.print(f"[green]Downloadable URL found for Episode {ep_num}")

            status.update("[cyan]Start Downloading...")

            dl = SmartDownloader(output_dir)
            status.stop()
            path, skipped = dl.download(direct_url, ep_num)

            if skipped:
                self.console.print(f"[yellow]Skipped (Exists): {path}[/]")
            else:
                self.console.print(f"[green]Downloaded: {path}[/]")
            return True
        except Exception as e:
            self.logger.error(f"Failed Ep {ep_num}: {e}")
            self.logger.debug(e, exc_info=True)
            return False

    def _handle_series(self, url, args):
        episodes = get_anime_episodes(url)
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
        for ep in to_download:
            self._process_episode(ep, output_dir, debug=args.debug)

    def _handle_single_episode(self, url, args):
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
        series_name = args.output or "Anime"
        self._process_episode((ep_num, full_url), args.output or ".", series_name)

    def run(self):
        parser = argparse.ArgumentParser(description="VoirAnime Downloader CLI")
        parser.add_argument("url", help="URL to anime page")
        parser.add_argument("-o", "--output", help="Output directory")
        parser.add_argument("-s", "--start", type=int, help="Start episode")
        parser.add_argument("--debug", action="store_true", help="Enable debug logs")

        args = parser.parse_args()
        self._setup_logging(args.debug)

        try:
            try:
                self._handle_series(args.url, args)
            except Exception as e:
                self.logger.debug(f"Not a series page: {e}")
                self._handle_single_episode(args.url, args)
        except KeyboardInterrupt:
            self.console.print("\n[red]Cancelled by user.[/]")
            sys.exit(0)
