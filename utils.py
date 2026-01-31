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


def download_file(
    url, output_dir=None, output_filename=None, resume=True, max_retries=3
):
    """
    Downloads a file from a URL using requests with resume capability and retries.

    Args:
        url (str): The direct download URL.
        output_dir (str, optional): Directory to save the file in. Defaults to current dir.
        output_filename (str, optional): Specific filename. If None, tries to detect.
        resume (bool): Whether to resume download if file exists. Defaults to True.
        max_retries (int): Number of retries on connection error. Defaults to 3.

    Returns:
        str: The path to the downloaded file, or None if failed.
    """
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    output_path = None

    # Attempt to resolve output path early if possible
    if output_dir and output_filename:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        output_path = os.path.join(output_dir, output_filename)
    elif output_filename:
        output_path = output_filename

    # Pre-check: Verify if file is already complete using HEAD request
    try:
        # Use allow_redirects=True because some file hosts redirect to the actual file
        with requests.head(
            url, headers=headers, allow_redirects=True, timeout=10
        ) as h_resp:
            if h_resp.status_code == 200:
                total_size_remote = int(h_resp.headers.get("Content-Length", 0))

                # If we didn't have a filename, try to get it now to check existence
                if not output_path:
                    temp_filename = output_filename
                    if not temp_filename:
                        cd = h_resp.headers.get("Content-Disposition")
                        if cd:
                            temp_filename = get_filename_from_cd(cd)

                        if not temp_filename:
                            path = urlparse(h_resp.url).path
                            temp_filename = os.path.basename(path)

                    if temp_filename:
                        temp_filename = sanitize_filename(temp_filename)
                        if output_dir:
                            if not os.path.exists(output_dir):
                                os.makedirs(output_dir)
                            temp_path = os.path.join(output_dir, temp_filename)
                        else:
                            temp_path = temp_filename

                        # Set output_path if we found it
                        output_path = temp_path
                        output_filename = temp_filename

                # Now check if file exists and matches size
                if (
                    output_path
                    and os.path.exists(output_path)
                    and total_size_remote > 0
                ):
                    local_size = os.path.getsize(output_path)
                    if local_size == total_size_remote:
                        print(
                            f"File '{output_filename}' already downloaded ({format_bytes(local_size)}). Skipping."
                        )
                        return output_path
                    elif local_size > total_size_remote:
                        print(
                            f"Warning: Local file '{output_filename}' is larger than remote. Restarting download."
                        )
                        # Force restart
                        resume = False
                        try:
                            os.remove(output_path)
                        except Exception as e:
                            print(f"Error removing existing file: {e}")
                            pass
    except Exception:
        # If HEAD fails, we just proceed to the normal download loop
        pass

    retry_count = 0
    while retry_count <= max_retries:
        try:
            current_headers = headers.copy()
            mode = "wb"
            existing_size = 0

            # Resume logic: Check if we have a partial file
            # Only works if we know the output path beforehand
            if resume and output_path and os.path.exists(output_path):
                existing_size = os.path.getsize(output_path)
                if existing_size > 0:
                    current_headers["Range"] = f"bytes={existing_size}-"
                    mode = "ab"
                    print(f"Resuming download from {format_bytes(existing_size)}...")

            # Stream the download
            with requests.get(
                url, headers=current_headers, stream=True, timeout=30
            ) as resp:
                # Handle 416 Range Not Satisfiable (File likely complete)
                if resp.status_code == 416:
                    content_range = resp.headers.get("Content-Range")
                    if content_range:
                        # Pattern: bytes */12345
                        match = re.search(r"bytes \*/(\d+)", content_range)
                        if match:
                            total_remote = int(match.group(1))
                            if existing_size == total_remote:
                                print(
                                    f"File verified complete via 416 response. ({format_bytes(existing_size)})"
                                )
                                return output_path

                    # If we can't verify, we might need to restart or error out.
                    # But usually 416 means we asked for bytes beyond end.
                    print(
                        "Server returned 416 Range Not Satisfiable. Assuming file might be complete or corrupted."
                    )
                    # Let's try to trust the local file if it's substantial
                    if existing_size > 0:
                        print(f"Keeping existing file {format_bytes(existing_size)}.")
                        return output_path

                resp.raise_for_status()

                # Determine filename if not yet known (first run, or if we didn't send Range)
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

                # Verify if server accepted Range
                if "Range" in current_headers and resp.status_code != 206:
                    print("Server does not support resume or file changed. Restarting.")
                    mode = "wb"
                    existing_size = 0

                if mode == "wb":
                    print(f"Downloading: {output_filename}")

                content_length = int(resp.headers.get("Content-Length", 0))
                total_size = existing_size + content_length

                downloaded = existing_size
                block_size = 1024 * 64  # 64KB buffer

                start_time = time.time()

                with open(output_path, mode) as f:
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

                # Verify size (approximate check)
                if total_size > 0 and downloaded < total_size:
                    print(
                        f"Warning: Download incomplete. Expected {total_size} bytes, got {downloaded} bytes."
                    )
                    raise IOError("Download incomplete")

                print(f"Completed in {time.time() - start_time:.1f}s")
                return output_path

        except Exception as e:
            print(f"\nError downloading {url}: {e}")
            retry_count += 1
            if retry_count <= max_retries:
                print(f"Retrying ({retry_count}/{max_retries}) in 5 seconds...")
                time.sleep(5)
            else:
                print("Max retries reached.")
                # IMPORTANT: Do NOT delete the partial file if resume is enabled
                if not resume and output_path and os.path.exists(output_path):
                    try:
                        os.remove(output_path)
                    except Exception as e:
                        print(f"Error removing existing file: {e}")
                        pass
                return None
    return None
