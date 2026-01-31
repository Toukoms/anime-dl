import re
import json
import urllib.parse
import urllib.request

def _fetch(url):
    req = urllib.request.Request(url)
    req.add_header("User-Agent", "Mozilla/5.0")
    with urllib.request.urlopen(req) as resp:
        return resp.read().decode("utf-8", errors="ignore")

def get_anime_episodes(anime_url):
    """
    Parses an anime main page and returns a list of (episode_number, url).
    List is sorted by episode number.
    """
    html = _fetch(anime_url)
    
    # Normalize anime URL to ensure no trailing slash for easier matching
    if anime_url.endswith("/"):
        anime_url = anime_url[:-1]
    
    # Find all links that look like episodes
    # Expected pattern: href=".../anime/slug/slug-NUMBER-vf/"
    # We look for links starting with the anime_url
    
    episodes = []
    seen_urls = set()
    
    # Pattern to find links. 
    # We want links that start with the anime_url but have something after it.
    # Usually: anime_url + "/" + ...
    
    # We can be a bit loose: href="(ANIME_URL/[^"]+)"
    # Then we try to extract number from that URL.
    
    base_pattern = re.escape(anime_url)
    # Regex to find hrefs starting with the anime url
    matches = re.finditer(r'href=["\'](' + base_pattern + r'/[^"\']+)["\']', html)
    
    for m in matches:
        url = m.group(1)
        if url in seen_urls:
            continue
            
        # Try to extract episode number
        # Usually the last number in the URL path
        # remove trailing slash
        clean_url = url.rstrip("/")
        parts = clean_url.split("-")
        
        # Look for a number in the last few parts
        num = None
        for part in reversed(parts):
            if part.isdigit():
                num = int(part)
                break
        
        if num is not None:
            # We assume it's a valid episode link if we found a number
            episodes.append((num, url))
            seen_urls.add(url)
            
    # Sort by episode number
    episodes.sort(key=lambda x: x[0])
    
    return episodes

def get_streamtape_url(url):
    html = _fetch(url)
    
    # Extract host parameter
    parsed = urllib.parse.urlparse(url)
    params = urllib.parse.parse_qs(parsed.query)
    host = params.get('host', [None])[0]
    
    if not host:
        # If no host specified, maybe try to find a default one or just fail for now
        # The user specifically asked for the one with ?host=LECTEUR Stape
        # If we are automating, we might want to default to 'LECTEUR Stape' if available
        # Check if we can find it in the source list
        if 'LECTEUR Stape' in html:
             host = 'LECTEUR Stape'
        else:
             # Just try to find ANY streamtape
             pass

    # Find the sources object
    # var thisChapterSources = { ... };
    m = re.search(r'var\s+thisChapterSources\s*=\s*(\{.*?\});', html, re.DOTALL)
    if not m:
        raise ValueError("Could not find thisChapterSources in page")
    
    sources_json_str = m.group(1)
    
    try:
        sources = json.loads(sources_json_str)
    except json.JSONDecodeError:
        # Fallback to regex if json parsing fails (e.g. trailing commas or loose keys)
        # Search for "HOST_NAME":"<iframe src=\"URL\""
        # We need to escape the host name for regex
        if host:
            host_esc = re.escape(host)
            pattern = f'"{host_esc}"\s*:\s*"<iframe[^>]+src=\\\\"([^\\\\"]+)\\\\"'
            m_src = re.search(pattern, sources_json_str)
            if m_src:
                return m_src.group(1).replace('\\/', '/')
        raise ValueError(f"Could not parse sources JSON or find host '{host}'")

    if not host:
        # Try to find Stape or Streamtape
        for k in sources.keys():
            if "Stape" in k or "Streamtape" in k:
                host = k
                break
        if not host:
            raise ValueError(f"No Streamtape host found. Available: {list(sources.keys())}")

    if host not in sources:
        raise ValueError(f"Host '{host}' not found in sources. Available: {list(sources.keys())}")
        
    iframe_html = sources[host]
    # Extract src from iframe
    # <iframe src="https:\/\/streamtape.com\/e\/..." ...>
    # Note: The JSON string has escaped slashes, but json.loads handles that.
    # However, the HTML inside might still be escaped if it was double encoded, 
    # but usually json.loads gives the string: <iframe src="https://streamtape.com/e/..." ...>
    
    m_iframe = re.search(r'src=["\']([^"\']+)["\']', iframe_html)
    if not m_iframe:
        raise ValueError(f"Could not find iframe src for host '{host}'")
        
    embed_url = m_iframe.group(1)
    
    # Check if it is a streamtape url
    if "streamtape.com" not in embed_url:
        # It might be normal if the user selected a non-streamtape host, 
        # but here we expect streamtape.
        # pass it anyway, maybe the caller checks.
        pass
        
    return embed_url
