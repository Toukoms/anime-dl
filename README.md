# Anime Downloader (VoirAnime)

A command-line tool to batch download anime episodes from **VoirAnime** via **Streamtape**.

## Why This Project Exists

In my country, internet data is expensive and not always reliable.  
Streaming anime online means waiting loading and paying again and again for the same content.

This tool allows me to:

- Download episodes once
- Watch them offline anytime
- Save bandwidth and money

This project solves a **real personal problem**

<img width="1854" height="962" alt="image" src="https://github.com/user-attachments/assets/55a72e8f-ace4-4250-9f2d-c9b456ccdbd7" />

## Features

- **Batch Downloading**: Download entire series or specific ranges of episodes.
- **Concurrent Processing**: Supports downloading multiple episodes simultaneously (default: 3).
- **Smart Resume**: Supports resuming interrupted downloads using `Range` headers.
- **Modern UI**: Beautiful progress bars and status updates powered by `rich`.
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

After installation, the `vadl` command will be available globally.

### Basic Usage

```bash
vadl <URL>
```

### Examples

**1. Download an entire series (or start from a specific episode):**

```bash
vadl "https://voiranime.com/anime/one-piece/"
```

- The script will detect all episodes.
- It will ask you which episode to start from (default: first available).
- It will use the anime title from the URL for the output directory.

**2. Download with specific concurrency and player:**

```bash
vadl "https://voiranime.com/anime/one-piece/" --process 5 --player streamtape
```

**3. Download a single episode:**

```bash
vadl "https://v6.voiranime.com/anime/one-piece/one-piece-1000-vostfr/"
```

**4. Specify output directory and start episode via CLI:**

```bash
vadl "https://voiranime.com/anime/one-piece/" --output "D:\Anime\One Piece" --start 1000
```

### Troubleshooting: "Command not found"

If `vadl` works in the installation window but not in a new terminal, you need to add the Python user scripts folder to your PATH.

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

- `src/cli.py`: Entry point and CLI orchestration.
- `src/core/`: Core logic including the orchestrator, downloader, and configuration.
- `src/extractors/`:
  - `platforms/`: Site-specific logic (e.g., `voiranime.py`) to fetch episodes.
  - `players/`: Video player logic (e.g., `streamtape.py`) to extract direct links.
- `src/utils.py`: Utility functions for filename sanitization and more.
- `doc.md`: Detailed technical documentation.

## Disclaimer

This tool is for educational purposes only. Please respect copyright laws and the terms of service of the websites involved.
