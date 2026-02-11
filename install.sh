#!/bin/bash

echo "=========================================="
echo "     Installing Anime-DL (vadl)"
echo "=========================================="
echo ""

# Check for python3
# Find python command
PYTHON_CMD=""
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    # Check that "python" is indeed Python 3
    MAJOR=$(python --version 2>&1 | awk '{print $2}' | cut -d. -f1)
    if [ "$MAJOR" -eq 3 ]; then
        PYTHON_CMD="python"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo Error: Python 3 is not found!
    echo Please install Python from https://www.python.org/
    echo and make sure to add Python to PATH
    exit 1
fi

# Find pip command
PIP_CMD=""
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
elif command -v pip &> /dev/null; then
    PIP_CMD="pip"
elif $PYTHON_CMD -m pip --version &> /dev/null; then
    PIP_CMD="$PYTHON_CMD -m pip"
fi

if [ -z "$PIP_CMD" ]; then
    echo "Error: pip is not found!"
    echo "Please install pip by running:"
    echo "    $PYTHON_CMD -m ensurepip --upgrade"
    echo ""
    echo "Checked: 'pip3', 'pip', and '$PYTHON_CMD -m pip'"
    exit 1
fi

# Install package
echo "Installing dependencies and package..."
pip3 install -e .

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Installation failed. "
    echo "You might need to use 'pip install -e .' instead of 'pip3', or check permissions."
    exit 1
fi

echo ""
echo "=========================================="
echo "       Installation Complete!"
echo "=========================================="
echo ""

# Check if vadl is in PATH
if ! command -v vadl &> /dev/null; then
    echo "[WARNING] The 'vadl' command is not yet in your PATH."
    echo ""
    echo "You likely need to add the user bin directory to your PATH."
    echo "Common location: ~/.local/bin"
    echo ""
    echo "To fix this temporarily, run:"
    echo "    export PATH=\$PATH:~/.local/bin"
    echo ""
    echo "To fix permanently, add the line above to your ~/.bashrc or ~/.zshrc"
    echo ""
    echo "For now, you can run the tool using:"
    echo "    python3 src/cli.py \"URL\""
else
    echo "Success! You can now run 'vadl' from anywhere."
    echo ""
    echo "Example:"
    echo "   vadl \"https://voiranime.com/anime/one-piece/\""
fi
