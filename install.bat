@echo off
echo ==========================================
echo      Installing Anime-DL (vadl)
echo ==========================================
echo.

:: Find python command
set PYTHON_CMD=
set PIP_CMD=

:: Check python3 first
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python3
    set PIP_CMD=pip3
    goto :found_python
)

:: Then check python
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    set PIP_CMD=pip
    goto :found_python
)

:: Neither found
echo Error: Python 3 is not found!
echo Please install Python from https://www.python.org/
echo and make sure to check "Add Python to PATH" during installation.
echo.
echo Checked: 'python3' and 'python'
pause
exit /b 1

:found_python

:: Check Python version >= 3.10
for /f "tokens=2 delims= " %%a in ('%PYTHON_CMD% --version 2^>^&1') do set PYTHON_VERSION=%%a
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set MAJOR=%%a
    set MINOR=%%b
)

if %MAJOR% lss 3 (
    echo Error: Python 3.10+ is required. Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

if %MAJOR% equ 3 if %MINOR% lss 10 (
    echo Error: Python 3.10+ is required. Current version: %PYTHON_VERSION%
    pause
    exit /b 1
)

echo Python %PYTHON_VERSION% detected ✓ (using '%PYTHON_CMD%')
echo.

:: Install the package in editable mode
echo Installing dependencies and package...
%PIP_CMD% install -e .

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Installation failed with '%PIP_CMD%'.
    echo Retrying with '%PYTHON_CMD% -m pip'...
    %PYTHON_CMD% -m pip install -e .
    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] Installation failed.
        echo Please check the error messages above.
        pause
        exit /b 1
    )
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
    echo    %PYTHON_CMD% src\cli.py "URL"
    echo.
) else (
    echo Success! You can now run 'vadl' from anywhere.
    echo.
    echo Example:
    echo    vadl "https://voiranime.com/anime/one-piece/"
)

echo.
pause
