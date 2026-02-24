"""
Form filler - handles RECOVERY run flow.
Connects to existing browser and fills in the login form.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from browser.state import BrowserState, STAGE_LOGIN_READY, STAGE_FORM_FILLED
from config.credentials import Credentials
from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def fill_login_form() -> bool:
    """Connect to existing browser and fill login form."""
    logger.info("=" * 60)
    logger.info("RECOVERY RUN - Connecting to Existing Browser")
    logger.info("=" * 60)
    logger.info("")
    
    # Load state
    state = BrowserState.load()
    if not state:
        logger.error("❌ No browser session found")
        logger.error("Run: python start_browser.py")
        return False
    
    logger.info(f"Current stage: {state['stage']}")
    logger.info(f"Browser endpoint: {state['endpoint']}")
    logger.info("")
    
    # Load credentials
    if not Credentials.validate_credentials():
        logger.error("❌ Credentials not configured")
        logger.error("Create .env file with:")
        logger.error("  LEUMIT_ID=<your-id>")
        logger.error("  LEUMIT_MOBILE=<your-phone>")
        return False
    
    user_id = Credentials.get_leumit_id()
    user_phone = Credentials.get_leumit_mobile()
    
    try:
        # Connect to existing browser
        logger.info("Connecting to browser...")
        logger.info(f"  Using Chrome data dir: {state.get('chrome_data_dir', 'N/A')}")
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.connect_over_cdp(state['endpoint'])
        
        logger.info("✓ Connected to browser")
        
        # Get all pages (including tabs)
        if not browser.contexts:
            logger.error("❌ No browser context found")
            await playwright.stop()
            input("Press Enter to exit...")
            return False
        
        context = browser.contexts[0]
        pages = context.pages
        
        logger.info(f"Found {len(pages)} page(s)/tab(s) in browser")
        
        # Try to find Leumit login page
        login_page = None
        for i, page in enumerate(pages):
            url = page.url
            logger.info(f"  Tab {i+1}: {url}")
            
            if "leumit" in url.lower() or "login" in url.lower():
                login_page = page
                logger.info(f"    ✓ Found Leumit page!")
        
        if not login_page:
            logger.warning("⚠️  No Leumit page found, using first page")
            if pages:
                login_page = pages[0]
            else:
                logger.error("❌ No pages found in browser")
                await playwright.stop()
                input("Press Enter to exit...")
                return False
        
        logger.info("")
        logger.info(f"Using page: {login_page.url}")
        logger.info("")
        
        # Wait for page to be ready
        await login_page.wait_for_load_state("networkidle")
        
        # Find login frame
        logger.info("Looking for login form...")
        frames = login_page.frames
        logger.info(f"Found {len(frames)} frame(s)")
        
        # Try to find input fields
        login_frame = None
        id_input = None
        
        for frame in frames:
            try:
                # Look for ID input
                elem = await frame.query_selector("#TextBoxIdNumForOTP")
                if elem:
                    login_frame = frame
                    id_input = elem
                    logger.info(f"✓ Found ID input in frame: {frame.name}")
                    break
            except:
                pass
        
        if not login_frame:
            logger.error("❌ Could not find login form")
            logger.error("Available frames:")
            for frame in frames:
                logger.error(f"  - {frame.name}: {frame.url}")
            await playwright.stop()
            input("Press Enter to exit...")
            return False
        
        # Fill ID
        logger.info("")
        logger.info("Filling credentials...")
        await id_input.fill(user_id)
        logger.info(f"✓ Entered ID")
        
        # Fill phone
        phone_input = await login_frame.query_selector("#TextBoxCellphone")
        if phone_input:
            await phone_input.fill(user_phone)
            logger.info(f"✓ Entered phone")
        else:
            logger.warning("⚠️  Could not find phone input")
        
        # Take screenshot
        screenshot_path = Path(__file__).parent / "form_filled.png"
        await login_page.screenshot(path=str(screenshot_path))
        logger.info(f"✓ Screenshot saved: {screenshot_path}")
        logger.info("")
        
        # Update state
        BrowserState.update_stage(STAGE_FORM_FILLED)
        
        logger.info("=" * 60)
        logger.info("Form Filled Successfully!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Check the form in Chrome browser")
        logger.info("2. Enter the OTP code when prompted")
        logger.info("3. Continue with the appointment booking")
        logger.info("")
        
        # Disconnect (don't close browser)
        await playwright.stop()
        logger.info("Python script exiting (browser stays open)")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        return False


def main():
    """Entry point."""
    try:
        return asyncio.run(fill_login_form())
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
