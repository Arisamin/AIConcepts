"""Simple test - connect to running Chrome and navigate."""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("Starting simple test...")
    
    playwright = await async_playwright().start()
    
    url = "https://online2.leumit.co.il/Online/Login/HomePage.aspx"
    logger.info(f"Navigating to: {url}")
    
    try:
        # Open a page directly (this will create a new tab in existing Chrome)
        page = await playwright.chromium.launch_persistent_context(
            user_data_dir=None  # Use default
        ).new_page()
        
    except Exception as e:
        logger.error(f"Could not open page: {e}")
        await playwright.stop()
        return
    
    await page.goto(url)
    logger.info("Page loaded. Keeping window open for 30 seconds...")
    
    await asyncio.sleep(30)
    
    logger.info("Closing...")
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())
