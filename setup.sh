#!/bin/bash
set -e

echo "=== Dictation App Setup ==="
echo ""

# Install system dependency
echo "Installing portaudio via Homebrew..."
brew install portaudio 2>/dev/null || echo "portaudio already installed."
echo ""

# Install Python dependencies
echo "Installing Python packages..."
pip3 install -r requirements.txt
echo ""

echo "=== Setup complete! ==="
echo ""
echo "To run the app:"
echo "  python3 main.py"
echo ""
echo "IMPORTANT: You must grant Accessibility permission to your"
echo "terminal app in System Settings > Privacy & Security > Accessibility."
echo "Without this, the hotkey and text typing will not work."
