import os
import time
import requests
import re
from urllib.parse import urlparse
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    DownloadColumn,
    TransferSpeedColumn,
    TimeRemainingColumn,
)
from rich.console import Console

console = Console()


class SmartDownloader:
    def __init__(self, output_dir, max_retries=3):
        self.output_dir = output_dir
        self.max_retries = max_retries
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124"
        }

    def _get_filename(self, response, url, override_name=None):
        if override_name:
            return override_name

        cd = response.headers.get("Content-Disposition")
        if cd:
            fname = re.findall("filename=(.+)", cd)
            if fname:
                return fname[0].strip().strip('"')

        path = urlparse(url).path
        name = os.path.basename(path)
        if not name or "." not in name:
            name = f"video_{int(time.time())}.mp4"
        return name

    def _check_existing(self, path, remote_size):
        if not os.path.exists(path):
            return 0, "wb"

        local_size = os.path.getsize(path)
        if local_size == remote_size:
            return -1, None

        if local_size > remote_size:
            return 0, "wb"

        return local_size, "ab"

    def _perform_download(self, url, path, resume_byte, total_size):
        headers = self.headers.copy()
        if resume_byte > 0:
            headers["Range"] = f"bytes={resume_byte}-"

        mode = "ab" if resume_byte > 0 else "wb"

        with requests.get(url, headers=headers, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(path, mode) as f:
                console.print(f"[blue]Downloading: {os.path.basename(path)}")
                with Progress(
                    SpinnerColumn(),
                    TextColumn("{task.description}"),
                    BarColumn(),
                    DownloadColumn(),
                    TransferSpeedColumn(),
                    TimeRemainingColumn(),
                ) as progress:
                    task = progress.add_task(
                        "[green]Downloading ",
                        total=total_size,
                        completed=resume_byte,
                    )
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

    def download(self, url: str, ep_num: int):
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        filename = f"{self.output_dir} ep{ep_num:02d}.mp4"

        for attempt in range(self.max_retries + 1):
            try:
                with requests.head(
                    url, headers=self.headers, allow_redirects=True
                ) as r:
                    remote_size = int(r.headers.get("Content-Length", 0))
                    final_name = self._get_filename(r, url, filename)
                    output_path = os.path.join(self.output_dir, final_name)

                resume_byte, mode = self._check_existing(output_path, remote_size)
                if resume_byte == -1:
                    return output_path, True

                self._perform_download(url, output_path, resume_byte, remote_size)
                return output_path, False
            except Exception as e:
                if attempt < self.max_retries:
                    print(f"Error: {e}. Retrying in 5s...")
                    time.sleep(5)
                else:
                    print(f"Failed after {self.max_retries} attempts.")
                    raise e
