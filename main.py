import sys
import argparse
import concurrent.futures
import os
import time
from urllib.parse import urlparse

from extractors.streamtape import extract as extract_streamtape
from extractors.voiranime import get_streamtape_url, get_anime_episodes
from utils import download_file, sanitize_filename

def process_episode(episode_data, output_dir):
    """
    Worker function to process a single episode.
    episode_data is (episode_num, url)
    """
    ep_num, url = episode_data
    print(f"[Ep {ep_num}] Processing...")
    
    try:
        # 1. Get Streamtape URL from VoirAnime page
        # Retry logic could be added here
        streamtape_url = get_streamtape_url(url)
        # print(f"[Ep {ep_num}] Found Streamtape: {streamtape_url}")
        
        # 2. Get direct video URL from Streamtape
        direct_url = extract_streamtape(streamtape_url)
        # print(f"[Ep {ep_num}] Found direct link")
        
        # 3. Download
        # Create a nice filename: AnimeName - Episode XX.mp4
        # We can try to guess anime name from output_dir or URL, 
        # but for now let's trust the auto-namer or prepend Episode Num
        
        # To make it cleaner, let's force a filename prefix if we can
        # But download_file handles auto-naming well.
        # Let's just prefix with the episode number to keep order
        
        # We can pass a hint to download_file? No, let's just let it download 
        # and maybe rename later? Or just let it be. 
        # Actually, the user wants "put episodes in a folder".
        # Let's rely on the server's filename but maybe ensure it's in the right folder.
        
        path = download_file(direct_url, output_dir=output_dir)
        if path:
            print(f"[Ep {ep_num}] Downloaded to {path}")
            return True
        else:
            print(f"[Ep {ep_num}] Download failed.")
            return False
            
    except Exception as e:
        print(f"[Ep {ep_num}] Error: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Scrape and download anime from voiranime")
    parser.add_argument("url", help="URL to voiranime anime page or episode page")
    parser.add_argument("-o", "--output", help="Output directory (optional)")
    parser.add_argument("-s", "--start", type=int, help="Start downloading from this episode number")
    
    args = parser.parse_args()
    url = args.url
    
    # Determine if it's a main page or episode page
    # Heuristic: Main page usually ends with /anime/slug/ or /anime/slug (no numbers usually)
    # Episode page usually has ...-NUMBER-vf/
    
    # Actually, we can just try `get_anime_episodes`. If it returns a list > 1, it's a main page.
    # If it returns empty or fails, maybe it's a single episode.
    
    is_main_page = False
    episodes = []
    
    # Try to treat as main page first
    try:
        episodes = get_anime_episodes(url)
        if episodes:
            is_main_page = True
    except Exception:
        # Might be a single episode or invalid URL
        pass
        
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
            # Extract slug from URL
            path = urlparse(url).path.strip("/")
            # usually anime/slug-vf
            parts = path.split("/")
            if len(parts) >= 2 and parts[0] == "anime":
                slug = parts[1]
            else:
                slug = "anime_downloads"
            output_dir = slug
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        else:
            print(f"Saving to: {output_dir}")
            
        # Parallel download in batches of 3
        batch_size = 3
        with concurrent.futures.ThreadPoolExecutor(max_workers=batch_size) as executor:
            # We submit all, but the executor limits concurrency to 3
            # Use list to consume iterator
            futures = {executor.submit(process_episode, ep, output_dir): ep for ep in episodes_to_download}
            
            for future in concurrent.futures.as_completed(futures):
                ep = futures[future]
                try:
                    future.result()
                except Exception as exc:
                    print(f"[Ep {ep[0]}] generated an exception: {exc}")
                    
    else:
        # Assume single episode
        print("Detected single episode URL (or failed to parse main page).")
        process_episode((0, url), args.output)

if __name__ == "__main__":
    main()
