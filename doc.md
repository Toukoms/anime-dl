# VoirAnime Downloader Documentation

This tool scrapes anime episodes from VoirAnime and downloads them from Streamtape.

## Features
- **Sequential Download**: Automatically downloads all episodes starting from a chosen episode.
- **Custom Naming**: Asks for the series name to generate clean filenames (e.g., `One Piece - Episode 01.mp4`).
- **Resumable**: Skips already downloaded files (implementation dependent, basic check exists).
- **Streamtape Support**: Extracts direct video links from Streamtape.

## How it Works

The extraction process involves several steps to bypass protections and get the direct video file.

### 1. VoirAnime Extraction
- The script fetches the VoirAnime episode page.
- It looks for the Streamtape iframe.
- **Technique**: It targets the `<iframe>` inside the element with `id="chapter-video-frame"`.
- This provides the `embed` URL for Streamtape.

### 2. Streamtape Extraction
- The script fetches the Streamtape embed page.
- It needs to find the token/redirect URL to the actual video file.
- **Technique**: It looks for an element with `id="botlink"`.
  - This element (often a `div` or `span`) contains the redirect URL, sometimes hidden in text or an `href`.
  - Example: `//streamtape.com/get_video?id=...&token=...`
- The script constructs the full URL and follows the redirect.
- Streamtape redirects this link to the final `tapecontent.net` (or similar) URL which serves the `.mp4` file.

### 3. Downloading
- The script uses the `requests` library to stream the video content.
- It saves the file with the format: `{Series Name} - Episode {Number}.mp4`.

## Usage

1. **Install Dependencies**:
   ```bash
   pip install requests beautifulsoup4
   ```

2. **Run the Script**:
   ```bash
   python main.py "URL_TO_ANIME_PAGE"
   ```
   Example:
   ```bash
   python main.py "https://voiranime.com/anime/one-piece/"
   ```

3. **Follow Prompts**:
   - Enter the **Series Name** (e.g., "One Piece").
   - Enter the **Start Episode** number (defaults to the first available).

The script will create a folder named after the series and download episodes into it.
