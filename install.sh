#!/bin/bash

echo "=========================================="
echo "     Installing Anime-DL (vadl)"
echo "=========================================="
echo ""

# Check for python3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not found!"
    echo "Please install Python 3."
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
