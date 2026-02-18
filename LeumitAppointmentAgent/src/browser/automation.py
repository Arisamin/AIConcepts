"""Browser automation logic using Playwright."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, TimeoutError

from config.settings import (
    LEUMIT_HOME_URL,
    HEADLESS,
    BROWSER_TIMEOUT,
    VIEWPORT_WIDTH,
    VIEWPORT_HEIGHT,
    SCREENSHOTS_DIR,
    MAX_RETRIES,
    RETRY_DELAY
)
from config.credentials import Credentials
from browser.selectors import LeumitSelectors

logger = logging.getLogger(__name__)


class LeumitBrowser:
    """Handles browser automation for Leumit website."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.credentials = Credentials()
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Initialize browser and create new page."""
        logger.info("Starting browser...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=HEADLESS,
            args=['--start-maximized']
        )
        
        context = await self.browser.new_context(
            viewport={'width': VIEWPORT_WIDTH, 'height': VIEWPORT_HEIGHT}
        )
        self.page = await context.new_page()
        self.page.set_default_timeout(BROWSER_TIMEOUT)
        logger.info("Browser started successfully")
    
    async def close(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Browser closed")
    
    async def take_screenshot(self, name: str = "screenshot"):
        """Take a screenshot for debugging."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create time-based folder (HH_mm format)
        time_folder = datetime.now().strftime("%H_%M")
        folder_path = SCREENSHOTS_DIR / time_folder
        folder_path.mkdir(exist_ok=True)
        
        filepath = folder_path / f"{name}_{timestamp}.png"
        await self.page.screenshot(path=str(filepath))
        logger.info(f"Screenshot saved: {filepath}")
        return filepath
    
    async def login(self) -> bool:
        """Login to Leumit website.
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            logger.info(f"Navigating to Leumit home page: {LEUMIT_HOME_URL}")
            await self.page.goto(LEUMIT_HOME_URL)
            await self.page.wait_for_load_state("networkidle")
            
            # Take screenshot of home page
            await self.take_screenshot("home_page")
            
            # Click personal area button
            logger.info("Clicking personal area button...")
            await self.page.click(LeumitSelectors.PERSONAL_AREA_BUTTON)
            
            # Wait for popup animation to complete
            logger.info("Waiting for login popup to fully appear...")
            await asyncio.sleep(3)  # Wait 3 seconds for animation
            
            # Take screenshot of login page
            await self.take_screenshot("login_page_before_input")
            
            # Wait for user confirmation that fields are visible
            logger.info("=" * 60)
            logger.info("WAITING FOR YOUR CONFIRMATION")
            logger.info("Please check that the login fields are fully visible")
            logger.info("Press ENTER when ready to continue...")
            logger.info("=" * 60)
            input()  # Wait for user to press Enter
            
            logger.info("User confirmed - proceeding with login...")
            
            # Wait for input fields to become visible
            logger.info("Waiting for input fields to be visible...")
            try:
                await self.page.wait_for_selector("input:visible", timeout=10000, state="visible")
            except Exception as e:
                logger.warning(f"Timeout waiting for visible inputs: {e}")
            
            await self.page.wait_for_load_state("networkidle")
            
            # Take screenshot after user confirmation
            await self.take_screenshot("login_page_after_confirmation")
            
            # Use Playwright's locator with visible filter
            logger.info("Finding visible input fields...")
            
            # The login form might be in an iframe - check all frames
            id_input = None
            mobile_input = None
            login_frame = None
            
            # First try main page
            if await self.page.locator("#TextBoxIdNumForOTP").count() > 0:
                logger.info("Found inputs in main page")
                id_input = self.page.locator("#TextBoxIdNumForOTP")
                mobile_input = self.page.locator("#TextBoxCellphone")
                login_frame = self.page
            else:
                # Check all frames
                logger.info("Inputs not in main page, checking frames...")
                for frame in self.page.frames:
                    frame_url = frame.url
                    logger.info(f"Checking frame: {frame_url}")
                    
                    if await frame.locator("#TextBoxIdNumForOTP").count() > 0:
                        logger.info(f"Found inputs in frame: {frame_url}")
                        id_input = frame.locator("#TextBoxIdNumForOTP")
                        mobile_input = frame.locator("#TextBoxCellphone")
                        login_frame = frame
                        break
            
            if not id_input or not login_frame:
                logger.error("Could not find login input fields in any frame")
                await self.take_screenshot("inputs_not_found")
                return False
            
            # Fill ID (Teudat Zehut)
            logger.info("Entering ID number...")
            user_id = self.credentials.get_leumit_id()
            await id_input.fill(user_id)
            
            # Fill mobile number
            logger.info("Entering mobile number...")
            mobile = self.credentials.get_leumit_mobile()
            await mobile_input.fill(mobile)
            
            # Click login button - use the same frame
            logger.info("Clicking login button...")
            await login_frame.click(LeumitSelectors.LOGIN_SUBMIT_BUTTON)
            
            # Wait for navigation after login
            await self.page.wait_for_load_state("networkidle")
            await self.take_screenshot("after_login")
            
            # Check if login was successful (you may need to adjust this check)
            current_url = self.page.url
            if "login" not in current_url.lower():
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login failed - still on login page")
                return False
                
        except TimeoutError as e:
            logger.error(f"Timeout during login: {e}")
            await self.take_screenshot("login_timeout_error")
            return False
        except Exception as e:
            logger.error(f"Error during login: {e}")
            await self.take_screenshot("login_error")
            return False
    
    async def navigate_to_appointments(self) -> bool:
        """Navigate to appointments section.
        
        Returns:
            bool: True if navigation successful
        """
        try:
            logger.info("Navigating to appointments section...")
            
            # Try to find and click appointments menu
            await self.page.click(LeumitSelectors.APPOINTMENTS_MENU)
            await self.page.wait_for_load_state("networkidle")
            await self.take_screenshot("appointments_page")
            
            logger.info("Successfully navigated to appointments")
            return True
            
        except Exception as e:
            logger.error(f"Error navigating to appointments: {e}")
            await self.take_screenshot("navigation_error")
            return False
    
    async def search_appointments(self, doctor_name: Optional[str] = None) -> list:
        """Search for available appointments.
        
        Args:
            doctor_name: Optional doctor name to filter by
            
        Returns:
            list: List of available appointment slots
        """
        try:
            logger.info("Searching for appointments...")
            
            # Click new appointment button
            await self.page.click(LeumitSelectors.NEW_APPOINTMENT_BUTTON)
            await self.page.wait_for_load_state("networkidle")
            
            # Select doctor if specified
            if doctor_name:
                await self.page.select_option(LeumitSelectors.DOCTOR_SELECT, doctor_name)
            
            # Click search
            await self.page.click(LeumitSelectors.SEARCH_BUTTON)
            await self.page.wait_for_load_state("networkidle")
            await self.take_screenshot("search_results")
            
            # Parse available slots
            appointments = await self._parse_appointment_slots()
            logger.info(f"Found {len(appointments)} available appointments")
            
            return appointments
            
        except Exception as e:
            logger.error(f"Error searching appointments: {e}")
            await self.take_screenshot("search_error")
            return []
    
    async def _parse_appointment_slots(self) -> list:
        """Parse appointment slots from the page.
        
        Returns:
            list: List of appointment dictionaries
        """
        appointments = []
        
        try:
            # Get all slot elements
            slots = await self.page.query_selector_all(LeumitSelectors.AVAILABLE_SLOTS)
            
            for slot in slots:
                try:
                    time_elem = await slot.query_selector(LeumitSelectors.SLOT_TIME)
                    doctor_elem = await slot.query_selector(LeumitSelectors.SLOT_DOCTOR)
                    
                    time_text = await time_elem.inner_text() if time_elem else "Unknown"
                    doctor_text = await doctor_elem.inner_text() if doctor_elem else "Unknown"
                    
                    appointments.append({
                        'time': time_text,
                        'doctor': doctor_text,
                        'element': slot
                    })
                except Exception as e:
                    logger.warning(f"Error parsing slot: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Error parsing appointment slots: {e}")
        
        return appointments
    
    async def book_appointment(self, appointment: dict) -> bool:
        """Book a specific appointment.
        
        Args:
            appointment: Appointment dictionary with 'element' key
            
        Returns:
            bool: True if booking successful
        """
        try:
            logger.info(f"Booking appointment: {appointment['time']} with {appointment['doctor']}")
            
            # Click book button on the appointment slot
            book_button = await appointment['element'].query_selector(LeumitSelectors.BOOK_BUTTON)
            if book_button:
                await book_button.click()
            else:
                logger.error("Book button not found")
                return False
            
            # Wait for confirmation dialog
            await self.page.wait_for_load_state("networkidle")
            await self.take_screenshot("booking_confirmation")
            
            # Confirm booking
            await self.page.click(LeumitSelectors.CONFIRM_BUTTON)
            await self.page.wait_for_load_state("networkidle")
            
            # Check for success message
            success_element = await self.page.query_selector(LeumitSelectors.SUCCESS_MESSAGE)
            if success_element:
                logger.info("Appointment booked successfully!")
                await self.take_screenshot("booking_success")
                return True
            else:
                logger.warning("Could not confirm booking success")
                await self.take_screenshot("booking_uncertain")
                return False
                
        except Exception as e:
            logger.error(f"Error booking appointment: {e}")
            await self.take_screenshot("booking_error")
            return False
