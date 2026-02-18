"""Main entry point for the Leumit Appointment Agent."""

import asyncio
import logging
import sys
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


async def main():
    """Main function to run the appointment agent."""
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
        # Use browser automation
        async with LeumitBrowser() as browser:
            # Browser is already at Leumit account page
            # Skip login - assume already authenticated
            logger.info("Step 1: Browser initialized at Leumit account page")
            logger.info("(Assuming already authenticated)")
            
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


def run():
    """Synchronous wrapper to run the async main function."""
    return asyncio.run(main())


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
