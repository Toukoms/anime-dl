# VoirAnime Downloader Documentation

This tool scrapes anime episodes from VoirAnime and downloads them from Streamtape.

## Features

- **Sequential Download**: Automatically downloads all episodes starting from a chosen episode.
- **Custom Naming**: Asks for the series name to generate clean filenames (e.g., `One Piece - Episode 01.mp4`).
- **Resumable Downloads**:
  - Uses HTTP `Range` headers to resume interrupted downloads.
  - Verifies file integrity using `Content-Length`.
  - Handles `416 Range Not Satisfiable` responses gracefully.
- **Robustness**:
  - Retries on connection failures.
  - Sanitizes filenames to be filesystem-safe.
- **Streamtape Support**: Extracts direct video links from Streamtape by solving obfuscation.

## How it Works

The extraction process involves several steps to bypass protections and get the direct video file.

### 1. VoirAnime Extraction (`src/extractors/voiranime.py`)

- **Main Page**:
  - Fetches the anime overview page.
  - Parses all links to find episode URLs (matching the anime URL pattern).
  - Sorts episodes by number.
- **Episode Page**:
  - Fetches the episode page.
  - Looks for the Streamtape player iframe.
  - **Target**: The `<iframe>` inside `#chapter-video-frame`.

### 2. Streamtape Extraction (`src/extractors/streamtape.py`)

- The script fetches the Streamtape embed page found in the previous step.
- **Obfuscation**: Streamtape hides the video token in a script tag that modifies the DOM.
- **Technique**:
  - Uses Regex to find the obfuscation pattern:  
    `document.getElementById('botlink').innerHTML = 'PREFIX' + ('TOKEN_STRING').substring(OFFSET)`
  - Reconstructs the full URL by combining the prefix and the substring of the token.
  - Appends `&stream=1` to the URL.
- **Redirect**:
  - Performs a HEAD/GET request to the constructed URL (allowing redirects).
  - The final destination (often `tapecontent.net`) is the direct `.mp4` link.

### 3. Downloading (`src/utils.py`)

- **Smart Download**:
  - Checks if the file already exists and matches the remote size (skips if complete).
  - If partial file exists, sends `Range: bytes=EXISTING_SIZE-` header to resume.
- **Progress**: Displays a text-based progress bar with percentage and size downloaded.

## Usage

### Installation

1. **Install the package**:
   Run this command in the project root:

   ```bash
   pip install .
   ```

   Or for development (editable mode):

   ```bash
   pip install -e .
   ```

2. **Run the CLI**:
   The tool is installed as a global command `vadl`.

   ```bash
   vadl "URL_TO_ANIME_PAGE"
   ```

   **Examples**:

   _Download all episodes from a series:_

   ```bash
   vadl "https://voiranime.com/anime/one-piece/"
   ```

   _Download a specific single episode:_

   ```bash
   vadl "https://v6.voiranime.com/anime/one-piece/one-piece-1000-vostfr/"
   ```

3. **CLI Arguments**:
   - `url`: The URL to the VoirAnime anime page or specific episode.
   - `-o`, `--output`: (Optional) Output directory. Defaults to a folder named after the series.
   - `-s`, `--start`: (Optional) Start downloading from this episode number (only for main page URLs).

4. **Interactive Prompts**:
   - If not provided via arguments, the script may ask for:
     - **Series Name**: For naming files.
     - **Start Episode**: To skip early episodes.
