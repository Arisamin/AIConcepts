"""Simple test - connect to running Chrome and navigate."""

import asyncio
import logging
from playwright.async_api import async_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    logger.info("\n" + "="*70)
    logger.info("STAGE 1: Starting simple test...")
    logger.info("="*70)
    
    try:
        logger.info("  [STAGE 1.1] Initializing Playwright...")
        playwright = await async_playwright().start()
        logger.info("  [STAGE 1.1] ✓ Playwright initialized")
        
        url = "https://online2.leumit.co.il/Online/Login/HomePage.aspx"
        logger.info(f"\n[STAGE 2] Launching persistent context...")
        logger.info(f"  URL: {url}")
        
        logger.info("  [STAGE 2.1] Creating persistent context...")
        context = await playwright.chromium.launch_persistent_context(
            user_data_dir=None  # Use default
        )
        logger.info("  [STAGE 2.1] ✓ Persistent context created")
        
        logger.info("  [STAGE 2.2] Creating new page...")
        page = await context.new_page()
        logger.info("  [STAGE 2.2] ✓ New page created")
        
        logger.info(f"\n[STAGE 3] Navigating to {url}...")
        await page.goto(url, timeout=30000)
        logger.info("  [STAGE 3] ✓ Page loaded successfully")
        
        logger.info(f"\n[STAGE 4] Waiting 30 seconds...")
        await asyncio.sleep(30)
        logger.info("  [STAGE 4] ✓ Wait completed")
        
        logger.info(f"\n[STAGE 5] Closing browser...")
        await context.close()
        await playwright.stop()
        logger.info("  [STAGE 5] ✓ Browser closed")
        logger.info("\n[SUCCESS] Test completed!\n")
        
    except asyncio.TimeoutError:
        logger.error("\n[TIMEOUT] Operation timed out (30s)")
        try:
            await playwright.stop()
        except:
            pass
        
    except Exception as e:
        logger.error(f"\n[ERROR] {type(e).__name__}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        try:
            await playwright.stop()
        except:
            pass

if __name__ == "__main__":
    asyncio.run(main())
