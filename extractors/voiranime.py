import requests
from bs4 import BeautifulSoup


def _fetch(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    resp = requests.get(url, headers=headers)
    resp.raise_for_status()
    return resp.text


def get_anime_episodes(anime_url):
    """
    Parses an anime main page and returns a list of (episode_number, url).
    List is sorted by episode number.
    """
    html = _fetch(anime_url)
    soup = BeautifulSoup(html, "html.parser")

    # Normalize anime URL to ensure no trailing slash for easier matching
    if anime_url.endswith("/"):
        anime_url = anime_url[:-1]

    episodes = []
    seen_urls = set()

    # Find all links that look like episodes
    for a in soup.find_all("a", href=True):
        url = a["href"]

        # We look for links starting with the anime_url
        if not url.startswith(anime_url):
            continue

        if url in seen_urls:
            continue

        # Try to extract episode number
        # Usually the last number in the URL path
        clean_url = url.rstrip("/")
        parts = clean_url.split("-")

        # Look for a number in the last few parts
        num = None
        for part in reversed(parts):
            if part.isdigit():
                num = int(part)
                break

        if num is not None:
            # Append host parameter to force Streamtape player
            if "?" in url:
                full_url = url + "&host=LECTEUR%20Stape"
            else:
                full_url = url + "?host=LECTEUR%20Stape"

            episodes.append((num, full_url))
            seen_urls.add(url)

    # Sort by episode number
    episodes.sort(key=lambda x: x[0])

    return episodes


def get_streamtape_url(url):
    html = _fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    # User tip: use id="chapter-video-frame" > iframe
    container = soup.find(id="chapter-video-frame")
    if container:
        iframe = container.find("iframe")
        if iframe and iframe.get("src"):
            print(f"- iframe url found: {iframe['src']}")
            return iframe["src"]

    # Fallback: check if direct iframe exists or other common patterns if the ID is wrong
    # But prioritizing the user's specific instruction.
    iframe = soup.select_one("iframe")
    if iframe and "streamtape" in iframe.get("src", ""):
        print(f"- iframe url found: {iframe['src']}")
        return iframe["src"]

    raise ValueError("Could not find Streamtape iframe (checked #chapter-video-frame)")
