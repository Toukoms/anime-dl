import re
import urllib.parse
import urllib.request

def _fetch(url, headers=None):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Accept-Language", "en-US,en;q=0.9")
    if headers:
        for k, v in headers.items():
            req.add_header(k, v)
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="ignore"), resp.geturl()

def _absolute(url, base):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme and parsed.netloc:
        return url
    basep = urllib.parse.urlparse(base)
    # Ensure url starts with / if it's not absolute
    if not url.startswith("/"):
        url = "/" + url
    return urllib.parse.urljoin(f"{basep.scheme}://{basep.netloc}", url)

def _find_get_video_path(html):
    # Try to find explicit full URL first
    m = re.search(r'(https?://[^"\'<>\s]*streamtape[^"\'<>\s]*/get_video\?[^"\'<>\s]+)', html, re.IGNORECASE)
    if m:
        return m.group(1)
        
    # Try to find valid path in href or src, avoiding HTML tags
    # We look for get_video inside quotes, but we forbid < > inside the quotes to avoid matching across tags if quotes are unbalanced or missing
    m = re.search(r'["\']([^"\'<>]*?/get_video\?[^"\'<>]+)["\']', html, re.IGNORECASE)
    if m:
        return m.group(1)
        
    # Try to find the token link in div or script (common in streamtape)
    # Exclude <, >, whitespace, quotes
    m = re.search(r'(get_video\?[^"\'<>\s]+)', html, re.IGNORECASE)
    if m:
        return m.group(1)
        
    return None

def extract(url):
    html, final_embed = _fetch(url)
    path = _find_get_video_path(html)
    if not path:
        raise RuntimeError("Streamtape get_video path not found")
    
    # Clean up path if it contains the domain but is treated as relative
    # e.g. /streamtape.com/get_video?... -> /get_video?...
    # Also handle xcdbtape.com/get_video... -> /get_video...
    if "get_video" in path:
        # Find where get_video starts
        idx = path.find("get_video")
        # Check if there is a slash before it, if so take it
        if idx > 0 and path[idx-1] == '/':
            path = path[idx-1:]
        else:
            path = "/" + path[idx:]

    get_url = _absolute(path, final_embed)
    
    # Verify it looks correct
    if "get_video" not in get_url:
        raise RuntimeError(f"Constructed invalid URL: {get_url}")

    req = urllib.request.Request(get_url)
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Accept-Language", "en-US,en;q=0.9")
    req.add_header("Referer", final_embed)
    
    # We expect a redirect to the final video file
    with urllib.request.urlopen(req) as resp:
        return resp.geturl()
