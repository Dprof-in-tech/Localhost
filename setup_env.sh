#!/bin/bash
set -e

echo "🚀 Setting up Localhost Environment..."

# 1. Setup Python Virtual Environment
echo "📦 Creating Python virtual environment..."
cd python_brain
python3 -m venv venv
source venv/bin/activate

# 2. Install Dependencies
echo "⬇️ Installing Python dependencies..."
pip install -r requirements.txt
pip install huggingface_hub

# 3. Download Model (Qwen-2.5-3B 4-bit)
echo "🧠 Downloading Qwen-2.5-3B 4-bit model..."
# 3. Download Model (Qwen-2.5-3B 4-bit)
python3 download_model.py

echo "✅ Python environment ready!"
echo ""

# 4. Instructions for Swift
echo "🍎 To Run the App:"
echo "1. Open LocalhostApp/Package.swift in Xcode"
echo "2. Ensure the 'LocalhostApp' scheme is selected"
echo "3. Press Cmd+R to run"
echo "4. Grant Accessibility permissions when prompted"
echo "5. Press Cmd+Shift+. to toggle the overlay"
