#!/bin/bash

# Setup script for Google Colab environment
# Installs all dependencies and Playwright with system requirements

echo "🚀 Setting up Website Intelligence Service for Colab..."

# Update system packages
echo "📦 Updating system packages..."
apt-get update -qq
apt-get install -y -qq libglib2.0-0 libsm6 libxrender1 libxext6 libfontconfig1 libfreetype6 > /dev/null 2>&1

# Install Python dependencies from requirements.txt
echo "📚 Installing Python packages..."
pip install -q --upgrade pip setuptools wheel

# Install all packages from requirements.txt
pip install -q -r requirements.txt

# Install Playwright and browsers
echo "🌐 Installing Playwright and Chromium browser..."
python -m pip install -q playwright

# Install Chromium browser and dependencies for headless operation
python -m playwright install -q chromium

# Install system dependencies for Playwright (needed for Linux)
python -m playwright install-deps -q chromium

# Verify installation
echo "✅ Verifying installation..."
python -c "from playwright.async_api import async_playwright; print('✓ Playwright installed')" 2>/dev/null && echo "✓ Playwright is ready" || echo "✗ Playwright installation may have issues"

python -c "from crawl4ai import AsyncWebCrawler; print('✓ Crawl4AI installed')" 2>/dev/null && echo "✓ Crawl4AI is ready" || echo "✗ Crawl4AI installation may have issues"

python -c "import fastapi; print('✓ FastAPI installed')" 2>/dev/null && echo "✓ FastAPI is ready" || echo "✗ FastAPI installation may have issues"

echo ""
echo "✨ Setup complete! Ready to run the application."
echo ""
echo "To start analyzing websites, run:"
echo "  python colab_runner.py"
echo ""
