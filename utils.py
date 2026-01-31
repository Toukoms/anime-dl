import os
import sys
import re
import time
import urllib.request
import urllib.parse

def get_filename_from_cd(cd):
    """
    Get filename from Content-Disposition header.
    """
    if not cd:
        return None
    fname = re.findall('filename=(.+)', cd)
    if len(fname) == 0:
        return None
    return fname[0].strip().strip('"')

def sanitize_filename(name):
    return "".join([c for c in name if c.isalpha() or c.isdigit() or c in "._- "]).strip()

def download_file(url, output_dir=None, output_filename=None):
    """
    Downloads a file from a URL.
    
    Args:
        url (str): The direct download URL.
        output_dir (str, optional): Directory to save the file in. Defaults to current dir.
        output_filename (str, optional): Specific filename. If None, tries to detect.
        
    Returns:
        str: The path to the downloaded file, or None if failed.
    """
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    
    # print(f"Connecting to {url}...")
    try:
        with urllib.request.urlopen(req) as resp:
            # Detect filename if not provided
            if not output_filename:
                cd = resp.getheader("Content-Disposition")
                if cd:
                    output_filename = get_filename_from_cd(cd)
                
            if not output_filename:
                path = urllib.parse.urlparse(resp.geturl()).path
                output_filename = os.path.basename(path)
                if not output_filename or output_filename == "/" or "." not in output_filename:
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

            # print(f"Downloading to: {output_path}")

            total_size = int(resp.getheader("Content-Length", 0))
            downloaded = 0
            block_size = 8192
            
            # Use a unique progress prefix if running in parallel (simplified for now)
            # For parallel downloads, console output might get messy. 
            # We'll just print start/end for now to avoid threading output conflicts.
            
            with open(output_path, "wb") as f:
                while True:
                    buffer = resp.read(block_size)
                    if not buffer:
                        break
                    downloaded += len(buffer)
                    f.write(buffer)
                    
                    # Optional: Print progress only if total size is known and large enough
                    # To avoid spamming console in parallel mode, maybe skipping detailed progress bars
                    # or using a simple logging approach.
                    
            return output_path
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        # Clean up partial file
        if output_path and os.path.exists(output_path):
            try:
                os.remove(output_path)
            except:
                pass
        return None
