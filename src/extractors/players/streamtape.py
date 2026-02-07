import re
import httpx
import logging
from typing import Optional
from core.base import VideoPlayer

logger = logging.getLogger(__name__)


class StreamtapePlayer(VideoPlayer):
    @property
    def name(self) -> str:
        return "Streamtape"

    async def extract_direct_url(self, url: str) -> Optional[str]:
        """
        Extracts the direct video URL from a Streamtape URL.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            async with httpx.AsyncClient(headers=headers, timeout=10) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text

                # Regex to capture the obfuscation logic for botlink
                pattern = r"document\.getElementById\('botlink'\)\.innerHTML\s*=\s*['\"](.*?)['\"]\s*\+\s*\(['\"]([^'\"]+)['\"]\)\.substring\(\s*(\d+)\s*\)"

                match = re.search(pattern, html)
                if not match:
                    logger.warning(
                        "Could not find botlink obfuscation pattern in Streamtape page."
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
                r = await client.get(final_url, follow_redirects=False, timeout=10)

                if r.status_code in (301, 302, 303, 307, 308):
                    redirect_url = r.headers.get("Location")
                    logger.debug(f"Direct link found (redirect): {redirect_url}")
                    return redirect_url
                else:
                    logger.debug(f"Direct link found (no redirect): {final_url}")
                    return final_url

        except Exception as e:
            logger.error(f"Error extracting Streamtape URL: {e}", exc_info=True)
            return None
