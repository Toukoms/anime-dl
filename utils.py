import os
import sys
import re
import time
import requests
from urllib.parse import urlparse


def get_filename_from_cd(cd):
    """
    Get filename from Content-Disposition header.
    """
    if not cd:
        return None
    fname = re.findall("filename=(.+)", cd)
    if len(fname) == 0:
        return None
    return fname[0].strip().strip('"')


def sanitize_filename(name):
    return "".join(
        [c for c in name if c.isalpha() or c.isdigit() or c in "._- "]
    ).strip()


def format_bytes(size):
    # 2**10 = 1024
    power = 2**10
    n = 0
    power_labels = {0: "", 1: "K", 2: "M", 3: "G", 4: "T"}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"


def download_file(url, output_dir=None, output_filename=None):
    """
    Downloads a file from a URL using requests.

    Args:
        url (str): The direct download URL.
        output_dir (str, optional): Directory to save the file in. Defaults to current dir.
        output_filename (str, optional): Specific filename. If None, tries to detect.

    Returns:
        str: The path to the downloaded file, or None if failed.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    output_path = None

    try:
        # Stream the download
        with requests.get(url, headers=headers, stream=True, timeout=30) as resp:
            resp.raise_for_status()

            # Detect filename if not provided
            if not output_filename:
                cd = resp.headers.get("Content-Disposition")
                if cd:
                    output_filename = get_filename_from_cd(cd)

            if not output_filename:
                path = urlparse(resp.url).path
                output_filename = os.path.basename(path)
                if (
                    not output_filename
                    or output_filename == "/"
                    or "." not in output_filename
                ):
                    output_filename = f"video_{int(time.time())}.mp4"

            output_filename = sanitize_filename(output_filename)
            if not output_filename:
                output_filename = f"video_{int(time.time())}.mp4"

            if output_dir:
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir)
                output_path = os.path.join(output_dir, output_filename)
            else:
                output_path = output_filename

            print(f"Downloading: {output_filename}")

            total_size = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            block_size = 1024 * 64  # 64KB buffer

            start_time = time.time()

            with open(output_path, "wb") as f:
                for chunk in resp.iter_content(chunk_size=block_size):
                    if chunk:
                        downloaded += len(chunk)
                        f.write(chunk)

                        # Progress display
                        if total_size > 0:
                            percent = downloaded * 100 / total_size
                            sys.stdout.write(
                                f"\rProgress: {percent:.1f}% ({format_bytes(downloaded)} / {format_bytes(total_size)})"
                            )
                        else:
                            sys.stdout.write(
                                f"\rDownloaded: {format_bytes(downloaded)}"
                            )
                        sys.stdout.flush()

            print()  # Newline after progress

            # Verify size
            if total_size > 0 and downloaded < total_size:
                print(
                    f"Warning: Download incomplete. Expected {total_size} bytes, got {downloaded} bytes."
                )
                raise IOError("Download incomplete")

            print(f"Completed in {time.time() - start_time:.1f}s")
            return output_path

    except Exception as e:
        print(f"\nError downloading {url}: {e}")
        # Clean up partial file
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:  # noqa: E722
                pass
        return None
