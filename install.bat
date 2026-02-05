@echo off
echo ==========================================
echo      Installing Anime-DL (vadl)
echo ==========================================
echo.

:: Check if python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not found!
    echo Please install Python from https://www.python.org/
    echo and make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

:: Install the package in editable mode (so updates to code apply immediately)
echo Installing dependencies and package...
pip install -e .

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed.
    echo Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ==========================================
echo        Installation Complete!
echo ==========================================
echo.

:: Check if vadl is recognized
where vadl >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] The 'vadl' command is not yet in your PATH.
    echo.
    echo You likely need to add the Python Scripts folder to your Windows PATH.
    echo Common location: %%APPDATA%%\Python\Python313\Scripts\
    echo.
    echo For now, you can run the tool using this command in this folder:
    echo    python src\cli.py "URL"
    echo.
) else (
    echo Success! You can now run 'vadl' from anywhere.
    echo.
    echo Example:
    echo    vadl "https://voiranime.com/anime/one-piece/"
)

echo.
pause
