import re
import requests


def extract(url) -> str:
    """
    Extracts the direct video URL from a Streamtape URL.
    Fetches the page, solves the obfuscation to get the /get_video URL,
    and then follows the redirect to get the final tapecontent.net URL.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        html = response.text

        # Regex to capture the obfuscation logic for botlink
        # Pattern: document.getElementById('botlink').innerHTML = 'PREFIX' + ('TOKEN_STRING').substring(OFFSET);
        # Example: document.getElementById('botlink').innerHTML = '//streamtape.com/get_v'+ ('xyzaideo?id=...').substring(4);

        pattern = r"document\.getElementById\('botlink'\)\.innerHTML\s*=\s*['\"](.*?)['\"]\s*\+\s*\(['\"]([^'\"]+)['\"]\)\.substring\(\s*(\d+)\s*\)"

        match = re.search(pattern, html)
        if not match:
            # Fallback or error
            print(
                "Error: Could not find botlink obfuscation pattern in Streamtape page."
            )
            return None

        prefix = match.group(1)
        token_string = match.group(2)
        offset = int(match.group(3))

        real_token = token_string[offset:]
        full_url_path = prefix + real_token

        # Ensure it starts with https:
        if full_url_path.startswith("//"):
            full_url = "https:" + full_url_path
        elif full_url_path.startswith("/"):
            full_url = "https://streamtape.com" + full_url_path
        else:
            full_url = full_url_path

        # Add &stream=1 to trigger the redirect to the video file
        final_url = full_url + "&stream=1"

        # Follow the redirect to get the actual video URL (tapecontent.net)
        # We use stream=True to avoid downloading the content
        r = requests.get(
            final_url, headers=headers, allow_redirects=False, stream=True, timeout=10
        )

        if r.status_code in (301, 302, 303, 307, 308):
            redirect_url = r.headers.get("Location")
            return redirect_url
        else:
            # If no redirect, maybe the URL is already the direct link or something else
            return final_url

    except Exception as e:
        print(f"Error extracting Streamtape URL: {e}")
        return None
