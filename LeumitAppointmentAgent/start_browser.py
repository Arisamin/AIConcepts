"""
Browser launcher - handles NEW run flow.
Starts fresh Chrome window with remote debugging.
Navigates to Leumit login page.
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

from browser.state import BrowserState, STAGE_LOGIN_READY

LEUMIT_HOME_URL = "https://online2.leumit.co.il/Online/Login/HomePage.aspx"
DEBUG_PORT = 9222
CHROME_DATA_DIR = Path(__file__).parent / ".chrome_data"  # Dedicated Chrome profile directory

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


def launch_new_browser() -> bool:
    """Launch new Chrome window as independent process."""
    logger.info("=" * 60)
    logger.info("NEW RUN - Starting Fresh Browser")
    logger.info("=" * 60)
    logger.info("")
    
    chrome_exe = find_chrome()
    if not chrome_exe:
        logger.error("❌ Chrome not found")
        return False
    
    logger.info(f"Using Chrome: {chrome_exe}")
    logger.info("")
    
    try:
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 5  # SW_SHOW
            
            # Use dedicated user-data-dir so we can reliably reconnect
            chrome_process = subprocess.Popen(
                [
                    chrome_exe,
                    "--new-window",
                    f"--remote-debugging-port={DEBUG_PORT}",
                    f"--user-data-dir={CHROME_DATA_DIR}",
                    "--start-maximized",
                    LEUMIT_HOME_URL
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
                    "--start-maximized",
                    LEUMIT_HOME_URL
                ],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        logger.info(f"✓ Chrome started (PID: {chrome_process.pid})")
        logger.info(f"✓ Remote debug port: {DEBUG_PORT}")
        logger.info(f"✓ URL: {LEUMIT_HOME_URL}")
        logger.info("")
        
        # Wait for Chrome to start
        logger.info("Waiting for Chrome to fully start...")
        time.sleep(3)
        
        # Save state
        state = BrowserState.create_new()
        state['browser_pid'] = chrome_process.pid
        state['stage'] = STAGE_LOGIN_READY
        state['chrome_data_dir'] = str(CHROME_DATA_DIR)
        BrowserState.save(state)
        
        logger.info("✓ Browser state saved")
        logger.info("")
        logger.info("=" * 60)
        logger.info("Ready for next step!")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Next: Run the form filler script to enter credentials")
        logger.info("")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to launch Chrome: {e}")
        return False


def monitor_browser(browser_pid):
    """Keep script alive while monitoring Chrome process."""
    logger.info("Monitoring Chrome process (PID: %d)" % browser_pid)
    logger.info("You can now run fill_form.py in another terminal")
    logger.info("Press Ctrl+C to stop monitoring")
    logger.info("")
    
    try:
        while True:
            time.sleep(1)
            # On Windows, we can't easily check if process is alive
            # Just keep the script running as a keepalive
    except KeyboardInterrupt:
        logger.info("\nMonitoring stopped. Chrome still running.")
        return 0


def main():
    """Entry point."""
    # Check if already running
    if BrowserState.exists():
        state = BrowserState.load()
        logger.info(f"⚠️  Browser already running (Stage: {state['stage']})")
        logger.info("Run the form filler script instead to continue.")
        return 1
    
    success = launch_new_browser()
    
    if not success:
        logger.error("")
        logger.error("❌ Failed to launch browser")
        return 1
    
    # Get the PID we just saved
    state = BrowserState.load()
    browser_pid = state.get('browser_pid')
    
    # Keep running to maintain CDP port connection
    return monitor_browser(browser_pid)


if __name__ == "__main__":
    sys.exit(main())
