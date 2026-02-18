"""Browser automation logic using Playwright."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.async_api import async_playwright, Browser, Page, TimeoutError

from config.settings import (
    LEUMIT_HOME_URL,
    LEUMIT_ACCOUNT_PAGE,
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
        self.context = None  # For persistent context
        self.playwright = None
        self.credentials = Credentials()
        self.using_existing_browser = False
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self):
        """Initialize browser and create new page.
        
        Uses your existing Chrome profile with authentication.
        Connects to the same Chrome instance you're logged into.
        """
        logger.info("Starting browser connection...")
        self.playwright = await async_playwright().start()
        
        # Use Chrome with your actual profile (not a fresh profile)
        chrome_executable = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        chrome_user_data = "C:\\Users\\smogb\\AppData\\Local\\Google\\Chrome\\User Data"
        
        logger.info(f"Launching Chrome from: {chrome_executable}")
        logger.info(f"Using profile: {chrome_user_data}")
        
        # Use launch_persistent_context to use existing user data directory
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=chrome_user_data,
            executable_path=chrome_executable,
            headless=False,
            args=[
                '--start-maximized',
                '--disable-popup-blocking',
                '--disable-blink-features=AutomationControlled'
            ]
        )
        
        self.page = await self.context.new_page()
        self.page.set_default_timeout(BROWSER_TIMEOUT)
        logger.info("Browser started successfully")
        
        # Navigate directly to the account page
        logger.info("Navigating to Leumit account page...")
        await self.page.goto(LEUMIT_ACCOUNT_PAGE)
        await self.page.wait_for_load_state("networkidle")
        await asyncio.sleep(1)
        logger.info("Page loaded")

    
    async def close(self):
        """Close browser and cleanup."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
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
            # If using existing browser, skip login - already authenticated
            if self.using_existing_browser:
                logger.info("Using existing authenticated browser session - skipping login")
                return True
            
            # First, try to navigate directly to account page to check if already logged in
            logger.info(f"Checking if already logged in by navigating to: {LEUMIT_ACCOUNT_PAGE}")
            await self.page.goto(LEUMIT_ACCOUNT_PAGE)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(2)  # Wait for any redirects
            await self.take_screenshot("initial_check")
            
            # Check if we're already logged in by looking for the appointments button
            if await self.page.locator("#ctl00_LinkButton3").count() > 0:
                logger.info("Already logged in! No need to login again.")
                return True
            
            # Check if we see login boxes (means we need to login)
            if await self.page.locator("#TextBoxIdNumForOTP").count() > 0:
                logger.info("Login required - found login form")
            else:
                # Maybe in iframe, check all frames
                for frame in self.page.frames:
                    if await frame.locator("#TextBoxIdNumForOTP").count() > 0:
                        logger.info("Login required - found login form in iframe")
                        break
                else:
                    # Neither logged in nor login form found - navigate to home
                    logger.info("Navigating to Leumit home page...")
                    await self.page.goto(LEUMIT_HOME_URL)
                    await self.page.wait_for_load_state("networkidle")
            
            # Continue with login process
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
            logger.info("The browser will stay open for 120 seconds (2 minutes)...")
            logger.info("=" * 60)
            
            # Wait 120 seconds (2 minutes) for user to enter OTP manually
            logger.info("Waiting 120 seconds for OTP entry...")
            await asyncio.sleep(120)
            
            logger.info("Checking login status...")
            await asyncio.sleep(2)
            
            # Wait for navigation after login
            await self.page.wait_for_load_state("networkidle")
            screenshot_path = await self.take_screenshot("after_login")
            
            # Check if login was successful - look for profile/main page elements
            current_url = self.page.url
            logger.info(f"Current URL after OTP: {current_url}")
            
            # Try vision-based verification if available
            try:
                from ai.vision_agent import VisionAgent
                vision = VisionAgent()
                
                if vision.client:
                    logger.info("Using AI vision to verify login success...")
                    verification_prompt = """
                    Look at this screenshot and determine if it shows a successfully logged-in 
                    Leumit health portal page. Look for:
                    - Patient/user name or ID
                    - Navigation menu with health-related options
                    - "זימון תורים" (appointment scheduling) button
                    - Personal health information
                    
                    Reply with ONLY "SUCCESS" if logged in, or "FAILED" if still on login page or error.
                    """
                    
                    result = await vision.analyze_page(screenshot_path, verification_prompt)
                    if result and "SUCCESS" in result.upper():
                        logger.info("Vision AI confirmed successful login!")
                        return True
                    elif result and "FAILED" in result.upper():
                        logger.error("Vision AI detected login failure")
                        return False
            except Exception as e:
                logger.warning(f"Vision verification not available: {e}")
            
            # Fallback to element-based detection
            logger.info("Using element detection to verify login...")
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
            
            # Click "בצע חיפוש חדש" (New Search) button
            logger.info("Step 1: Clicking new search button...")
            try:
                await self.page.click(LeumitSelectors.NEW_SEARCH_BUTTON)
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)
                await self.take_screenshot("01_new_search_clicked")
                logger.info("New search button clicked successfully")
            except Exception as e:
                logger.warning(f"Could not click new search button: {e}")
                await self.take_screenshot("01_new_search_button_error")
            
            # Click "רופאים ומטפלים" (Doctors and Therapists) button
            logger.info("Step 2: Clicking doctors and therapists button...")
            try:
                await self.page.click(LeumitSelectors.DOCTORS_THERAPISTS_BUTTON)
                await self.page.wait_for_load_state("networkidle")
                await asyncio.sleep(1)
                await self.take_screenshot("02_doctors_clicked")
                logger.info("Doctors and therapists button clicked successfully")
            except Exception as e:
                logger.warning(f"Could not click doctors button: {e}")
                await self.take_screenshot("02_doctors_button_error")
            
            # Fill search form
            logger.info("Step 3: Filling search form...")
            
            # Fill doctor/specialty search
            if doctor_name:
                try:
                    await self.page.fill(LeumitSelectors.SEARCH_DOCTOR_INPUT, doctor_name)
                    await self.take_screenshot("03_doctor_filled")
                    logger.info(f"Entered doctor name: {doctor_name}")
                except Exception as e:
                    logger.warning(f"Could not fill doctor input: {e}")
            
            # Click search/submit button
            logger.info("Step 4: Clicking search button...")
            try:
                await self.page.click(LeumitSelectors.SEARCH_BUTTON)
                await self.page.wait_for_load_state("networkidle")
                await self.take_screenshot("04_search_submitted")
                logger.info("Search submitted successfully")
            except Exception as e:
                logger.warning(f"Could not click search button: {e}")
                await self.take_screenshot("04_search_button_error")
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
