import re
import urllib.parse
import urllib.request
import time


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
    m = re.search(
        r'(https?://[^"\'<>\s]*streamtape[^"\'<>\s]*/get_video\?[^"\'<>\s]+)',
        html,
        re.IGNORECASE,
    )
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


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def http_error_302(self, req, fp, code, msg, headers):
        return fp


def extract(url):
    # Retry fetching the embed page if necessary
    max_retries = 3
    retry_delay = 5

    html = ""
    final_embed = url

    for attempt in range(max_retries):
        try:
            html, final_embed = _fetch(url)
            # Basic check if we got a valid page or just a loading screen
            if "get_video" in html:
                break
            time.sleep(retry_delay)
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_delay)

    path = _find_get_video_path(html)
    if not path:
        raise RuntimeError("Streamtape get_video path not found")

    # Clean up path if it contains the domain but is treated as relative
    if "get_video" in path:
        # Find where get_video starts
        idx = path.find("get_video")
        # Check if there is a slash before it, if so take it
        if idx > 0 and path[idx - 1] == "/":
            path = path[idx - 1 :]
        else:
            path = "/" + path[idx:]

    get_url = _absolute(path, final_embed)

    # Verify it looks correct
    if "get_video" not in get_url:
        raise RuntimeError(f"Constructed invalid URL: {get_url}")

    # Now we need to follow the redirect from get_video URL to the actual mp4 file.
    # Streamtape sometimes uses a 302 redirect, sometimes serves a page with meta refresh?
    # Usually it's a 302/301 redirect.
    # HOWEVER, urllib.request follows redirects automatically.
    # If it returns the same URL, it means:
    # 1. No redirect happened (maybe 200 OK with content, e.g. "link expired" or "wait").
    # 2. Redirect loop?

    # We will try to handle the redirect manually to inspect what happens if auto fails

    req = urllib.request.Request(get_url)
    req.add_header("User-Agent", "Mozilla/5.0")
    req.add_header("Accept-Language", "en-US,en;q=0.9")
    req.add_header("Referer", final_embed)

    # We expect a redirect to the final video file
    # We use a loop to follow redirects until we get a video file (ending in mp4 usually)
    # or stop getting redirects.

    # Streamtape get_video link is supposed to redirect to the video file.
    # If it returns 200 OK without redirect, it might be an error page or "wait" page.

    try:
        # Check if we get a redirect
        # We allow up to 5 retries for the redirect itself, because sometimes Streamtape
        # returns 200 OK with "We are preparing your video" page instead of redirect immediately.

        for i in range(3):
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler)
            with opener.open(req) as resp:
                final_url = resp.geturl()

                # If the URL is still the get_video URL, it failed to redirect properly
                if "tapecontent.net" not in final_url:
                    # Check content
                    content = resp.read(2048).decode("utf-8", errors="ignore")

                    if "expired" in content.lower():
                        raise RuntimeError("Streamtape link expired")

                    # If it's just not ready, wait and retry
                    # print(f"Redirect not ready (attempt {i+1}). Waiting...")
                    time.sleep(5)
                    continue

                return final_url

        # If we exhausted retries and still have get_video url
        return final_url

    except Exception as e:
        raise RuntimeError(f"Failed to resolve Streamtape video URL: {e}")
