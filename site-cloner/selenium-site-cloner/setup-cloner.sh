#!/bin/bash
# setup-cloner.sh - Complete setup for Selenium cloner

echo "Setting up Selenium Website Cloner..."

# 1. Install system dependencies
sudo apt update
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    chromium-browser \
    chromium-chromedriver \
    tor \
    proxychains4 \
    xvfb \
    wget \
    curl

# 2. Install Python packages
pip3 install --upgrade pip
pip3 install selenium beautifulsoup4 requests lxml

# 3. Download the script
curl -O https://raw.githubusercontent.com/yourusername/selenium-cloner/main/selenium-clone.py
chmod +x selenium-clone.py

# 4. Create alias
echo "alias clone-site='python3 $(pwd)/selenium-clone.py'" >> ~/.bashrc
echo "alias clone-tor='python3 $(pwd)/selenium-clone.py --tor'" >> ~/.bashrc

echo ""
echo "Setup complete! Restart terminal or run: source ~/.bashrc"
echo ""
echo "Usage examples:"
echo "  clone-site https://example.com"
echo "  clone-site --tor --no-headless https://example.com"
echo "  clone-site --depth 2 --output ./backup https://example.com"
