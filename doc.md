# VoirAnime Downloader Documentation

This tool scrapes anime episodes from VoirAnime and downloads them from Streamtape.

## Features

- **Concurrent Downloads**: Uses `asyncio` and `Semaphore` to download multiple episodes at once (default: 3).
- **Custom Naming**: Automatically generates filenames based on the anime title and episode number.
- **Resumable Downloads**:
  - Uses HTTP `Range` headers to resume interrupted downloads.
  - Verifies file integrity using `Content-Length`.
  - Handles `416 Range Not Satisfiable` responses gracefully.
- **Robustness**:
  - Retries on connection failures (default: 3 retries).
  - Sanitizes filenames to be filesystem-safe.
- **Streamtape Support**: Extracts direct video links from Streamtape by solving obfuscation.
- **Modern UI**: Uses `rich` for progress bars, spinners, and formatted logging.

## How it Works

The tool is built with a modular architecture that separates platform logic (fetching episodes) from player logic (extracting video links).

### 1. Orchestration (`src/core/orchestrator.py`)

The `Orchestrator` is the central brain of the tool. It:
- Manages the concurrency limit using an `asyncio.Semaphore`.
- Coordinates the flow between platforms, players, and the downloader.
- Registers available platforms (like `VoirAnimePlatform`) and players (like `StreamtapePlayer`).

### 2. VoirAnime Extraction (`src/extractors/platforms/voiranime.py`)

- **Main Page**:
  - Fetches the anime overview page.
  - Parses all links to find episode URLs (matching the anime URL pattern).
  - Sorts episodes by number.
- **Episode Page**:
  - Fetches the episode page.
  - Looks for the preferred player (default: Streamtape).
  - **Target**: The `<iframe>` inside `#chapter-video-frame`.

### 3. Streamtape Extraction (`src/extractors/players/streamtape.py`)

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

### 4. Downloading (`src/core/downloader.py`)

- **Smart Downloader**:
  - Checks if the file already exists and matches the remote size (skips if complete).
  - If a partial file exists, sends a `Range: bytes=EXISTING_SIZE-` header to resume.
  - If the existing file is larger than the remote size, it re-downloads from scratch to avoid corruption.
- **Progress**: Displays detailed progress bars for each download using `rich.progress`.
- **Retries**: Implements an exponential backoff-like retry mechanism (default: 3 retries with a 5s delay).

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
   - `-p`, `--process`: (Optional) Number of simultaneous downloads (default: 3).
   - `--player`: (Optional) Video player to use (choices: `streamtape`, default: `streamtape`).
   - `--debug`: (Optional) Enable debug logging.

4. **Interactive Prompts**:
   - If not provided via arguments, the script may ask for:
     - **Series Name**: For naming files.
     - **Start Episode**: To skip early episodes.
