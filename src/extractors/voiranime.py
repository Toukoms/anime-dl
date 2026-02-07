import httpx
from bs4 import BeautifulSoup


async def _fetch(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/91.0.4472.124 Safari/537.36"
    }
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.text


def _extract_episode_number(url):
    clean_url = url.rstrip("/")
    parts = clean_url.split("-")
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    return None


def _format_streamtape_url(url):
    if "?" in url:
        return url + "&host=LECTEUR%20Stape"
    return url + "?host=LECTEUR%20Stape"


async def get_anime_episodes(anime_url):
    """
    Parses an anime main page and returns a list of (episode_number, url).
    List is sorted by episode number.
    """
    html = await _fetch(anime_url)
    soup = BeautifulSoup(html, "html.parser")

    if anime_url.endswith("/"):
        anime_url = anime_url[:-1]

    episodes = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        url = a["href"]
        if not url.startswith(anime_url) or url in seen_urls:
            continue

        num = _extract_episode_number(url)
        if num is not None:
            full_url = _format_streamtape_url(url)
            episodes.append((num, full_url))
            seen_urls.add(url)

    episodes.sort(key=lambda x: x[0])
    return episodes


async def get_streamtape_url(url):
    html = await _fetch(url)
    soup = BeautifulSoup(html, "html.parser")

    container = soup.find(id="chapter-video-frame")
    if container:
        iframe = container.find("iframe")
        if iframe and iframe.get("src"):
            return iframe["src"]

    iframe = soup.select_one("iframe")
    if iframe and "streamtape" in iframe.get("src", ""):
        return iframe["src"]

    raise ValueError("Could not find Streamtape iframe")
