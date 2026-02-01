import sys
import argparse
import os

from extractors.streamtape import extract as extract_streamtape
from extractors.voiranime import get_streamtape_url, get_anime_episodes
from utils import download_file, sanitize_filename


def process_episode(episode_data, output_dir, series_name=None):
    """
    Worker function to process a single episode.
    episode_data is (episode_num, url)
    """
    ep_num, url = episode_data
    print(f"\n[Ep {ep_num}] Processing...")

    try:
        # 1. Get Streamtape URL from VoirAnime page
        streamtape_url = get_streamtape_url(url)

        # 2. Get direct video URL from Streamtape
        direct_url = extract_streamtape(streamtape_url)

        # Construct filename
        filename = None
        if series_name:
            filename = f"{series_name} ep{ep_num:02d}.mp4"
            filename = sanitize_filename(filename)

        # 3. Download
        path = download_file(
            direct_url, output_dir=output_dir, output_filename=filename
        )
        if path:
            print(f"[Ep {ep_num}] Downloaded to {path}")
            return True
        else:
            print(f"[Ep {ep_num}] Download failed.")
            return False

    except KeyboardInterrupt:
        raise
    except Exception as e:
        print(f"[Ep {ep_num}] Error: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Scrape and download anime from voiranime"
    )
    parser.add_argument("url", help="URL to voiranime anime page or episode page")
    parser.add_argument("-o", "--output", help="Output directory (optional)")
    parser.add_argument(
        "-s", "--start", type=int, help="Start downloading from this episode number"
    )

    args = parser.parse_args()
    url = args.url

    try:
        # Determine if it's a main page or episode page
        is_main_page = False
        episodes = []

        try:
            episodes = get_anime_episodes(url)
            if episodes:
                is_main_page = True
        except Exception:
            pass

        parsed_url = ""
        if url.endswith("/"):
            parsed_url = url[:-1]
        else:
            parsed_url = url
        series_name = str(args.output or parsed_url.split("/")[-1])
        if not series_name:
            series_name = "Anime"  # Default fallback

        if is_main_page:
            print(f"Found {len(episodes)} episodes.")
            if not episodes:
                print("No episodes found.")
                return

            first_ep = episodes[0][0]
            last_ep = episodes[-1][0]
            print(f"First Episode: {first_ep}")
            print(f"Last Episode: {last_ep}")

            start_ep = args.start
            if start_ep is None:
                try:
                    val = input(f"Start download from episode [{first_ep}]: ").strip()
                    if val:
                        start_ep = int(val)
                    else:
                        start_ep = first_ep
                except ValueError:
                    print("Invalid number. Starting from first.")
                    start_ep = first_ep

            # Filter episodes
            episodes_to_download = [ep for ep in episodes if ep[0] >= start_ep]
            print(f"Queued {len(episodes_to_download)} episodes for download.")

            # Determine output folder
            output_dir = args.output
            if not output_dir:
                # Use series name as folder if not provided
                output_dir = sanitize_filename(series_name)

            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                print(f"Created output directory: {output_dir}")
            else:
                print(f"Saving to: {output_dir}")

            # Sequential download
            print("Starting sequential download (Press Ctrl+C to stop)...")
            for ep in episodes_to_download:
                process_episode(ep, output_dir, series_name=series_name)

        else:
            # Assume single episode
            print("Detected single episode URL (or failed to parse main page).")
            ep_num = 0
            # Try to guess ep num from url?
            try:
                # voiranime urls often end in -123-vf
                parts = url.rstrip("/").split("-")
                for p in reversed(parts):
                    if p.isdigit():
                        ep_num = int(p)
                        break
            except:  # noqa: E722
                pass
            full_url = url
            if "?" in url:
                full_url += "&host=LECTEUR%20Stape"
            else:
                full_url += "?host=LECTEUR%20Stape"
            process_episode((ep_num, full_url), args.output, series_name=series_name)

    except KeyboardInterrupt:
        print("\n\nDownload cancelled by user.")
        sys.exit(0)


if __name__ == "__main__":
    main()
