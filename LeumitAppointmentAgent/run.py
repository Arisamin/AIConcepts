"""
Unified Leumit automation script.
- NEW RUN: Launch Chrome, navigate to login, fill credentials
- RECOVERY RUN: Connect to existing browser session and continue from last stage
"""

import asyncio
import logging
import subprocess
import sys
import platform
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser.state import BrowserState, STAGE_LOGIN_READY, STAGE_FORM_FILLED, STAGE_OTP_READY
from config.credentials import Credentials
from playwright.async_api import async_playwright

GOOGLE_URL = "https://www.google.com"
LEUMIT_SEARCH_TERM = "לאומית"
DEBUG_PORT = 9222
CHROME_DATA_DIR = Path(__file__).parent / ".chrome_data"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def find_chrome():
    """Find Chrome executable."""
    if platform.system() == "Windows":
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        for path in possible_paths:
            if Path(path).exists():
                return path
        return None
    else:
        return "google-chrome"


async def new_run():
    """NEW RUN: Launch browser and complete initial login flow."""
    logger.info("=" * 60)
    logger.info("NEW RUN - Starting Fresh Browser Session")
    logger.info("=" * 60)
    logger.info("")
    
    # Validate credentials first
    if not Credentials.validate_credentials():
        logger.error("❌ Credentials not configured")
        logger.error("Create .env file with:")
        logger.error("  LEUMIT_ID=<your-id>")
        logger.error("  LEUMIT_MOBILE=<your-phone>")
        return False
    
    user_id = Credentials.get_leumit_id()
    user_phone = Credentials.get_leumit_mobile()
    
    # Find Chrome
    chrome_exe = find_chrome()
    if not chrome_exe:
        logger.error("❌ Chrome not found")
        return False
    
    logger.info(f"Using Chrome: {chrome_exe}")
    logger.info("")
    
    # Launch Chrome
    try:
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 5  # SW_SHOW
            
            chrome_process = subprocess.Popen(
                [
                    chrome_exe,
                    "--new-window",
                    f"--remote-debugging-port={DEBUG_PORT}",
                    f"--user-data-dir={CHROME_DATA_DIR}",
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "https://online2.leumit.co.il/Online/Login/HomePage.aspx"
                ],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NEW_CONSOLE,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            chrome_process = subprocess.Popen(
                [
                    chrome_exe,
                    "--new-window",
                    f"--remote-debugging-port={DEBUG_PORT}",
                    f"--user-data-dir={CHROME_DATA_DIR}",
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    "https://www.google.com"
                ],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        logger.info(f"✓ Chrome launched (PID: {chrome_process.pid})")
        logger.info(f"✓ Remote debug port: {DEBUG_PORT}")
        logger.info(f"✓ Starting URL: Google")
        logger.info("")
        logger.info("Waiting for Chrome to start and page to load...")
        time.sleep(7)  # Give more time for CDP to initialize
        
    except Exception as e:
        logger.error(f"❌ Failed to launch Chrome: {e}")
        return False
    
    # Save initial state
    state = BrowserState.create_new()
    state['browser_pid'] = chrome_process.pid
    state['stage'] = STAGE_LOGIN_READY
    state['chrome_data_dir'] = str(CHROME_DATA_DIR)
    BrowserState.save(state)
    
    # Connect via Playwright and fill form
    try:
        logger.info("Connecting to browser via CDP...")
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{DEBUG_PORT}")
        
        logger.info("✓ Connected to browser")
        
        # Get the login page
        if not browser.contexts:
            logger.error("❌ No browser context found")
            await playwright.stop()
            return False
        
        context = browser.contexts[0]
        pages = context.pages
        
        logger.info(f"Found {len(pages)} page(s)")
        
        # Get the first page (Chrome may show sign-in page or Leumit page)
        page = pages[0] if pages else None
        if not page:
            logger.error("❌ No pages found")
            await playwright.stop()
            return False
        
        logger.info(f"Current page: {page.url}")
        
        # If not on Google, navigate there first
        if "google.com" not in page.url.lower():
            logger.info("Navigating to Google...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            logger.info(f"✓ At Google: {page.url}")
        
        # Search Google for Leumit
        if "google.com" in page.url.lower():
            logger.info(f"Google page detected, searching for '{LEUMIT_SEARCH_TERM}'...")
            
            # Accept cookies if present
            try:
                accept_button = await page.query_selector("button:has-text('Accept all'), button:has-text('I agree')")
                if accept_button:
                    await accept_button.click()
                    await asyncio.sleep(1)
                    logger.info("✓ Accepted Google cookies")
            except:
                pass
            
            # Search for Leumit
            await page.fill("textarea[name='q'], input[name='q']", LEUMIT_SEARCH_TERM)
            await page.press("textarea[name='q'], input[name='q']", "Enter")
            await page.wait_for_load_state("domcontentloaded")
            logger.info("✓ Search completed")
            await asyncio.sleep(2)
            
            # Click the Leumit link
            logger.info("Looking for Leumit website link in search results...")
            leumit_link = await page.query_selector("a[href*='leumit.co.il']")
            if leumit_link:
                await leumit_link.click()
                await page.wait_for_load_state("domcontentloaded")
                logger.info(f"✓ Clicked Leumit link, navigated to: {page.url}")
                await asyncio.sleep(3)
                
                # If on main Leumit site, click "אזור אישי" button
                if "www.leumit.co.il" in page.url and "/Online/Login" not in page.url:
                    logger.info("On Leumit homepage, clicking 'אזור אישי' button...")
                    # Try to find and click the personal area button
                    personal_area_button = await page.query_selector("a:has-text('אזור אישי'), button:has-text('אזור אישי')")
                    if personal_area_button:
                        await personal_area_button.click()
                        logger.info("✓ Clicked 'אזור אישי' button")
                        await asyncio.sleep(3)  # Wait longer for login boxes to appear
                        logger.info(f"✓ Current page: {page.url}")
                    else:
                        logger.warning("⚠️  'אזור אישי' button not found, navigating directly...")
                        await page.goto("https://online2.leumit.co.il/Online/Login/HomePage.aspx", wait_until="domcontentloaded")
                        await asyncio.sleep(2)
                        logger.info(f"✓ Navigated to login: {page.url}")
            else:
                logger.error("❌ Could not find Leumit link in search results")
                await playwright.stop()
                return False
        
        # If error page, try navigating to login
        if "SystemErr" in page.url or "ErrPages" in page.url:
            logger.info("Error page detected, trying to navigate to login...")
            await page.goto("https://online2.leumit.co.il/Online/Login/HomePage.aspx", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            logger.info(f"✓ Navigated to: {page.url}")
        
        # Find Leumit login page
        login_page = None
        pages = context.pages
        for i, p in enumerate(pages):
            logger.info(f"  Page {i+1}: {p.url}")
            if "leumit.co.il" in p.url.lower():
                login_page = p
                break
        
        if not login_page:
            logger.error("❌ Leumit login page not found")
            await playwright.stop()
            return False
        
        logger.info(f"✓ Found login page: {login_page.url}")
        logger.info("")
        
        # Wait a bit for modal/iframe to load (don't wait for networkidle as it may timeout)
        await asyncio.sleep(2)
        
        # Find login frame and form fields
        logger.info("Looking for login form...")
        frames = login_page.frames
        logger.info(f"Found {len(frames)} frame(s)")
        
        login_frame = None
        id_input = None
        
        for frame in frames:
            try:
                # Look for ID input in frames
                elem = await frame.query_selector("#TextBoxIdNumForOTP")
                if elem:
                    login_frame = frame
                    id_input = elem
                    logger.info(f"✓ Found ID input in frame: {frame.name or 'main'}")
                    break
            except:
                pass
        
        if not login_frame:
            logger.warning("❌ Login form not found - page may have loaded immaturely")
            logger.info("Retrying: Navigating back to Google to start fresh...")
            await page.goto("https://www.google.com", wait_until="domcontentloaded")
            await asyncio.sleep(2)
            
            # Search again
            logger.info(f"Searching for '{LEUMIT_SEARCH_TERM}' again...")
            await page.fill("textarea[name='q'], input[name='q']", LEUMIT_SEARCH_TERM)
            await page.press("textarea[name='q'], input[name='q']", "Enter")
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)
            
            # Click Leumit link again
            leumit_link = await page.query_selector("a[href*='leumit.co.il']")
            if leumit_link:
                await leumit_link.click()
                await page.wait_for_load_state("domcontentloaded")
                await asyncio.sleep(3)
                
                # Click אזור אישי again
                personal_area_button = await page.query_selector("a:has-text('אזור אישי'), button:has-text('אזור אישי')")
                if personal_area_button:
                    await personal_area_button.click()
                    await asyncio.sleep(3)
                    logger.info("✓ Retry complete, checking for form again...")
                    
                    # Try finding form again
                    frames = page.frames
                    for frame in frames:
                        try:
                            elem = await frame.query_selector("#TextBoxIdNumForOTP")
                            if elem:
                                login_frame = frame
                                id_input = elem
                                login_page = page
                                logger.info(f"✓ Found ID input in frame after retry")
                                break
                        except:
                            pass
        
        if not login_frame:
            logger.error("❌ Could not find login form even after retry")
            logger.error("Taking screenshot for debugging...")
            screenshot_path = Path(__file__).parent / "screenshots" / "debug_no_form.png"
            screenshot_path.parent.mkdir(exist_ok=True)
            await login_page.screenshot(path=str(screenshot_path))
            logger.error(f"Screenshot saved: {screenshot_path}")
            await playwright.stop()
            return False
        
        logger.info("")
        
        # Fill the form
        logger.info("Filling login form...")
        logger.info(f"  ID: {user_id}")
        logger.info(f"  Phone: {user_phone}")
        
        await id_input.fill(user_id)
        logger.info("✓ Entered ID")
        
        phone_input = await login_frame.query_selector("#TextBoxCellphone")
        if phone_input:
            await phone_input.fill(user_phone)
            logger.info("✓ Entered phone")
        else:
            logger.error("❌ Phone input not found")
            await playwright.stop()
            return False
        
        logger.info("✓ Form filled")
        logger.info("")
        
        # Update state
        state['stage'] = STAGE_FORM_FILLED
        BrowserState.save(state)
        
        # Take screenshot
        screenshot_path = Path(__file__).parent / "screenshots" / "login_filled.png"
        screenshot_path.parent.mkdir(exist_ok=True)
        await login_page.screenshot(path=str(screenshot_path))
        logger.info(f"✓ Screenshot saved: {screenshot_path}")
        logger.info("")
        
        # TEST MODE: Exit here, leave Chrome open
        logger.info("=" * 60)
        logger.info("✅ NEW RUN COMPLETE - Chrome window left open for review")
        logger.info("=" * 60)
        logger.info("")
        logger.info("👉 Review the filled form in Chrome window")
        logger.info("👉 To continue: run script again (recovery mode)")
        logger.info("👉 Chrome will stay open after this script exits")
        logger.info("")
        
        await playwright.stop()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error during form filling: {e}")
        import traceback
        traceback.print_exc()
        return False


async def recovery_run():
    """RECOVERY RUN: Launch Chrome with existing profile (cookies preserved)."""
    logger.info("=" * 60)
    logger.info("RECOVERY RUN - Launching Chrome with Saved Profile")
    logger.info("=" * 60)
    logger.info("")
    
    state = BrowserState.load()
    logger.info(f"Previous stage: {state['stage']}")
    logger.info(f"Using saved profile: {state.get('chrome_data_dir', CHROME_DATA_DIR)}")
    logger.info("ℹ️  Login cookies should be preserved from previous session")
    logger.info("")
    
    # Note: We're essentially doing a NEW RUN but with existing profile
    # This preserves cookies while giving us debugging control
    logger.info("⚠️  Recovery mode will launch fresh Chrome with your saved profile")
    logger.info("    (Your login session should be preserved via cookies)")
    logger.info("")
    
    # Just call new_run() - it will use the existing .chrome_data profile
    return await new_run()


async def main():
    """Entry point."""
    if BrowserState.exists():
        # Recovery mode
        success = await recovery_run()
    else:
        # New run
        success = await new_run()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
