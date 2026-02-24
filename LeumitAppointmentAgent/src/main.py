"""Main entry point for the Leumit Appointment Agent."""

import asyncio
import logging
import sys
import signal
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config.settings import LOGS_DIR, LOG_LEVEL, LOG_FORMAT
from config.credentials import Credentials
from browser.automation import LeumitBrowser
from ai.decision_maker import AppointmentDecisionMaker

# Setup logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGS_DIR / "agent.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Global browser reference to keep it alive
browser_instance = None


def signal_handler(signum, frame):
    """Handle signals gracefully - allows browser to stay open."""
    logger.info("Signal received - script exiting but browser stays open")
    # Just exit - don't close anything
    sys.exit(0)


# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
if sys.platform != "win32":
    signal.signal(signal.SIGTERM, signal_handler)


async def main():
    """Main function to run the appointment agent."""
    global browser_instance
    
    logger.info("=" * 60)
    logger.info("Starting Leumit Appointment Agent")
    logger.info("=" * 60)
    
    # Validate credentials
    if not Credentials.validate_credentials():
        logger.error("Credentials not found. Please configure .env file.")
        logger.error("Copy .env.example to .env and fill in your credentials.")
        return False
    
    # Initialize decision maker
    decision_maker = AppointmentDecisionMaker()
    
    try:
        # IMPORTANT: Don't use async context manager - manually manage browser
        # This prevents automatic cleanup that closes the browser
        browser = LeumitBrowser()
        browser_instance = browser
        
        # Manually start browser (don't use __aenter__)
        await browser.start()
        
        try:
            # Step 1: Login (or use cached cookies)
            logger.info("Step 1: Authenticating...")
            login_success = await browser.login()
            
            if not login_success:
                logger.error("Login failed. Please check your credentials.")
                return False
            
            # Step 2: Navigate to appointments
            logger.info("Step 2: Navigating to appointments section...")
            nav_success = await browser.navigate_to_appointments()
            
            if not nav_success:
                logger.error("Could not navigate to appointments section.")
                return False
            
            # Step 3: Search for appointments
            logger.info("Step 3: Searching for available appointments...")
            appointments = await browser.search_appointments()
            
            if not appointments:
                logger.info("No appointments found.")
                return True
            
            # Step 4: Select best appointment
            logger.info("Step 4: Analyzing appointments...")
            best_appointment = decision_maker.select_best_appointment(appointments)
            
            if not best_appointment:
                logger.info("No suitable appointments found matching preferences.")
                return True
            
            # Step 5: Book appointment (optional - can be disabled for testing)
            logger.info("Step 5: Ready to book appointment...")
            logger.info(f"Best appointment: {best_appointment['time']} with {best_appointment['doctor']}")
            
            # Uncomment to actually book:
            # booking_success = await browser.book_appointment(best_appointment)
            # if booking_success:
            #     logger.info("✓ Appointment booked successfully!")
            # else:
            #     logger.error("✗ Failed to book appointment")
            
            logger.info("Run completed successfully!")
            return True
        
        finally:
            # IMPORTANT: Do NOT close the browser here
            # We want it to stay open with the logged-in session
            # Don't call: await browser.close()
            logger.info("Browser left open (not closing)")
            
    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        return False
    finally:
        logger.info("=" * 60)
        logger.info("Leumit Appointment Agent finished")
        logger.info("=" * 60)
        logger.info("")
        logger.info("✓ Browser session is ready and waiting")
        logger.info("")
        logger.info("TO KEEP THE BROWSER OPEN:")
        logger.info("  - This script will keep running indefinitely")
        logger.info("  - Press Ctrl+C anytime to close the browser and exit")
        logger.info("  - If running from VS Code chat: use run_detached.bat instead")
        logger.info("")
        logger.info("The browser will stay open with your logged-in session.")
        logger.info("=" * 60)
        logger.info("")
        
        # Keep the browser alive by running event loop indefinitely
        # This prevents the script from exiting and closing the browser
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Closing browser...")
            if browser_instance:
                await browser_instance.close()
            logger.info("Done.")


def run():
    """Synchronous wrapper to run the async main function."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        # User pressed Ctrl+C
        return 0


if __name__ == "__main__":
    try:
        success = run()
        # Don't exit immediately - give browser time to stay open
        # The browser reference should keep it alive even after this script "completes"
        import time
        time.sleep(0.5)
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        # Handle Ctrl+C at top level
        sys.exit(0)
