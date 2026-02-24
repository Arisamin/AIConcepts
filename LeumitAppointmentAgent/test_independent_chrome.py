"""
Launch browser independently - truly detached from Python process.
Uses subprocess to start Chrome directly, not via Playwright.
Then Playwright connects to it later.
"""

import asyncio
import logging
import subprocess
import sys
import json
from pathlib import Path
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

BROWSER_INFO_FILE = Path(__file__).parent / ".browser_info.json"
DEBUG_PORT = 9222


def launch_chrome_detached():
    """Launch Chrome in a completely detached process."""
    import os
    import platform
    
    logger.info("\n" + "="*70)
    logger.info("[STAGE 1] Launching Chrome as detached process")
    logger.info("="*70)
    logger.info("  [STAGE 1.1] Searching for Chrome executable...")
    
    # Chrome executable path
    if platform.system() == "Windows":
        # Try common locations
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        ]
        
        chrome_exe = None
        for path in possible_paths:
            if Path(path).exists():
                chrome_exe = path
                logger.info(f"  [STAGE 1.1] ✓ Found Chrome at: {path}")
                break
        
        if not chrome_exe:
            logger.error("  [STAGE 1.1] ✗ Chrome not found in standard locations")
            return False
    else:
        chrome_exe = "google-chrome"
    
    logger.info(f"Using Chrome: {chrome_exe}")
    
    # Create Chrome process with detached flag
    # This makes it independent of the parent process
    try:
        if platform.system() == "Windows":
            # On Windows: use CREATE_NEW_PROCESS_GROUP to detach
            import subprocess
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 5  # SW_SHOW constant
            
            chrome_process = subprocess.Popen(
                [
                    chrome_exe,
                    f"--remote-debugging-port={DEBUG_PORT}",
                    "--start-maximized",
                    "https://www.google.com"
                ],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NEW_CONSOLE,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            # On Linux/Mac: use start_new_session
            chrome_process = subprocess.Popen(
                [
                    chrome_exe,
                    f"--remote-debugging-port={DEBUG_PORT}",
                    "--start-maximized",
                    "https://www.google.com"
                ],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        logger.info(f"✓ Chrome process started (PID: {chrome_process.pid})")
        logger.info(f"✓ Remote debugging on port {DEBUG_PORT}")
        
        # Wait for Chrome to fully start
        logger.info("Waiting for Chrome to start...")
        time.sleep(3)
        
        # Save browser info
        browser_info = {
            'pid': chrome_process.pid,
            'port': DEBUG_PORT,
            'endpoint': f'ws://127.0.0.1:{DEBUG_PORT}',
            'timestamp': time.time()
        }
        
        with open(BROWSER_INFO_FILE, 'w') as f:
            json.dump(browser_info, f)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("Chrome is now running INDEPENDENTLY")
        logger.info("=" * 60)
        logger.info("")
        logger.info("✓ You can now close this Python script")
        logger.info("✓ Chrome will stay open (truly independent)")
        logger.info("✓ PID: " + str(chrome_process.pid))
        logger.info("")
        logger.info("Test:")
        logger.info("  1. Close this terminal window")
        logger.info("  2. Wait 5 seconds")
        logger.info("  3. Chrome should STILL be running")
        logger.info("")
        
        # Keep Python running for a moment, but don't actually manage the process
        # This ensures Chrome stays as a separate process group
        try:
            for i in range(10):
                logger.info(f"Keeping script alive... {i+1}s")
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Ctrl+C received")
        
        logger.info("")
        logger.info("Exiting Python script (Chrome stays open)...")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to launch Chrome: {e}", exc_info=True)
        return False


def main():
    """Main entry point."""
    logger.info("=" * 60)
    logger.info("Browser Independence Test")
    logger.info("=" * 60)
    logger.info("")
    
    success = launch_chrome_detached()
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
