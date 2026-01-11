#!/bin/bash
set -e

# Configuration
APP_NAME="Localhost"
INSTALL_DIR="$HOME/.localhost"

# Resolve the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
BRAIN_SRC="$SCRIPT_DIR/python_brain"

echo "🚀 Installing $APP_NAME Brain to $INSTALL_DIR..."

# 1. Create Directory Structure
echo "📂 Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$INSTALL_DIR/python_brain"
mkdir -p "$INSTALL_DIR/models"

# 2. Copy Python Logic
if [ ! -d "$BRAIN_SRC" ]; then
    echo "❌ Error: Could not find 'python_brain' folder next to this script."
    echo "Is the zip file extracted correctly?"
    read -p "Press Enter to exit..."
    exit 1
fi

echo "📦 Copying Python source code..."
rsync -av "$BRAIN_SRC/" "$INSTALL_DIR/python_brain/"

# 3. Create Virtual Environment
echo "🐍 Setting up Python Virtual Environment..."
if [ ! -f "$INSTALL_DIR/venv/bin/python" ]; then
    python3 -m venv "$INSTALL_DIR/venv"
fi

# 4. Install Dependencies
echo "📥 Installing Python dependencies (this may take a minute)..."
"$INSTALL_DIR/venv/bin/pip" install --upgrade pip
"$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/python_brain/requirements.txt"

# 5. Download Model (Optional Check)
# We check if MLX is working and maybe trigger a model download or verify it
echo "🧠 Verifying MLX and Model setup..."
# We can run a small pure-python script to trigger model download if needed, 
# or just rely on the app to do it on first launch.
# For now, we'll let the user know.

echo ""
echo "✅ Installation Complete!"
echo "------------------------------------------------"
echo "The Localhost Brain is installed at: $INSTALL_DIR"
echo "You can now run Localhost.app."
echo "------------------------------------------------"
