# Refactor and Batch Download Implementation Plan

## 1. Project Restructuring
- Create `utils.py` to house shared utilities (generic file downloader, input helpers).
- Clean up `main.py` to focus on orchestration and CLI interaction.

## 2. Enhance `extractors/voiranime.py`
- Implement `get_anime_episodes(url)`:
  - Fetch the anime main page.
  - Parse all episode links using regex (handling the descending order).
  - Sort episodes numerically to ensure correct order (Episode 1 to Last).
  - Return a list of tuples: `[(1, "url1"), (2, "url2"), ...]`.

## 3. Implement Parallel Downloading in `main.py`
- Update `main` to detect if the input URL is a **Main Anime Page** or a **Single Episode**.
- **For Main Anime Page**:
  - Call `get_anime_episodes` and display the range (e.g., "Found Episodes 1 to 293").
  - Prompt user: `Start download from episode [1]:`.
  - Filter the episode list based on user input.
  - Use `concurrent.futures.ThreadPoolExecutor` with `max_workers=3` to process the batch.
  - Each worker will:
    1. Extract Streamtape URL from the episode page.
    2. Resolve the final video URL.
    3. Download the file to the output directory.

## 4. CLI Arguments & Output Management
- Re-introduce `argparse` for cleaner argument handling:
  - `url`: The input URL.
  - `-o/--output`: Output directory.
  - `-s/--start`: (Optional) Auto-start from this episode (skips prompt).
- **Folder Logic**:
  - If `-o` is not provided, extract the anime slug from the URL (e.g., `boruto-naruto-next-generations-vf`) and create a folder with that name.
  - Save all downloads inside this folder.
