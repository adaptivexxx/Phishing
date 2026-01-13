95839005#!/usr/bin/env python3
"""
selenium-clone.py - Advanced website cloner using Selenium
Ideal for JavaScript-heavy sites (React, Vue, Angular, etc.)
"""

import os
import sys
import time
import random
import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urlparse, urljoin, urlunparse

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.proxy import Proxy, ProxyType
from selenium.common.exceptions import TimeoutException, WebDriverException

# For downloading assets
import requests
from bs4 import BeautifulSoup
import json

# ============================================================================
# CONFIGURATION
# ============================================================================

# Windows User Agents (rotating for OPSEC)
WINDOWS_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.6045.159 Safari/537.36 Edg/119.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36 OPR/103.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36 Brave/116.0.0.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Vivaldi/6.1.0.0",
]

# Screen resolutions to rotate
SCREEN_SIZES = [
    (1920, 1080),  # Full HD
    (1366, 768),   # Common laptop
    (1536, 864),   # MacBook-like
    (1280, 720),   # HD
    (1440, 900),   # WXGA+
    (2560, 1440),  # 2K
]

# Referers for realism
REFERERS = [
    "https://www.google.com/",
    "https://www.bing.com/",
    "https://duckduckgo.com/",
    "https://www.reddit.com/",
    "https://news.ycombinator.com/",
    "https://www.wikipedia.org/",
    "https://github.com/",
    "",
]

# Default Chrome options
DEFAULT_CHROME_ARGS = [
    '--no-sandbox',
    '--disable-dev-shm-usage',
    '--disable-gpu',
    '--disable-software-rasterizer',
    '--disable-blink-features=AutomationControlled',
    '--disable-features=VizDisplayCompositor',
    '--disable-background-timer-throttling',
    '--disable-backgrounding-occluded-windows',
    '--disable-renderer-backgrounding',
    '--disable-features=IsolateOrigins,site-per-process',
    '--disable-ipc-flooding-protection',
    '--disable-hang-monitor',
    '--disable-popup-blocking',
    '--disable-prompt-on-repost',
    '--disable-client-side-phishing-detection',
    '--disable-sync',
    '--disable-default-apps',
    '--disable-translate',
    '--disable-web-resources',
    '--disable-extensions',
    '--disable-component-extensions-with-background-pages',
    '--disable-breakpad',
    '--disable-component-update',
    '--disable-domain-reliability',
    '--disable-features=AudioServiceOutOfProcess,AudioServiceSandbox',
    '--metrics-recording-only',
    '--no-first-run',
    '--safebrowsing-disable-auto-update',
    '--password-store=basic',
    '--use-mock-keychain',
    '--hide-scrollbars',
    '--mute-audio',
    '--disable-notifications',
    '--disable-logging',
    '--log-level=3',
    '--silent',
]

# ============================================================================
# LOGGING SETUP
# ============================================================================

def setup_logging(verbose: bool = False):
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

# ============================================================================
# RANDOMIZATION FUNCTIONS
# ============================================================================

def get_random_user_agent() -> str:
    """Return a random Windows user agent."""
    return random.choice(WINDOWS_USER_AGENTS)

def get_random_screen_size() -> tuple:
    """Return random screen dimensions."""
    return random.choice(SCREEN_SIZES)

def get_random_referer() -> str:
    """Return random referer or empty string."""
    return random.choice(REFERERS)

def get_random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0) -> float:
    """Return random delay between requests."""
    return random.uniform(min_seconds, max_seconds)

def get_random_scroll_pattern() -> list:
    """Generate random scroll pattern to mimic human behavior."""
    scrolls = []
    for _ in range(random.randint(3, 8)):
        scrolls.append(random.randint(100, 800))
        scrolls.append(random.uniform(0.1, 1.5))  # Delay between scrolls
    return scrolls

# ============================================================================
# TOR SUPPORT
# ============================================================================

def configure_tor_proxy(port: int = 9050) -> Dict:
    """Configure Selenium to use Tor proxy."""
    return {
        'proxy': {
            'proxyType': 'manual',
            'socksProxy': f'127.0.0.1:{port}',
            'socksVersion': 5,
        }
    }

