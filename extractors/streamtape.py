import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin


def extract(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    session = requests.Session()
    session.headers.update(headers)

    # 1. Fetch the page
    resp = session.get(url)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # 2. Find id="botlink"
    botlink = soup.find(id="botlink")
    if not botlink:
        raise RuntimeError("Streamtape botlink element not found")

    # Extract the URL from the text content of the element (e.g. span or div)
    # User tip: link is in children of the element not in href
    link = botlink.get_text().strip()

    if not link:
        # Fallback: check href if it happens to be an anchor tag
        if botlink.name == "a":
            link = botlink.get("href")
        else:
            a_child = botlink.find("a")
            if a_child:
                link = a_child.get("href")

    if not link:
        raise RuntimeError("Could not extract URL from botlink")

    print(f"- botlink url found: {link}")

    # Handle relative URLs
    if link.startswith("//"):
        link = "https:" + link
    elif link.startswith("/"):
        link = urljoin(url, link)

    # 3. Follow redirect to find tapecontent.net
    print(f"Found intermediate link: {link}")

    # We loop because sometimes there's a 'waiting' page
    max_retries = 5
    for i in range(max_retries):
        try:
            # allow_redirects=True is default for get, but explicit here.
            # stream=True to avoid downloading the video content if we find it.
            r = session.get(link, allow_redirects=True, stream=True)
            final_url = r.url

            if "tapecontent.net" in final_url:
                r.close()
                print(f"- direct link url found: {final_url}")
                return final_url

            # Check if it's the video content even if domain doesn't match exactly (just in case)
            content_type = r.headers.get("Content-Type", "")
            if "video" in content_type:
                r.close()
                print(f"- direct link url found: {final_url}")
                return final_url

            # If it's HTML, it might be the waiting page
            if "text/html" in content_type:
                # We need to read content to check for errors, but don't consume too much
                # Just closing and retrying after wait
                r.close()
                print(f"Waiting for video redirect... (Attempt {i + 1}/{max_retries})")
                time.sleep(3)
                continue

            r.close()

        except Exception as e:
            print(f"Error following redirect: {e}")
            time.sleep(2)

    # If we fall through, return the last link we had, hoping it works
    print(f"- direct link url found: {link}")
    return link
