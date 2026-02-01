# Anime Downloader (VoirAnime)

A command-line tool to batch download anime episodes from **VoirAnime** via **Streamtape**.

## Features

- **Batch Downloading**: Download entire series or specific ranges of episodes.
- **Smart Resume**: Supports resuming interrupted downloads using `Range` headers.
- **Sequential Processing**: Downloads episodes one by one.
- **Direct Extraction**: Bypasses Streamtape obfuscation to get direct `.mp4` links.

## Installation

### Easy Install

#### Windows

1. Download this project.
2. Double-click **`install.bat`**.
3. It will install the tool and check if everything is set up correctly.

#### macOS / Linux

1. Open a terminal in the project folder.
2. Run the install script:
   ```bash
   bash install.sh
   ```

### Manual Install

This tool requires Python 3.13+ (or compatible newer versions).

1. Clone the repository or download the source code.
2. Open a terminal in this folder and run:

```bash
pip install -e .
```

## Usage

After installation, the `anime-dl` command will be available globally.

### Basic Usage

```bash
anime-dl <URL>
```

### Examples

**1. Download an entire series (or start from a specific episode):**

```bash
anime-dl "https://voiranime.com/anime/one-piece/"
```

- The script will detect all episodes.
- It will ask you which episode to start from (default: first available).
- It will ask for a series name to prefix filenames (e.g., "One Piece").

**2. Download a single episode:**

```bash
anime-dl "https://v6.voiranime.com/anime/one-piece/one-piece-1000-vostfr/"
```

**3. Specify output directory and start episode via CLI:**

```bash
anime-dl "https://voiranime.com/anime/one-piece/" --output "D:\Anime\One Piece" --start 1000
```

### Troubleshooting: "Command not found"

If `anime-dl` works in the installation window but not in a new terminal, you need to add the Python user scripts folder to your PATH.

**Windows**:

1. Search Windows for **"Edit the system environment variables"**.
2. Click **Environment Variables**.
3. Under **User variables**, find **Path** and click **Edit**.
4. Click **New** and add the path (Commonly: `C:\Users\USERNAME\AppData\Roaming\Python\Python313\Scripts`).

**macOS / Linux**:
Add the following line to your `~/.bashrc` or `~/.zshrc`:

```bash
export PATH=$PATH:~/.local/bin
```

Then run `source ~/.bashrc` (or `.zshrc`).

## Project Structure

- `src/cli.py`: Entry point and orchestration logic.
- `src/extractors/`:
  - `voiranime.py`: Scrapes episode links and finds Streamtape iframes.
  - `streamtape.py`: Solves Streamtape obfuscation to extract video links.
- `src/utils.py`: Handles file downloading (resume, progress bar) and filename sanitization.
- `doc.md`: Detailed technical documentation.

## Disclaimer

This tool is for educational purposes only. Please respect copyright laws and the terms of service of the websites involved.