def test_tor_connection(port: int = 9050) -> bool:
    """Test if Tor connection is working."""
    try:
        proxies = {
            'http': f'socks5h://127.0.0.1:{port}',
            'https': f'socks5h://127.0.0.1:{port}'
        }
        response = requests.get('https://check.torproject.org/api/ip', 
                              proxies=proxies, timeout=10)
        return response.json().get('IsTor', False)
    except:
        return False

# ============================================================================
# CHROME DRIVER SETUP
# ============================================================================

def setup_chrome_driver(
    use_tor: bool = False,
    headless: bool = True,
    user_agent: Optional[str] = None,
    screen_size: Optional[tuple] = None,
    chrome_path: Optional[str] = None
) -> webdriver.Chrome:
    """
    Configure and return Chrome driver with advanced options.
    
    Args:
        use_tor: Whether to use Tor proxy
        headless: Run in headless mode
        user_agent: Custom user agent string
        screen_size: Tuple of (width, height)
        chrome_path: Path to Chrome/Chromium binary
    """
    chrome_options = Options()
    
    # Add default arguments
    for arg in DEFAULT_CHROME_ARGS:
        chrome_options.add_argument(arg)
    
    # Headless mode
    if headless:
        chrome_options.add_argument('--headless=new')
    
    # Custom Chrome binary path
    if chrome_path and os.path.exists(chrome_path):
        chrome_options.binary_location = chrome_path
    
    # User agent
    if user_agent:
        chrome_options.add_argument(f'user-agent={user_agent}')
    
    # Screen size
    if screen_size:
        chrome_options.add_argument(f'--window-size={screen_size[0]},{screen_size[1]}')
    else:
        chrome_options.add_argument('--window-size=1920,1080')
    
    # Anti-detection settings
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Disable automation flags
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    
    # Disable automation in navigator
    chrome_options.add_argument('--disable-web-security')
    chrome_options.add_argument('--allow-running-insecure-content')
    
    # Performance optimizations
    chrome_options.add_argument('--disable-accelerated-2d-canvas')
    chrome_options.add_argument('--disable-accelerated-jpeg-decoding')
    chrome_options.add_argument('--disable-accelerated-mjpeg-decode')
    
    # Configure proxy if using Tor
    if use_tor:
        chrome_options.add_argument('--proxy-server=socks5://127.0.0.1:9050')
    
    # Set up driver service
    service = Service()
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
    except WebDriverException as e:
        logging.error(f"Failed to create Chrome driver: {e}")
        logging.info("Attempting to find Chrome binary automatically...")
        
        # Try common Chrome paths
        common_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/local/bin/chrome',
            '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
            'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
            'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                chrome_options.binary_location = path
                try:
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                    logging.info(f"Successfully used Chrome at: {path}")
                    break
                except:
                    continue
        else:
            raise Exception("Could not find Chrome/Chromium binary. Please install Chrome or specify path with --chrome-path")
    
    # Execute CDP commands to evade detection
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            window.chrome = {
                runtime: {}
            };
        '''
    })
    
    return driver

# ============================================================================
# HUMAN-LIKE BEHAVIOR
# ============================================================================

def human_like_scroll(driver: webdriver.Chrome, scroll_pattern: Optional[list] = None):
    """Scroll the page in a human-like pattern."""
    if not scroll_pattern:
        scroll_pattern = get_random_scroll_pattern()
    
    current_scroll = 0
    for i in range(0, len(scroll_pattern), 2):
        if i + 1 < len(scroll_pattern):
            scroll_amount = scroll_pattern[i]
            delay = scroll_pattern[i + 1]
            
            current_scroll += scroll_amount
            driver.execute_script(f"window.scrollTo(0, {current_scroll});")
            time.sleep(delay)
    
    # Randomly scroll back up a bit
    if random.random() > 0.7:
        scroll_back = random.randint(100, 400)
        driver.execute_script(f"window.scrollBy(0, -{scroll_back});")
        time.sleep(random.uniform(0.5, 1.5))

def human_like_mouse_movement(driver: webdriver.Chrome):
    """Simulate human-like mouse movements."""
    try:
        # Move mouse to random positions
        for _ in range(random.randint(3, 7)):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            driver.execute_script(f"""
                var evt = new MouseEvent('mousemove', {{
                    clientX: {x},
                    clientY: {y},
                    bubbles: true
                }});
                document.dispatchEvent(evt);
            """)
            time.sleep(random.uniform(0.1, 0.5))
    except:
        pass  # Silently fail if JavaScript execution fails

def mimic_human_behavior(driver: webdriver.Chrome):
    """Execute all human-like behaviors."""
    time.sleep(get_random_delay(0.5, 2.0))
    human_like_scroll(driver)
    human_like_mouse_movement(driver)
    time.sleep(get_random_delay(0.5, 1.5))

# ============================================================================
# ASSET DOWNLOADER
# ============================================================================

class AssetDownloader:
    """Handles downloading of assets (CSS, JS, images, fonts)."""
    
    def __init__(self, base_url: str, output_dir: Path, use_tor: bool = False):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.downloaded_assets = set()
        
        # Configure session
        self.session.headers.update({
            'User-Agent': get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        if use_tor:
            self.session.proxies = {
                'http': 'socks5h://127.0.0.1:9050',
                'https': 'socks5h://127.0.0.1:9050'
            }
    
    def download_asset(self, url: str, asset_type: str) -> Optional[Path]:
        """Download a single asset and return local path."""
        if not url or url in self.downloaded_assets:
            return None
        
        try:
            # Make URL absolute
            if not url.startswith(('http://', 'https://')):
                url = urljoin(self.base_url, url)
            
            # Skip external domains (optional)
            base_domain = urlparse(self.base_url).netloc
            asset_domain = urlparse(url).netloc
            # if asset_domain != base_domain:
            #     return None
            
            # Generate filename
            parsed_url = urlparse(url)
            path = parsed_url.path.lstrip('/')
            if not path:
                path = 'index.html'
            
            # Create clean filename
            filename = path.replace('/', '_').replace('?', '_').replace('&', '_')
            if len(filename) > 200:
                import hashlib
                filename_hash = hashlib.md5(filename.encode()).hexdigest()[:10]
                ext = os.path.splitext(filename)[1] or '.bin'
                filename = f'{filename_hash}{ext}'
            
            # Create directory structure
            asset_dir = self.output_dir / asset_type
            asset_dir.mkdir(parents=True, exist_ok=True)
            filepath = asset_dir / filename
            
            # Download asset
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Save file
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            self.downloaded_assets.add(url)
            logging.debug(f"Downloaded {asset_type}: {url}")
            
            return filepath
            
        except Exception as e:
            logging.debug(f"Failed to download {url}: {e}")
            return None
    
    def extract_and_download_assets(self, html_content: str) -> Dict[str, list]:
        """Extract assets from HTML and download them."""
        soup = BeautifulSoup(html_content, 'html.parser')
        assets = {'css': [], 'js': [], 'img': [], 'font': []}
        
        # CSS files
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                path = self.download_asset(href, 'css')
                if path:
                    assets['css'].append(str(path))
        
        # JavaScript files
        for script in soup.find_all('script', src=True):
            src = script.get('src')
            if src:
                path = self.download_asset(src, 'js')
                if path:
                    assets['js'].append(str(path))
        
        # Images
        for img in soup.find_all('img', src=True):
            src = img.get('src')
            if src and not src.startswith('data:'):  # Skip data URLs
                path = self.download_asset(src, 'img')
                if path:
                    assets['img'].append(str(path))
        
        # Fonts
        for link in soup.find_all('link', rel=['preload', 'stylesheet']):
            href = link.get('href')
            if href and any(href.endswith(ext) for ext in ['.woff', '.woff2', '.ttf', '.eot', '.otf']):
                path = self.download_asset(href, 'font')
                if path:
                    assets['font'].append(str(path))
        
        return assets

# ============================================================================
# MAIN CLONER CLASS
# ============================================================================

class SeleniumWebsiteCloner:
    """Main class for cloning websites using Selenium."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.logger = setup_logging(config.get('verbose', False))
        self.driver = None
        self.downloader = None
        self.output_dir = Path(config['output_dir'])
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def initialize(self):
        """Initialize driver and downloader."""
        self.logger.info("Initializing Selenium cloner...")
        
        # Test Tor if enabled
        if self.config.get('use_tor'):
            self.logger.info("Testing Tor connection...")
            if test_tor_connection():
                self.logger.info("✓ Tor connection successful")
            else:
                self.logger.warning("✗ Tor connection failed, proceeding without Tor")
                self.config['use_tor'] = False
        
        # Setup driver
        user_agent = self.config.get('user_agent') or get_random_user_agent()
        screen_size = self.config.get('screen_size') or get_random_screen_size()
        
        self.logger.info(f"Using User-Agent: {user_agent[:80]}...")
        self.logger.info(f"Screen size: {screen_size[0]}x{screen_size[1]}")
        
        self.driver = setup_chrome_driver(
            use_tor=self.config.get('use_tor', False),
            headless=self.config.get('headless', True),
            user_agent=user_agent,
            screen_size=screen_size,
            chrome_path=self.config.get('chrome_path')
        )
        
        # Setup downloader
        self.downloader = AssetDownloader(
            base_url=self.config['url'],
            output_dir=self.output_dir,
            use_tor=self.config.get('use_tor', False)
        )
        
        self.logger.info("Initialization complete")
    
    def capture_page(self, url: str, page_name: str = 'index') -> Dict:
        """Capture a single page with all its assets."""
        self.logger.info(f"Capturing page: {url}")
        
        try:
            # Navigate to URL
            self.driver.get(url)
            
            # Wait for page to load
            wait_time = self.config.get('wait_time', 10)
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Mimic human behavior
            if self.config.get('human_behavior', True):
                mimic_human_behavior(self.driver)
            
            # Wait for dynamic content
            time.sleep(self.config.get('dynamic_wait', 3))
            
            # Get page source after JavaScript execution
            page_source = self.driver.page_source
            
            # Take screenshot
            screenshot_path = self.output_dir / f"{page_name}.png"
            self.driver.save_screenshot(str(screenshot_path))
            
            # Save HTML
            html_path = self.output_dir / f"{page_name}.html"
            html_path.write_text(page_source, encoding='utf-8')
            
            # Download assets
            assets = self.downloader.extract_and_download_assets(page_source)
            
            # Save metadata
            metadata = {
                'url': url,
                'timestamp': datetime.now().isoformat(),
                'user_agent': self.driver.execute_script("return navigator.userAgent;"),
                'screen_size': self.driver.get_window_size(),
                'title': self.driver.title,
                'html_file': str(html_path.relative_to(self.output_dir)),
                'screenshot': str(screenshot_path.relative_to(self.output_dir)),
                'assets': assets,
            }
            
            metadata_path = self.output_dir / f"{page_name}_metadata.json"
            metadata_path.write_text(json.dumps(metadata, indent=2), encoding='utf-8')
            
            self.logger.info(f"✓ Page captured: {self.driver.title}")
            
            return metadata
            
        except TimeoutException:
            self.logger.error(f"Timeout while loading {url}")
            return None
        except Exception as e:
            self.logger.error(f"Error capturing {url}: {e}")
            return None
    
    def crawl_site(self, start_url: str, max_depth: int = 2):
        """Crawl the site recursively."""
        visited = set()
        to_visit = [(start_url, 0)]
        
        while to_visit:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > max_depth:
                continue
            
            self.logger.info(f"Crawling depth {depth}: {url}")
            visited.add(url)
            
            # Capture page
            page_name = f"page_{len(visited)}"
            metadata = self.capture_page(url, page_name)
            
            if metadata and depth < max_depth:
                # Find links on page
                try:
                    links = self.driver.find_elements(By.TAG_NAME, 'a')
                    for link in links:
                        href = link.get_attribute('href')
                        if (href and href.startswith('http') and 
                            urlparse(href).netloc == urlparse(start_url).netloc and
                            href not in visited):
                            to_visit.append((href, depth + 1))
                except:
                    pass
            
            # Random delay between pages
            time.sleep(get_random_delay(2, 5))
    
    def clone(self):
        """Main cloning function."""
        self.logger.info("=" * 60)
        self.logger.info(f"Starting clone of: {self.config['url']}")
        self.logger.info(f"Output directory: {self.output_dir}")
        self.logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            self.initialize()
            
            if self.config.get('crawl', False):
                max_depth = self.config.get('max_depth', 2)
                self.crawl_site(self.config['url'], max_depth)
            else:
                self.capture_page(self.config['url'], 'index')
            
            self.logger.info("=" * 60)
            self.logger.info("Clone completed successfully!")
            
            # Show summary
            html_files = list(self.output_dir.glob('*.html'))
            screenshots = list(self.output_dir.glob('*.png'))
            asset_dirs = [d for d in self.output_dir.iterdir() if d.is_dir()]
            
            self.logger.info(f"Pages captured: {len(html_files)}")
            self.logger.info(f"Screenshots taken: {len(screenshots)}")
            self.logger.info(f"Asset directories: {len(asset_dirs)}")
            
            for asset_dir in asset_dirs:
                files = list(asset_dir.glob('*'))
                self.logger.info(f"  {asset_dir.name}: {len(files)} files")
            
        except Exception as e:
            self.logger.error(f"Clone failed: {e}")
            raise
        finally:
            if self.driver:
                self.driver.quit()
                self.logger.info("Browser closed")
            
            elapsed = time.time() - start_time
            self.logger.info(f"Total time: {elapsed:.2f} seconds")
    
    def cleanup(self):
        """Clean up temporary files."""
        # Currently no cleanup needed
        pass

# ============================================================================
# COMMAND LINE INTERFACE
# ============================================================================

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Advanced website cloner using Selenium',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s https://example.com
  %(prog)s --tor --depth 2 https://example.com
  %(prog)s --no-headless --chrome-path /usr/bin/chromium https://example.com
  %(prog)s --output ./myclone --verbose https://example.com
        '''
    )
    
    # Required arguments
    parser.add_argument('url', help='URL to clone')
    
    # Output options
    parser.add_argument('-o', '--output', default=None,
                       help='Output directory (default: domain_timestamp)')
    
    # Cloning options
    parser.add_argument('--depth', type=int, default=0,
                       help='Maximum crawl depth (0 = single page, default: 0)')
    parser.add_argument('--crawl', action='store_true',
                       help='Crawl the entire site (alias for --depth 2)')
    
    # Browser options
    parser.add_argument('--no-headless', dest='headless', action='store_false',
                       help='Run browser in visible mode')
    parser.add_argument('--chrome-path', default=None,
                       help='Path to Chrome/Chromium binary')
    parser.add_argument('--user-agent', default=None,
                       help='Custom user agent string')
    parser.add_argument('--screen-size', default=None,
                       help='Screen size WxH (e.g., 1920x1080)')
    
    # Behavior options
    parser.add_argument('--no-human-behavior', dest='human_behavior', action='store_false',
                       help='Disable human-like behavior simulation')
    parser.add_argument('--wait-time', type=int, default=10,
                       help='Maximum wait time for page load (seconds)')
    parser.add_argument('--dynamic-wait', type=float, default=3.0,
                       help='Additional wait for dynamic content (seconds)')
    
    # OPSEC options
    parser.add_argument('--tor', action='store_true',
                       help='Use Tor proxy for anonymity')
    parser.add_argument('--tor-port', type=int, default=9050,
                       help='Tor SOCKS5 proxy port (default: 9050)')
    
    # Debug options
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--test-only', action='store_true',
                       help='Test configuration without downloading')
    
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # Set crawl depth
    if args.crawl and args.depth == 0:
        args.depth = 2
    
    # Parse screen size
    screen_size = None
    if args.screen_size:
        try:
            screen_size = tuple(map(int, args.screen_size.split('x')))
        except:
            print(f"Invalid screen size: {args.screen_size}. Using default.")
    
    # Generate output directory name
    if not args.output:
        domain = urlparse(args.url).netloc.replace('.', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        args.output = f"{domain}_{timestamp}"
    
    # Configuration
    config = {
        'url': args.url,
        'output_dir': args.output,
        'use_tor': args.tor,
        'tor_port': args.tor_port,
        'headless': args.headless,
        'chrome_path': args.chrome_path,
        'user_agent': args.user_agent,
        'screen_size': screen_size,
        'human_behavior': args.human_behavior,
        'wait_time': args.wait_time,
        'dynamic_wait': args.dynamic_wait,
        'crawl': args.depth > 0,
        'max_depth': args.depth,
        'verbose': args.verbose,
        'test_only': args.test_only,
    }
    
    # Run cloner
    try:
        cloner = SeleniumWebsiteCloner(config)
        
        if args.test_only:
            print("Testing configuration...")
            cloner.initialize()
            print("✓ Configuration test passed")
            cloner.driver.quit()
        else:
            cloner.clone()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

# ============================================================================
# INSTALLATION SCRIPT
# ============================================================================

def generate_install_script():
    """Generate installation script for dependencies."""
    install_script = '''#!/bin/bash
# install-dependencies.sh - Install Selenium cloner dependencies

echo "Installing Selenium Website Cloner dependencies..."

# Update package list
sudo apt update

# Install system dependencies
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    chromium-browser \
    chromium-chromedriver \
    wget \
    curl \
    tor \
    xvfb \
    x11vnc

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install --upgrade pip
pip install selenium==4.15.0
pip install beautifulsoup4==4.12.2
pip install requests==2.31.0
pip install lxml==4.9.3

# Install Chrome/Chromium WebDriver
CHROME_VERSION=$(chromium --version | grep -oP '\\d+\\.\\d+\\.\\d+\\.\\d+')
CHROMEDRIVER_VERSION=$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROME_VERSION%%.*})
wget -O chromedriver.zip "https://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip"
unzip chromedriver.zip
sudo mv chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver
rm chromedriver.zip

# Make scripts executable
chmod +x selenium-clone.py

# Create aliases
echo "alias clone-site='python3 $(pwd)/selenium-clone.py'" >> ~/.bashrc
echo "alias clone-tor='python3 $(pwd)/selenium-clone.py --tor'" >> ~/.bashrc

echo ""
echo "Installation complete!"
echo "Restart your terminal or run: source ~/.bashrc"
echo ""
echo "Usage examples:"
echo "  clone-site https://example.com"
echo "  clone-tor https://example.com --output ./myclone"
'''

    with open('install-dependencies.sh', 'w') as f:
        f.write(install_script)
    
    os.chmod('install-dependencies.sh', 0o755)
    print("Installation script created: install-dependencies.sh")
    print("Run: ./install-dependencies.sh")

# ============================================================================
# QUICK START SCRIPT
# ============================================================================

def generate_quick_start():
    """Generate quick start script."""
    quick_start = '''#!/bin/bash
# quick-clone.sh - Quick wrapper for common cloning tasks

set -e

URL="$1"
OUTPUT="${2:-$(echo "$1" | sed 's|https://||; s|http://||; s|/|_|g')_$(date +%Y%m%d_%H%M%S)}"

echo "Cloning $URL to $OUTPUT..."

# Single page with Tor
python3 selenium-clone.py "$URL" \
    --output "$OUTPUT" \
    --tor \
    --no-headless \
    --dynamic-wait 5 \
    --verbose

echo "Done! Output in: $OUTPUT"
'''

    with open('quick-clone.sh', 'w') as f:
        f.write(quick_start)
    
    os.chmod('quick-clone.sh', 0o755)
    print("Quick start script created: quick-clone.sh")
    print("Usage: ./quick-clone.sh https://example.com [output_dir]")

# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    # Check if user wants to generate helper scripts
    if len(sys.argv) > 1 and sys.argv[1] == "--install":
        generate_install_script()
        generate_quick_start()
        print("\nHelper scripts generated. Next steps:")
        print("1. Install dependencies: ./install-dependencies.sh")
        print("2. Try cloning: ./quick-clone.sh https://example.com")
    else:
        main()
