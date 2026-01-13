# 🕷️ Selenium Website Cloner with OPSEC Features

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.x-green)](https://www.selenium.dev/)
[![Tor Support](https://img.shields.io/badge/Tor-Supported-orange)](https://www.torproject.org/)
[![License](https://img.shields.io/badge/license-MIT-yellow)](LICENSE)

An advanced, production-ready website cloner using Selenium with OPSEC features including Tor proxy support, rotating Windows user agents, human-like behavior simulation, and full asset downloading.

## ✨ Features

### 🛡️ OPSEC & Anonymity
- **Tor Proxy Integration** - Route all traffic through Tor network
- **Rotating Windows User Agents** - 15+ realistic Windows browser signatures
- **Randomized Behavior** - Variable delays, scroll patterns, mouse movements
- **Referer Spoofing** - Random referer headers from popular sites
- **Screen Size Rotation** - Multiple Windows screen resolutions
- **Browser Fingerprint Obfuscation** - Anti-detection techniques

### 🌐 Website Capture
- **JavaScript Rendering** - Full support for React, Vue, Angular, SPA sites
- **Complete Asset Download** - HTML, CSS, JS, images, fonts, screenshots
- **Dynamic Content Waiting** - Intelligent wait for AJAX/API calls
- **Human-like Interaction** - Natural scrolling, mouse movements, delays
- **Site Crawling** - Recursive crawling with depth control
- **Metadata Capture** - Full page info, timestamps, user agents

### ⚙️ Advanced Options
- **Headless/Visible Mode** - Run with or without browser UI
- **Custom Chrome Path** - Use system Chrome or Chromium
- **Rate Limiting** - Control request frequency
- **Selective Download** - Choose asset types to download
- **Verbose Logging** - Detailed debug information
- **Resume Support** - Continue interrupted downloads

## 📋 Prerequisites

### System Requirements
- **Linux** (Ubuntu/Debian, Fedora, Arch, etc.)
- **Python 3.8+**
- **Chrome/Chromium** browser (version 100+ recommended)
- **At least 2GB RAM** (4GB+ recommended for complex sites)
- **Disk space** depending on website size

### Network Requirements
- **Internet connection** for downloading
- **Tor** (optional, for anonymous cloning)

## 🚀 Installation

### Quick Install (One Command)
```bash
# Download and run installer
curl -sSL https://raw.githubusercontent.com/yourusername/selenium-cloner/main/install.sh | bash
