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
            
            # Wait for popup animation and iframe to load
            logger.info("Waiting for login popup and iframe to load...")
            await asyncio.sleep(5)  # Increased to 5 seconds
            await self.page.wait_for_load_state("networkidle")
            
            # Take screenshot of login page
            await self.take_screenshot("login_page_before_input")
            
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
            
            # Switch to SMS/OTP login mode (left toggle button)
            logger.info("Switching to SMS/OTP login mode...")
            sms_toggle_selectors = [
                "button:has-text('SMS')",
                "button:has-text('קוד')",
                "div.custom-radio-btns input[type='radio'][value='1'] + label",
                "#divLoginWithOtpStepOneNew div.custom-radio-btns label:first-of-type"
            ]
            
            for selector in sms_toggle_selectors:
                try:
                    if await login_frame.locator(selector).count() > 0:
                        logger.info(f"Found SMS toggle with selector: {selector}")
                        await login_frame.click(selector)
                        await asyncio.sleep(1)
                        await self.take_screenshot("after_toggle_to_sms")
                        break
                except Exception as e:
                    logger.debug(f"Toggle selector {selector} failed: {e}")
            
            # Wait a bit more for iframe to be fully interactive
            await asyncio.sleep(1)
            
            # Fill ID (Teudat Zehut) - with explicit click first
            logger.info("Entering ID number...")
            user_id = self.credentials.get_leumit_id()
            await id_input.click()  # Click to focus
            await asyncio.sleep(0.5)
            await id_input.fill(user_id, force=True)  # Force fill
            await self.take_screenshot("after_id_fill")
            
            # Fill mobile number - with explicit click first
            logger.info("Entering mobile number...")
            mobile = self.credentials.get_leumit_mobile()
            await mobile_input.click()  # Click to focus
            await asyncio.sleep(0.5)
            await mobile_input.fill(mobile, force=True)  # Force fill
            await self.take_screenshot("after_mobile_fill")
            
            # Click login button - use the same frame
            logger.info("Clicking send OTP button...")
            await self.take_screenshot("before_clicking_submit")
            
            # Use exact button ID
            submit_button = login_frame.locator("#ButtonSendCellPhoneNew")
            
            if await submit_button.count() == 0:
                logger.error("Could not find submit button #ButtonSendCellPhoneNew")
                await self.take_screenshot("submit_button_not_found")
                return False
            
            logger.info("Found submit button, clicking...")
            await submit_button.click()
            
            # Wait for response and OTP screen
            await asyncio.sleep(2)
            await self.take_screenshot("after_submit_button")
            
            # Wait for user to enter OTP code manually
            logger.info("=" * 60)
            logger.info("OTP CODE ENTRY - MANUAL STEP REQUIRED")
            logger.info("A verification code should be sent to your phone.")
            logger.info("Please enter the OTP code in the browser manually.")
            logger.info("Press ENTER here once you've submitted the OTP code...")
            logger.info("=" * 60)
            input()  # Wait for user to press Enter
            
            logger.info("User confirmed OTP entry - checking login status...")
            await asyncio.sleep(2)
            
            # Wait for navigation after login
            await self.page.wait_for_load_state("networkidle")
            await self.take_screenshot("after_login")
            
            # Check if login was successful - look for profile/main page elements
            current_url = self.page.url
            logger.info(f"Current URL after OTP: {current_url}")
            
            # Check for appointment button or profile elements as success indicator
            success_indicators = [
                "#ctl00_LinkButton3",  # Appointments button
                "a:has-text('זימון תורים')",
                "text=תיק הבריאות שלי"  # My health file
            ]
            
            logged_in = False
            for indicator in success_indicators:
                if await self.page.locator(indicator).count() > 0:
                    logger.info(f"Found success indicator: {indicator}")
                    logged_in = True
                    break
            
            if logged_in:
                logger.info("Login successful!")
                return True
            else:
                logger.error("Login failed - could not find profile page indicators")
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
            
            # Try multiple selectors for the appointments button
            selectors = [
                "#ctl00_LinkButton3",
                "a:has-text('זימון תורים')",
                "xpath=/html/body/form/div[3]/div[2]/div[1]/div[2]/ul/li[2]/a"
            ]
            
            clicked = False
            for selector in selectors:
                try:
                    if await self.page.locator(selector).count() > 0:
                        logger.info(f"Found appointments button with: {selector}")
                        await self.page.click(selector)
                        clicked = True
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
            
            if not clicked:
                logger.error("Could not find appointments button")
                await self.take_screenshot("appointments_button_not_found")
                return False
            
            await self.page.wait_for_load_state("networkidle")
            await self.take_screenshot("appointments_page")
            
            logger.info("Successfully navigated to appointments")
            
            # Wait for user to inspect
            logger.info("=" * 60)
            logger.info("Arrived at appointments page")
            logger.info("Please inspect the page and identify next steps")
            logger.info("Press ENTER to continue...")
            logger.info("=" * 60)
            input()
            
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
