"""
Persistent Leumit agent - stays running with browser session alive.
Supports both file-based commands (commands.json) and socket-based commands.
"""
import asyncio
import json
import logging
import os
import sys
import signal
import traceback
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from otp_listener import OTPListener

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright

LOGS_DIR = Path(__file__).parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Create unique log file per run: persistent_agent_<PID>_<HH-mm>.log
import os
pid = os.getpid()
time_str = datetime.now().strftime("%H-%m")
LOG_FILE = LOGS_DIR / f"persistent_agent_{pid}_{time_str}.log"

# Configure logging with a console-only Hebrew mapping
HEBREW_CONSOLE_MAP = {
    "ברגעים אלה נשלחת אליך הודעת": "bergaim ele nishleha eleycha hodaat",
    "אנא לחץ על הקישור והזין מספר ת": "ana lehatz al hakishur vehazen mispar TZ",
    "בצע חיפוש חדש": "batza hipus hadash",
    "רופאים ומטפלים": "rofim vemetaplim",
    "זמן לוידאו": "zamen levideo",
    "זמן לטלפון": "zamen letelefon",
    "זמן למרפאה": "zamen lemirpaa",
    "זימון תורים": "zimun torim",
    "אזור אישי": "ezor ishi",
    "זמן תור": "zamen tor",
    "שמור וסיים": "shmor vesayem",
    "לאומית": "leumit",
    "חפש": "hapes",
    "שלח": "shlah",
    "המשך": "hanshech",
    "ז": "Z",
    "ת": "T",
}


class ConsoleSafeFormatter(logging.Formatter):
    def __init__(self, fmt: str, mapping: dict[str, str]):
        super().__init__(fmt)
        self._mapping = sorted(mapping.items(), key=lambda item: len(item[0]), reverse=True)

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for hebrew, replacement in self._mapping:
            message = message.replace(hebrew, replacement)
        return message.encode("cp1252", errors="replace").decode("cp1252")


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.propagate = False

file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
file_handler.setFormatter(logging.Formatter("%(asctime)s - %(message)s"))

console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(ConsoleSafeFormatter("%(asctime)s - %(message)s", HEBREW_CONSOLE_MAP))

logger.handlers = [file_handler, console_handler]

load_dotenv()

LEUMIT_ID = os.getenv("LEUMIT_ID")
LEUMIT_MOBILE = os.getenv("LEUMIT_MOBILE")
COMMANDS_FILE = Path(__file__).parent / "commands.json"
STATE_FILE = Path(__file__).parent / "agent_state.json"
SOCKET_HOST = "localhost"
SOCKET_PORT = 5556


class PersistentAgent:
    """Persistent browser agent that executes commands."""
    
    def __init__(self):
        self.page = None
        self.browser = None
        self.playwright = None
        self.logged_in = False
        self.last_command_hash = None
        self.last_file_mtime = None
        self.socket_server = None
        self.debug_mode = os.getenv("AGENT_DEBUG", "0") == "1"
    
    async def setup(self):
        """Initialize browser."""
        logger.info("=" * 60)
        logger.info("PERSISTENT LEUMIT AGENT - STARTING")
        logger.info("=" * 60)
        logger.info("")
        
        self.playwright = await async_playwright().start()
        
        # Use persistent context to save cookies/session across restarts
        user_data_dir = Path(__file__).parent / ".browser_profile"
        user_data_dir.mkdir(exist_ok=True)
        
        context = None
        lock_files = ["SingletonLock", "SingletonCookie", "SingletonSocket", "lockfile"]
        for attempt in range(1, 3):
            try:
                context = await self.playwright.chromium.launch_persistent_context(
                    str(user_data_dir),
                    headless=False,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--start-maximized",
                    ]
                )
                break
            except Exception as e:
                if "Target" in str(e) or "closed" in str(e):
                    logger.error("Browser profile locked! Attempting to clear stale lock files...")
                    removed = []
                    for name in lock_files:
                        lock_path = user_data_dir / name
                        if lock_path.exists():
                            try:
                                lock_path.unlink()
                                removed.append(name)
                            except Exception:
                                pass
                    if removed:
                        logger.info(f"Removed lock files: {', '.join(removed)}")
                    if attempt < 2:
                        await asyncio.sleep(1)
                        continue
                    logger.error("Browser profile still locked. Close existing browser windows or delete .browser_profile/")
                    logger.error(f"Error: {e}")
                    raise
                else:
                    raise

        if context is None:
            raise RuntimeError("Failed to launch browser context")
        
        # Get or create first page
        if len(context.pages) > 0:
            self.page = context.pages[0]
        else:
            self.page = await context.new_page()
        
        self.browser = context  # Store context as browser for compatibility
        
        # Load state from file
        try:
            if STATE_FILE.exists():
                with open(STATE_FILE, "r", encoding='utf-8') as f:
                    state = json.load(f)
                    self.logged_in = state.get("logged_in", False)
                    if self.logged_in:
                        logger.info("✓ Loaded session state: logged_in=True")
        except Exception as e:
            logger.warning(f"Could not load state file: {e}")
        
        logger.info("✓ Browser initialized")
        logger.info("")
    
    async def login_to_leumit(self):
        """Complete login flow following the documented workflow."""
        logger.info("=" * 60)
        logger.info("LOGIN FLOW")
        logger.info("=" * 60)
        logger.info("")
        
        try:
            # Step 1: Navigate to Google
            logger.info("Step 1: Navigating to Google...")
            await self.page.goto("https://www.google.com", wait_until="domcontentloaded")
            await asyncio.sleep(1)
            
            # Step 2: Search for Leumit
            logger.info("Step 2: Searching for 'לאומית'...")
            await self.page.fill("textarea[name='q'], input[name='q']", "לאומית")
            await self.page.click("input[name='btnK']")
            await asyncio.sleep(3)
            
            # Step 3: Click Leumit link
            logger.info("Step 3: Clicking Leumit link...")
            await self.page.click("a[href*='leumit.co.il']")
            await asyncio.sleep(5)  # Wait for homepage to load
            
            # Step 4: Check login state per workflow
            logger.info("Step 4: Checking login state...")
            
            # Check for "אזור אישי" (not logged in)
            azor_ishi_found = False
            zimun_torim_found = False
            
            try:
                await self.page.get_by_text("אזור אישי").first.wait_for(timeout=3000, state="visible")
                azor_ishi_found = True
                logger.info("  ✓ Found 'אזור אישי' button → NOT logged in")
            except:
                pass
            
            # Check for "זימון תורים" (logged in)
            if not azor_ishi_found:
                try:
                    await self.page.get_by_text("זימון תורים").first.wait_for(timeout=3000, state="visible")
                    zimun_torim_found = True
                    logger.info("  ✓ Found 'זימון תורים' button → Already logged in!")
                    self.logged_in = True
                    return True
                except:
                    pass
            
            # If neither found, trigger error
            if not azor_ishi_found and not zimun_torim_found:
                logger.error("  ✗ Neither 'אזור אישי' nor 'זימון תורים' found!")
                logger.error("  → Unexpected state - cannot proceed with login")
                return False
            
            # If we found "אזור אישי", proceed with login
            logger.info("Step 5: Clicking 'אזור אישי' button...")
            try:
                await self.page.get_by_text("אזור אישי").first.click()
            except:
                logger.warning("Could not click via text, trying selector...")
                await self.page.click("button:has-text('אזור אישי'), a:has-text('אזור אישי')")
            
            await asyncio.sleep(8)  # Wait for page to respond
            
            # After clicking, check if we're now logged in (button appeared) or need to login
            logger.info("Step 6: Checking if login modal appeared or already logged in...")
            try:
                await self.page.get_by_text("זימון תורים").first.wait_for(timeout=3000, state="visible")
                logger.info("  ✓ Found 'זימון תורים' → Already logged in after clicking!")
                self.logged_in = True
                return True
            except:
                logger.info("  → 'זימון תורים' not found, proceeding with login form...")
            
            # Find and fill login form
            logger.info("Step 7: Looking for login form...")
            
            # Wait for the form to be visible
            await self.page.wait_for_selector("[id*='fecd8561']", timeout=5000)
            
            # Get all frames
            frames = self.page.frames
            login_frame = None
            
            for frame in frames:
                if "LoginForHomepageNew" in frame.url:
                    login_frame = frame
                    logger.info(f"✓ Found login frame: {frame.url}")
                    break
            
            if not login_frame:
                logger.error("Login frame not found!")
                return False
            
            # Wait a bit more for frame to be interactive
            await asyncio.sleep(2)
            
            # Try to find inputs in the frame using known field IDs
            try:
                logger.info("Looking for login form fields...")
                
                # These are the actual field IDs from the Leumit form
                id_input = await login_frame.query_selector("#TextBoxIdNumForOTP")
                phone_input = await login_frame.query_selector("#TextBoxCellphone")
                
                if id_input and phone_input:
                    logger.info("✓ Found both input fields")
                    logger.info(f"  Filling ID field...")
                    await id_input.fill(LEUMIT_ID)
                    logger.info(f"  ✓ ID entered: {LEUMIT_ID}")
                    
                    logger.info(f"  Filling phone field...")
                    await phone_input.fill(LEUMIT_MOBILE)
                    logger.info(f"  ✓ Phone entered: {LEUMIT_MOBILE}")
                else:
                    logger.error("Could not find required input fields")
                    logger.info("Available text input fields:")
                    inputs = await login_frame.query_selector_all("input[type='text']")
                    for i, inp in enumerate(inputs[:5]):
                        inp_id = await inp.get_attribute("id")
                        logger.info(f"  {i}: id={inp_id}")
                    return False
                    
            except Exception as e:
                logger.error(f"Error filling form: {e}")
                import traceback
                traceback.print_exc()
                return False
            
            # Take screenshot
            screenshot_path = Path(__file__).parent / "screenshots" / "login_form_filled.png"
            screenshot_path.parent.mkdir(exist_ok=True)
            await self.page.screenshot(path=str(screenshot_path))
            logger.info(f"✓ Screenshot: {screenshot_path}")
            
            # Now click the submit button (שלח)
            logger.info("Clicking 'שלח' button...")
            try:
                await login_frame.get_by_text("שלח").first.click(timeout=3000)
                logger.info("✓ Submit button clicked")
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Could not click שלח button via text: {e}")
                # Try clicking by selector
                try:
                    submit_btn = await login_frame.query_selector("input[type='submit'], button[type='submit']")
                    if submit_btn:
                        await submit_btn.click()
                        logger.info("✓ Submit button clicked")
                        await asyncio.sleep(2)
                except:
                    logger.warning("Could not find submit button")
            
            # Before waiting for OTP, check one more time if we're already logged in
            logger.info("Checking if already logged in before OTP wait...")
            try:
                await self.page.get_by_text("זימון תורים").first.wait_for(timeout=3000, state="visible")
                logger.info("  ✓ Found 'זימון תורים' → Already logged in!")
                self.logged_in = True
                return True
            except:
                logger.info("  → Not logged in yet, need OTP verification")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("⏳ WAITING FOR OTP VERIFICATION")
            logger.info("=" * 60)
            logger.info("Waiting for OTP code from phone notifications...")
            logger.info("Agent will auto-fill OTP when received.")
            logger.info("")
            # Start OTP listener
            otp_listener = OTPListener()
            otp_listener.start()
            max_wait = 300  # 5 minutes
            waited = 0
            check_interval = 2
            otp_code = None
            while waited < max_wait:
                # Try to get OTP from listener
                otp_code = otp_listener.get_latest_otp(timeout=check_interval)
                waited += check_interval
                if otp_code:
                    logger.info(f"✓ OTP code received: {otp_code}")
                    # Re-find login frame as it may have been detached
                    try:
                        # Wait a bit for OTP field to appear
                        await asyncio.sleep(1)
                        
                        # Find the login frame again
                        frames = self.page.frames
                        current_login_frame = None
                        for frame in frames:
                            if "LoginForHomepageNew" in frame.url:
                                current_login_frame = frame
                                logger.info(f"  Found login frame: {frame.url}")
                                break
                        
                        if not current_login_frame:
                            logger.warning("Login frame not found, trying main page")
                            current_login_frame = self.page
                        
                        # Try multiple selectors for OTP input
                        otp_input = None
                        otp_selectors = [
                            "#TextBoxOTP",
                            "input[type='text'][id*='OTP']",
                            "input[type='text'][name*='OTP']",
                            "input[placeholder*='קוד']",
                        ]
                        
                        for selector in otp_selectors:
                            try:
                                otp_input = await current_login_frame.query_selector(selector)
                                if otp_input:
                                    logger.info(f"  Found OTP input with selector: {selector}")
                                    break
                            except:
                                pass
                        
                        if otp_input:
                            await otp_input.fill(otp_code)
                            logger.info("✓ OTP field filled")
                            # Submit OTP - try multiple button selectors
                            submit_btn = None
                            submit_selectors = [
                                "span.button_text:has-text('כניסה למערכת')",
                                "span:has-text('כניסה למערכת')",
                                "input[type='submit']",
                                "button[type='submit']",
                            ]
                            
                            for selector in submit_selectors:
                                try:
                                    submit_btn = await current_login_frame.query_selector(selector)
                                    if submit_btn:
                                        logger.info(f"  Found submit button with selector: {selector}")
                                        break
                                except:
                                    pass
                            
                            if submit_btn:
                                await submit_btn.click()
                                logger.info("✓ OTP submit button clicked")
                            else:
                                logger.warning("OTP submit button not found!")
                        else:
                            logger.warning("OTP input field not found with any selector!")
                            # Log available input fields for debugging
                            inputs = await current_login_frame.query_selector_all("input[type='text']")
                            logger.info(f"  Available text inputs: {len(inputs)}")
                            for i, inp in enumerate(inputs[:5]):
                                inp_id = await inp.get_attribute("id")
                                inp_name = await inp.get_attribute("name")
                                inp_placeholder = await inp.get_attribute("placeholder")
                                logger.info(f"    [{i}] id={inp_id}, name={inp_name}, placeholder={inp_placeholder}")
                    except Exception as e:
                        logger.error(f"Error auto-filling OTP: {e}")
                    # Wait for login to complete
                    await asyncio.sleep(5)
                    try:
                        await self.page.get_by_text("זימון תורים").first.wait_for(timeout=3000, state="visible")
                        logger.info(f"✓ Login successful! Found 'זימון תורים' button")
                        self.logged_in = True
                        logger.info("")
                        otp_listener.stop()
                        return True
                    except:
                        logger.info("Waiting for login completion after OTP...")
                else:
                    # Check if already logged in (in case OTP was auto-processed)
                    try:
                        await self.page.get_by_text("זימון תורים").first.wait_for(timeout=1000, state="visible")
                        logger.info(f"✓ Login successful! Found 'זימון תורים' button")
                        self.logged_in = True
                        logger.info("")
                        otp_listener.stop()
                        return True
                    except:
                        pass
                if waited % 30 == 0:
                    logger.info(f"Still waiting for OTP... ({waited}s / {max_wait}s)")
            otp_listener.stop()
            logger.error("Login timeout - OTP not verified in time")
            return False
        except Exception as e:
            logger.error(f"Error in login flow: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_command(self) -> dict:
        """Load command from file."""
        logger.info(f"DEBUG: Looking for commands file at: {COMMANDS_FILE}")
        logger.info(f"DEBUG: File exists: {COMMANDS_FILE.exists()}")
        if not COMMANDS_FILE.exists():
            return None
        
        try:
            with open(COMMANDS_FILE, encoding='utf-8') as f:
                cmd = json.load(f)
                # Log only the action, not the full command (which may contain Hebrew chars)
                action = cmd.get('action', 'unknown')
                logger.info(f"DEBUG: Loaded command: {action}")
                return cmd
        except Exception as e:
            logger.error(f"DEBUG: Error loading command: {e}")
            return None
    
    def save_state(self, state: dict):
        """Save agent state."""
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def get_command_hash(self, cmd: dict) -> str:
        """Get hash of command to detect changes."""
        return hash(json.dumps(cmd, sort_keys=True)).__str__()
    
    async def handle_socket_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle incoming socket command."""
        addr = writer.get_extra_info('peername')
        logger.info(f"Socket connection from {addr}")
        
        try:
            # Read command (expect JSON followed by newline)
            data = await reader.readline()
            if not data:
                return
            
            cmd_str = data.decode().strip()
            cmd = json.loads(cmd_str)
            logger.info(f"Received socket command: {cmd.get('action')}")
            
            # Execute command
            if cmd.get("action") == "login":
                success = await self.login_to_leumit()
                result = {"status": "success" if success else "error", "logged_in": success}
            else:
                if not self.logged_in:
                    result = {"status": "error", "message": "Not logged in"}
                else:
                    result = await self.execute_command(cmd)
            
            # Send response
            response = json.dumps(result) + "\n"
            writer.write(response.encode())
            await writer.drain()
            logger.info(f"Sent response: {result.get('status')}")
            
        except Exception as e:
            logger.error(f"Socket handler error: {e}")
            error_response = json.dumps({"status": "error", "message": str(e)}) + "\n"
            writer.write(error_response.encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def start_socket_server(self):
        """Start TCP socket server."""
        server = await asyncio.start_server(
            self.handle_socket_client,
            SOCKET_HOST,
            SOCKET_PORT
        )
        self.socket_server = server
        logger.info(f"✓ Socket server listening on {SOCKET_HOST}:{SOCKET_PORT}")
        return server
    
    async def execute_command(self, cmd: dict) -> dict:
        """Execute a command."""
        action = cmd.get("action")
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"COMMAND: {action}")
        logger.info("=" * 60)
        logger.info(f"Params: {cmd.get('params', {})}")
        logger.info("")
        
        try:
            # Log that we're processing the command
            logger.info(f"Executing action: {action}")
            
            if action == "navigate":
                url = cmd["params"]["url"]
                logger.info(f"Navigating to: {url}")
                await self.page.goto(url, wait_until="domcontentloaded")
                return {"status": "success", "url": self.page.url}
            
            elif action == "wait":
                seconds = cmd["params"].get("seconds", 5)
                logger.info(f"Waiting {seconds} seconds...")
                await asyncio.sleep(seconds)
                return {"status": "success"}
            
            elif action == "screenshot":
                path = cmd["params"].get("path", "screenshot.png")
                full_path = Path(__file__).parent / path
                full_path.parent.mkdir(exist_ok=True)
                await self.page.screenshot(path=str(full_path))
                logger.info(f"Screenshot: {full_path}")
                return {"status": "success", "path": str(full_path)}
            
            elif action == "get_url":
                url = self.page.url
                logger.info(f"Current URL: {url}")
                return {"status": "success", "url": url}
            
            elif action == "search_doctor":
                # Search for doctor by specialty and name
                specialty = cmd["params"].get("specialty")
                doctor_name = cmd["params"].get("doctor_name")
                subcategory = cmd["params"].get("subcategory", "כל תתי התחומים")
                date_from = cmd["params"].get("date_from")  # Optional: filter by date
                date_to = cmd["params"].get("date_to")      # Optional: filter by date
                
                logger.info(f"Starting doctor search:")
                logger.info(f"  Specialty: {specialty}")
                logger.info(f"  Doctor: {doctor_name}")
                logger.info(f"  Date range: {date_from} to {date_to}")
                
                # Step 0: Check if we're logged in by looking for the "זימון תורים" button
                logger.info("Step 0: Checking login state...")
                try:
                    # Quick check if button exists (3 second timeout)
                    await self.page.get_by_text("זימון תורים").first.wait_for(timeout=3000, state="visible")
                    logger.info("  ✓ Already logged in - 'זימון תורים' button found")
                    self.logged_in = True
                except:
                    logger.info("  ✗ Not logged in - 'זימון תורים' button not found")
                    logger.info("  → Need to perform login before continuing")
                    
                    # Return error asking for login
                    return {
                        "status": "error",
                        "message": "Not logged in. Please send login command first: {\"action\": \"login\"}",
                        "requires_login": True
                    }
                
                # Navigate to appointments section
                logger.info("Step 1: Click 'זימון תורים'")
                try:
                    await self.page.get_by_text("זימון תורים").first.click(timeout=30000)
                    await asyncio.sleep(3)  # Wait for page transition
                    logger.info("  ✓ Clicked 'זימון תורים'")
                    
                    # Take screenshot after clicking
                    screenshot_path = Path(__file__).parent / "screenshots" / f"after_zimon_torim_{datetime.now().strftime('%H%M%S')}.png"
                    screenshot_path.parent.mkdir(exist_ok=True)
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.info(f"  📸 Screenshot: {screenshot_path.name}")
                    
                except Exception as e:
                    logger.error(f"  ✗ Failed to click 'זימון תורים': {e}")
                    return {"status": "error", "message": f"Failed to click appointments button: {e}"}
                
                logger.info("Step 2: Click 'בצע חיפוש חדש'")
                
                # Try multiple selector strategies for the button
                clicked = False
                strategies = [
                    ("onclick", lambda: self.page.locator("div.appointments_large_button_text[onclick='newSearch()']")),
                    ("text_in_div", lambda: self.page.locator("div.appointments_large_button_text:has-text('בצע חיפוש חדש')")),
                    ("parent_div", lambda: self.page.locator("div.appointments_large_button:has-text('בצע חיפוש חדש')")),
                    ("text", lambda: self.page.get_by_text("בצע חיפוש חדש", exact=False).first),
                ]
                
                for strategy_name, selector_fn in strategies:
                    try:
                        logger.info(f"  → Trying strategy: {strategy_name}")
                        element = selector_fn()
                        await element.wait_for(timeout=5000, state="visible")
                        await element.click()
                        logger.info(f"  ✓ Clicked 'בצע חיפוש חדש' (strategy: {strategy_name})")
                        clicked = True
                        
                        # Take screenshot after clicking
                        screenshot_path = Path(__file__).parent / "screenshots" / f"after_new_search_{datetime.now().strftime('%H%M%S')}.png"
                        await self.page.screenshot(path=str(screenshot_path))
                        logger.info(f"  📸 Screenshot: {screenshot_path.name}")
                        break
                        
                    except Exception as e:
                        logger.debug(f"  ✗ Strategy '{strategy_name}' failed: {e}")
                        continue
                
                if not clicked:
                    logger.error(f"  ✗ All strategies failed to click 'בצע חיפוש חדש'")
                    
                    # Take error screenshot
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step2_error_{datetime.now().strftime('%H%M%S')}.png"
                    screenshot_path.parent.mkdir(exist_ok=True)
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.error(f"  📸 Error screenshot: {screenshot_path.name}")
                    
                    return {"status": "error", "message": "Failed to click בצע חיפוש חדש - all strategies exhausted"}
                
                # Wait for page to load after clicking new search - increased to 5 seconds
                logger.info("  → Waiting for search page to load...")
                await asyncio.sleep(5)  # Give page more time to fully render
                
                logger.info("Step 3: Click 'רופאים ומטפלים'")
                
                # Try multiple selector strategies
                clicked = False
                strategies = [
                    ("text", lambda: self.page.get_by_text("רופאים ומטפלים", exact=False).first),
                    ("radio", lambda: self.page.locator("input[type='radio'][value*='doctor'], input[type='radio'][value*='Doctor']").first),
                    ("label", lambda: self.page.locator("label:has-text('רופאים ומטפלים')").first),
                    ("contains", lambda: self.page.locator("*:has-text('רופאים ומטפלים')").first),
                ]
                
                for strategy_name, selector_fn in strategies:
                    try:
                        logger.info(f"  → Trying strategy: {strategy_name}")
                        element = selector_fn()
                        await element.wait_for(timeout=5000, state="visible")
                        await element.click()
                        await asyncio.sleep(2)
                        logger.info(f"  ✓ Clicked 'רופאים ומטפלים' (strategy: {strategy_name})")
                        clicked = True
                        break
                    except Exception as e:
                        logger.debug(f"  ✗ Strategy '{strategy_name}' failed: {e}")
                        continue
                
                if not clicked:
                    logger.error(f"  ✗ All strategies failed to click 'רופאים ומטפלים'")
                    
                    # Take screenshot to see current state
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step3_error_{datetime.now().strftime('%H%M%S')}.png"
                    screenshot_path.parent.mkdir(exist_ok=True)
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.error(f"  📸 Error screenshot: {screenshot_path.name}")
                    return {"status": "error", "message": "Failed to click רופאים ומטפלים - all strategies exhausted"}
                
                # Select specialty
                logger.info(f"Step 4: Select specialty '{specialty}'")
                specialty_selected = False
                
                # Select2 autocomplete field - need to type and select from dropdown
                specialty_strategies = [
                    ("select2_input", "input.select2-input"),
                    ("select2_search", "input.select2-search-field"),
                    ("placeholder_search", "input[placeholder*='חיפוש'], input[placeholder*='תחום']"),
                ]
                
                for strategy_name, selector in specialty_strategies:
                    try:
                        logger.info(f"  → Trying strategy: {strategy_name}")
                        
                        # Find and click the input field
                        input_field = self.page.locator(selector).first
                        await input_field.wait_for(timeout=5000, state="visible")
                        await input_field.click()
                        await asyncio.sleep(0.5)
                        
                        # Type the specialty name
                        await input_field.fill(specialty)
                        await asyncio.sleep(1)  # Wait for dropdown to appear
                        logger.info(f"  ✓ Typed '{specialty}' in search field")
                        
                        # Wait for and click the dropdown option
                        # Select2 creates li elements with the results
                        dropdown_option = self.page.locator(f"li.select2-result:has-text('{specialty}')").first
                        await dropdown_option.wait_for(timeout=5000, state="visible")
                        await dropdown_option.click()
                        await asyncio.sleep(2)
                        
                        logger.info(f"  ✓ Selected specialty '{specialty}' from dropdown (strategy: {strategy_name})")
                        specialty_selected = True
                        
                        # Take screenshot after selection
                        screenshot_path = Path(__file__).parent / "screenshots" / f"after_specialty_{datetime.now().strftime('%H%M%S')}.png"
                        await self.page.screenshot(path=str(screenshot_path))
                        logger.info(f"  📸 Screenshot: {screenshot_path.name}")
                        break
                        
                    except Exception as e:
                        logger.debug(f"  ✗ Strategy '{strategy_name}' failed: {e}")
                        continue
                
                if not specialty_selected:
                    logger.error(f"  ✗ Failed to select specialty '{specialty}'")
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step4_error_{datetime.now().strftime('%H%M%S')}.png"
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.error(f"  📸 Error screenshot: {screenshot_path.name}")
                    return {"status": "error", "message": f"Failed to select specialty: {specialty}"}
                
                # Select subcategory (also Select2 dropdown)
                logger.info(f"Step 5: Select subcategory '{subcategory}'")
                subcategory_selected = False
                
                subcategory_strategies = [
                    ("select2_input", lambda: self.page.locator("input.select2-input").nth(1)),  # Second Select2 input
                    ("visible_select2", lambda: self.page.locator("input.select2-input:visible").last),
                ]
                
                for strategy_name, locator_fn in subcategory_strategies:
                    try:
                        logger.debug(f"  Trying strategy: {strategy_name}")
                        input_field = locator_fn()
                        await input_field.wait_for(timeout=3000, state="visible")
                        
                        # Type subcategory text
                        await input_field.fill(subcategory)
                        await asyncio.sleep(1)  # Wait for dropdown to populate
                        
                        # Click matching option from dropdown
                        dropdown_option = self.page.locator(f"li.select2-result:has-text('{subcategory}')").first
                        await dropdown_option.wait_for(timeout=2000)
                        await dropdown_option.click()
                        
                        logger.info(f"  ✓ Selected subcategory '{subcategory}' using strategy: {strategy_name}")
                        subcategory_selected = True
                        
                        # Take screenshot after selection
                        screenshot_path = Path(__file__).parent / "screenshots" / f"after_subcategory_{datetime.now().strftime('%H%M%S')}.png"
                        await self.page.screenshot(path=str(screenshot_path))
                        logger.info(f"  📸 Screenshot: {screenshot_path.name}")
                        break
                        
                    except Exception as e:
                        logger.debug(f"  ✗ Strategy '{strategy_name}' failed: {e}")
                        continue
                
                if not subcategory_selected:
                    logger.warning(f"  → Could not select subcategory '{subcategory}' (might not be available)")
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step5_error_{datetime.now().strftime('%H%M%S')}.png"
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.warning(f"  📸 Error screenshot: {screenshot_path.name}")
                
                # Fill doctor name if provided
                if doctor_name:
                    logger.info(f"Step 6: Filter by doctor name '{doctor_name}'")
                    doctor_filled = False
                    
                    # Try multiple strategies to find and fill doctor name
                    doctor_strategies = [
                        ("placeholder", "input[placeholder*='שם רופא']"),
                        ("id_doctor", "input[id*='doctor'], input[id*='Doctor']"),
                        ("name_doctor", "input[name*='doctor'], input[name*='Doctor']"),
                        ("text_input", "input[type='text']"),
                    ]
                    
                    for strategy_name, selector in doctor_strategies:
                        try:
                            logger.info(f"  → Trying strategy: {strategy_name}")
                            doctor_input = self.page.locator(selector).first
                            await doctor_input.wait_for(timeout=3000, state="visible")
                            await doctor_input.fill(doctor_name)
                            await asyncio.sleep(1)
                            logger.info(f"  ✓ Doctor name '{doctor_name}' entered (strategy: {strategy_name})")
                            doctor_filled = True
                            
                            # Take screenshot after entering
                            screenshot_path = Path(__file__).parent / "screenshots" / f"after_doctor_name_{datetime.now().strftime('%H%M%S')}.png"
                            await self.page.screenshot(path=str(screenshot_path))
                            logger.info(f"  📸 Screenshot: {screenshot_path.name}")
                            break
                            
                        except Exception as e:
                            logger.debug(f"  ✗ Strategy '{strategy_name}' failed: {e}")
                            continue
                    
                    if not doctor_filled:
                        logger.warning("  ⚠ Could not find doctor name input field")
                        screenshot_path = Path(__file__).parent / "screenshots" / f"step6_error_{datetime.now().strftime('%H%M%S')}.png"
                        await self.page.screenshot(path=str(screenshot_path))
                        logger.warning(f"  📸 Error screenshot: {screenshot_path.name}")
                
                # Click search
                logger.info("Step 7: Click 'חפש'")
                await self.page.get_by_text("חפש").first.click()
                await asyncio.sleep(3)
                
                logger.info("✓ Search complete - results should be displayed")
                
                # Take screenshot of results
                screenshot_path = Path(__file__).parent / "screenshots" / "search_results.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                await self.page.screenshot(path=str(screenshot_path))
                logger.info(f"📸 Search results screenshot: {screenshot_path.name}")
                
                # Step 8: Click "זמן תור" button to book appointment
                logger.info("Step 8: Click 'זמן תור' button")
                zaman_button_clicked = False
                
                zaman_strategies = [
                    ("span_id", lambda: self.page.locator('span#ctl00_MainContentPlaceHolder_ucSearchResults_RepeaterDoctorsResults_ctl00_LabelButtonTextForMakingAppointment').first),
                    ("span_text", lambda: self.page.locator('span:has-text("זמן תור")').first),
                    ("parent_link", lambda: self.page.locator('a:has(span:has-text("זמן תור"))').first),
                    ("contains_text", lambda: self.page.get_by_text("זמן תור").first)
                ]
                
                for strategy_name, locator_fn in zaman_strategies:
                    try:
                        logger.debug(f"  Trying strategy: {strategy_name}")
                        element = locator_fn()
                        await element.wait_for(timeout=2000)
                        await element.click()
                        logger.info(f"  ✓ Clicked using strategy: {strategy_name}")
                        zaman_button_clicked = True
                        await asyncio.sleep(2)
                        
                        # Take screenshot after clicking
                        screenshot_path = Path(__file__).parent / "screenshots" / f"after_zaman_click_{datetime.now().strftime('%H%M%S')}.png"
                        await self.page.screenshot(path=str(screenshot_path))
                        logger.info(f"  📸 After click screenshot: {screenshot_path.name}")
                        break
                    except Exception as e:
                        logger.debug(f"  ✗ Strategy '{strategy_name}' failed: {e}")
                        continue
                
                if not zaman_button_clicked:
                    logger.warning("  ⚠ Could not click 'זמן תור' button")
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step8_error_{datetime.now().strftime('%H%M%S')}.png"
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.warning(f"  📸 Error screenshot: {screenshot_path.name}")
                    return {"status": "error", "message": "Failed to click זמן תור button"}
                
                # Step 16: Wait for Calendar Page
                logger.info("Step 16: Wait for Calendar Page (2 seconds)")
                await asyncio.sleep(2)
                
                # Step 17: VALIDATE DATE IN RANGE?
                logger.info("Step 17: VALIDATE DATE IN RANGE?")
                logger.info("  Reading pre-selected appointment from calendar...")
                # Step 17 (cont'd): Reading pre-selected appointment date from calendar
                from datetime import datetime as dt
                date_from = dt.strptime(cmd["params"].get("date_from", "2026-02-23"), "%Y-%m-%d")
                date_to = dt.strptime(cmd["params"].get("date_to", "2026-04-03"), "%Y-%m-%d")
                logger.info(f"  Date range to validate against: {date_from.strftime('%d.%m.%Y')} to {date_to.strftime('%d.%m.%Y')}")
                try:
                    selected_date_elem = self.page.locator("#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedDate")
                    selected_time_elem = self.page.locator("#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedTime")
                    
                    selected_date = await selected_date_elem.text_content() if await selected_date_elem.count() > 0 else "Unknown"
                    selected_time = await selected_time_elem.text_content() if await selected_time_elem.count() > 0 else "Unknown"
                    selected_date_str = selected_date.strip()
                    selected_time_str = selected_time.strip()
                    
                    logger.info(f"  ✓ Calendar shows: Date={selected_date_str}, Time={selected_time_str}")
                    
                except Exception as e:
                    logger.error(f"  ✗ Could not read selected date from calendar: {e}")
                    return {"status": "error", "message": f"Could not read calendar date: {e}"}
                
                # Step 9.4: Validate selected date is within requested boundaries
                logger.info("  Checking if selected date is within boundaries...")
                date_within_range = False
                try:
                    # Parse selected date: format is DD.MM.YY (e.g., "01.06.26")
                    parts = selected_date_str.split('.')
                    if len(parts) == 3:
                        day, month, year = parts
                        # Convert YY to YYYY
                        year_full = f"20{year}" if len(year) == 2 else year
                        selected_date_obj = dt.strptime(f"{day}.{month}.{year_full}", "%d.%m.%Y")
                        
                        # Check if date is within range
                        if selected_date_obj >= date_from and selected_date_obj <= date_to:
                            logger.info(f"  ✓ Selected date {selected_date_str} is WITHIN boundaries")
                            date_within_range = True
                        else:
                            logger.warning(f"  ✗ Selected date {selected_date_str} ({selected_date_obj.strftime('%d.%m.%Y')}) is OUTSIDE boundaries")
                            logger.warning(f"     Valid range: {date_from.strftime('%d.%m.%Y')} to {date_to.strftime('%d.%m.%Y')}")
                    else:
                        logger.error(f"  ✗ Could not parse date format: {selected_date_str}")
                except Exception as e:
                    logger.error(f"  ✗ Date parsing error: {e}")
                
                # BRANCH: Check if date is in range
                if not date_within_range:
                    # DATE IS OUTSIDE BOUNDARIES - Execute retry workflow
                    logger.warning("  " + "=" * 68)
                    logger.warning("  DATE OUT OF RANGE - Starting retry workflow")
                    logger.warning("  " + "=" * 68)
                    
                    # FALLBACK WORKFLOW: Step 100 - Step 105
                    logger.warning("")
                    logger.warning("=" * 70)
                    logger.warning("FALLBACK WORKFLOW TRIGGERED - DATE OUT OF RANGE")
                    logger.warning("=" * 70)
                    
                    # Step 100: Refresh page
                    logger.info("Step 100: Refresh page")
                    try:
                        await self.page.reload(wait_until="domcontentloaded")
                        logger.info("  ✓ Page refreshed successfully")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not refresh page: {e}")
                    
                    # Step 101: Take screenshot (post-refresh)
                    logger.info("Step 101: Take screenshot (post-refresh)")
                    try:
                        screenshot_path = Path(__file__).parent / "screenshots" / f"step101_after_refresh_{datetime.now().strftime('%H%M%S')}.png"
                        await self.page.screenshot(path=str(screenshot_path), full_page=True)
                        logger.info(f"  ✓ Screenshot: {screenshot_path.name}")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not take screenshot: {e}")
                    
                    # Step 102: Wait 15 minutes (900s)
                    logger.info("Step 102: Wait 15 minutes (900 seconds)")
                    logger.info("  💤 Sleeping for 15 minutes to allow appointments to refresh...")
                    for remaining in range(900, 0, -60):
                        await asyncio.sleep(60)
                        if remaining > 60:
                            logger.info(f"     Time remaining: {remaining - 60}s ({(remaining - 60) // 60}m)")
                    logger.info("  ✓ 15-minute wait completed")
                    
                    # Step 103: Refresh page again
                    logger.info("Step 103: Refresh page again")
                    try:
                        await self.page.reload(wait_until="domcontentloaded")
                        logger.info("  ✓ Page refreshed successfully")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not refresh page: {e}")
                    
                    # Step 104: Take screenshot (post-wait)
                    logger.info("Step 104: Take screenshot (post-wait)")
                    try:
                        screenshot_path = Path(__file__).parent / "screenshots" / f"step104_after_wait_{datetime.now().strftime('%H%M%S')}.png"
                        await self.page.screenshot(path=str(screenshot_path), full_page=True)
                        logger.info(f"  ✓ Screenshot: {screenshot_path.name}")
                    except Exception as e:
                        logger.warning(f"  ⚠ Could not take screenshot: {e}")
                    
                    # Step 105: Check for "זימון תורים" button
                    logger.info("Step 105: Check for 'זימון תורים' button")
                    zimon_found = False
                    try:
                        zimon_patterns = [
                            'div:has-text("זימון תורים")',
                            'span:has-text("זימון תורים")',
                            'a:has-text("זימון תורים")',
                            'button:has-text("זימון תורים")',
                        ]
                        
                        for pattern in zimon_patterns:
                            try:
                                zimon_btn = self.page.locator(pattern).first
                                if await zimon_btn.count() > 0 and await zimon_btn.is_visible():
                                    logger.info(f"  ✓ Found 'זימון תורים' button using pattern: {pattern}")
                                    zimon_found = True
                                    break
                            except:
                                pass
                        
                        if zimon_found:
                            logger.info("  → Session is valid. Returning retry_later status.")
                            return {
                                "status": "retry_later",
                                "message": "No appointments in range. Waited 15min and checked recovery point. Retrying search.",
                                "retry_after_seconds": 5
                            }
                        else:
                            logger.warning("  ✗ 'זימון תורים' button not found after wait")
                            logger.info("  → Session expired. Requires re-login.")
                            return {
                                "status": "error",
                                "message": "Session expired during fallback workflow. Re-login required.",
                                "requires_login": True
                            }
                    except Exception as e:
                        logger.warning(f"  ⚠ Error checking for zimon button: {e}")
                        return {
                            "status": "error",
                            "message": f"Could not verify session state after wait: {e}",
                            "requires_login": False
                        }
                
                # DATE IS WITHIN BOUNDARIES - Continue with appointment booking
                logger.info("")
                logger.info("=" * 70)
                logger.info("DATE WITHIN RANGE - PROCEEDING WITH APPOINTMENT BOOKING")
                logger.info("=" * 70)
                logger.info("")
                
                # Step 18: Find Appointment Type Button
                logger.info("Step 18: Find Appointment Type Button (זמן לוידאו/זמן לטלפון/זמן למרפאה)")
                
                appointment_btn = None
                appointment_btn_text = None
                
                # Multiple patterns to find the appointment button
                appointment_patterns = [
                    'div#divCalendarButtonsBoxForDoctor .appointments_large_button_blue_2',
                    '.appointment_calendar_buttons_box .appointments_large_button_blue_2',
                    'div:has-text("זמן לוידאו")',
                    'div:has-text("זמן לטלפון")',
                    'div:has-text("זמן למרפאה")',
                    'span:has-text("זמן לוידאו")',
                    'span:has-text("זמן לטלפון")',
                    'span:has-text("זמן למרפאה")',
                ]
                
                for pattern in appointment_patterns:
                    try:
                        logger.debug(f"  → Trying pattern: {pattern}")
                        btn = self.page.locator(pattern).first
                        if await btn.count() > 0 and await btn.is_visible():
                            btn_text = await btn.text_content()
                            logger.info(f"  ✓ Found appointment button: '{btn_text.strip()}'")
                            appointment_btn = btn
                            appointment_btn_text = btn_text.strip()
                            break
                    except Exception as e:
                        logger.debug(f"  → Pattern '{pattern}' failed: {str(e)[:80]}")
                        continue
                
                if not appointment_btn:
                    logger.error("  ✗ Could not find appointment type button")
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step18_error_{datetime.now().strftime('%H%M%S')}.png"
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.error(f"  📸 Error screenshot: {screenshot_path.name}")
                    return {
                        "status": "error",
                        "message": "Could not find appointment type button",
                        "requires_login": False
                    }
                
                # Step 19: Click Appointment Button
                logger.info("Step 19: Click Appointment Button")
                logger.info(f"  Clicking: '{appointment_btn_text}'")
                try:
                    await appointment_btn.click(timeout=5000)
                    logger.info("  ✓ Appointment button clicked")
                except Exception as e:
                    logger.error(f"  ✗ Failed to click appointment button: {e}")
                    return {"status": "error", "message": f"Failed to click appointment button: {e}"}
                
                # Step 20: Wait 2 Seconds
                logger.info("Step 20: Wait 2 Seconds")
                await asyncio.sleep(2)
                
                # Step 21: Take Screenshot
                logger.info("Step 21: Take Screenshot")
                screenshot_path = Path(__file__).parent / "screenshots" / f"step21_after_appointment_click_{datetime.now().strftime('%H%M%S')}.png"
                try:
                    await self.page.screenshot(path=str(screenshot_path), full_page=True)
                    logger.info(f"  📸 Screenshot: {screenshot_path.name}")
                except Exception as e:
                    logger.warning(f"  ⚠ Could not take screenshot: {e}")
                
                # Step 22: Enter Multi-Step Approval Loop (Max 10 Steps)
                logger.info("Step 22: Enter Multi-Step Approval Loop (Max 10 Steps)")
                logger.info("  Clicking continuation buttons and checking for SMS validation...")
                logger.info("")
                
                step_count = 0
                max_steps = 10
                sms_validation_reached = False
                
                while step_count < max_steps:
                    step_count += 1
                    logger.info(f"  ├─ Approval Loop Step {step_count}/10")
                    
                    # Step A: Check for SMS Validation Screen
                    logger.info(f"    ├─ Step A: Check for SMS validation screen")
                    try:
                        sms_patterns = [
                            'div.appointments_approve_video_validation_row_1:visible',
                            'div:has-text("ברגעים אלה נשלחת אליך הודעת"):visible',
                            'div:has-text("SMS"):visible',
                        ]
                        
                        for pattern in sms_patterns:
                            try:
                                sms_elem = self.page.locator(pattern).first
                                if await sms_elem.count() > 0:
                                    sms_text = await sms_elem.text_content()
                                    logger.info(f"    │  ✓ SMS validation screen detected!")
                                    logger.info(f"    │  Message: {sms_text.strip()[:80]}")
                                    sms_validation_reached = True
                                    break
                            except:
                                pass
                        
                        if sms_validation_reached:
                            break
                    except Exception as e:
                        logger.debug(f"    ├─ SMS check error: {str(e)[:60]}")
                    
                    # Step B: Find Continuation Button (4 patterns)
                    logger.info(f"    ├─ Step B: Find continuation button")
                    
                    button_patterns = [
                        ('pattern1_id', 'div#divContinueToShowMessage'),
                        ('pattern2_id', 'div#divContinueToFillPhone'),
                        ('pattern3_id', 'div#divValidatePhone'),
                        ('pattern4_id', 'div#divSaveAppointment'),
                        ('pattern5_class', '.appointments_large_button_blue_2:has-text("המשך")'),
                        ('pattern6_class', '.appointments_large_button_blue_2:has-text("שמור וסיים")'),
                    ]
                    
                    button_clicked = False
                    button_text = None
                    
                    for pattern_name, pattern in button_patterns:
                        try:
                            logger.debug(f"    │  → Trying {pattern_name}: {pattern}")
                            btn = self.page.locator(pattern).first
                            if await btn.count() > 0:
                                is_visible = await btn.is_visible()
                                if is_visible:
                                    button_text = await btn.text_content()
                                    logger.info(f"    │  ✓ Found button ({pattern_name}): '{button_text.strip()}'")
                                    
                                    # Step C: Click Button
                                    logger.info(f"    ├─ Step C: Click button")
                                    await btn.click(timeout=5000)
                                    logger.info(f"    │  ✓ Button clicked")
                                    
                                    # Step D: Wait 1 Second
                                    logger.info(f"    ├─ Step D: Wait 1 second")
                                    await asyncio.sleep(1)
                                    
                                    # Step E: Take Screenshot
                                    logger.info(f"    ├─ Step E: Take screenshot")
                                    step_screenshot_path = Path(__file__).parent / "screenshots" / f"step22_approval_{step_count}_{datetime.now().strftime('%H%M%S')}.png"
                                    try:
                                        await self.page.screenshot(path=str(step_screenshot_path), full_page=True)
                                        logger.info(f"    │  📸 {step_screenshot_path.name}")
                                    except:
                                        pass
                                    
                                    button_clicked = True
                                    break
                                else:
                                    logger.debug(f"    │  ⚠ Element found but not visible")
                        except Exception as e:
                            logger.debug(f"    │  ✗ {pattern_name} failed: {str(e)[:60]}")
                    
                    if not button_clicked:
                        logger.info(f"    └─ No continuation button found - approval loop ended")
                        break
                
                logger.info("")
                
                # Check result of approval loop
                if sms_validation_reached:
                    logger.info("✓ SMS VALIDATION SCREEN REACHED")
                    logger.info("")
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step_sms_validation_{datetime.now().strftime('%H%M%S')}.png"
                    try:
                        await self.page.screenshot(path=str(screenshot_path), full_page=True)
                        logger.info(f"📸 SMS validation screenshot: {screenshot_path.name}")
                    except:
                        pass
                    
                    return {
                        "status": "awaiting_sms_verification",
                        "message": "Appointment approved. SMS sent to phone. Enter code to confirm.",
                        "screenshot": str(screenshot_path)
                    }
                else:
                    logger.warning("⚠ APPROVAL LOOP COMPLETED WITHOUT SMS VALIDATION")
                    logger.info("Workflow may have progressed differently or reached unexpected state")
                    logger.info("")
                    screenshot_path = Path(__file__).parent / "screenshots" / f"step_approval_final_{datetime.now().strftime('%H%M%S')}.png"
                    try:
                        await self.page.screenshot(path=str(screenshot_path), full_page=True)
                        logger.info(f"📸 Final state screenshot: {screenshot_path.name}")
                    except:
                        pass
                    
                    return {
                        "status": "awaiting_completion",
                        "message": "Appointment approval workflow completed. Check browser for next steps.",
                        "screenshot": str(screenshot_path)
                    }
            
            elif action == "click_zaman_tor":
                # Click the "זמן תור" button from search results
                logger.info("Starting click_zaman_tor command")
                
                zaman_button_clicked = False
                
                zaman_strategies = [
                    ("span_id", lambda: self.page.locator('span#ctl00_MainContentPlaceHolder_ucSearchResults_RepeaterDoctorsResults_ctl00_LabelButtonTextForMakingAppointment').first),
                    ("span_text", lambda: self.page.locator('span:has-text("זמן תור")').first),
                    ("parent_link", lambda: self.page.locator('a:has(span:has-text("זמן תור"))').first),
                    ("contains_text", lambda: self.page.get_by_text("זמן תור").first)
                ]
                
                for strategy_name, locator_fn in zaman_strategies:
                    try:
                        logger.info(f"  Trying strategy: {strategy_name}")
                        element = locator_fn()
                        await element.wait_for(timeout=5000)
                        await element.click()
                        logger.info(f"  ✓ Clicked 'זמן תור' using strategy: {strategy_name}")
                        zaman_button_clicked = True
                        await asyncio.sleep(2)
                        
                        # Take screenshot after clicking
                        screenshot_path = Path(__file__).parent / "screenshots" / f"zaman_tor_clicked_{datetime.now().strftime('%H%M%S')}.png"
                        screenshot_path.parent.mkdir(exist_ok=True)
                        await self.page.screenshot(path=str(screenshot_path))
                        logger.info(f"  📸 Screenshot: {screenshot_path.name}")
                        break
                    except Exception as e:
                        logger.debug(f"  ✗ Strategy '{strategy_name}' failed: {e}")
                        continue
                
                if not zaman_button_clicked:
                    logger.error("  ⚠ Could not click 'זמן תור' button")
                    screenshot_path = Path(__file__).parent / "screenshots" / f"zaman_tor_error_{datetime.now().strftime('%H%M%S')}.png"
                    screenshot_path.parent.mkdir(exist_ok=True)
                    await self.page.screenshot(path=str(screenshot_path))
                    logger.error(f"  📸 Error screenshot: {screenshot_path.name}")
                    return {"status": "error", "message": "Failed to click זמן תור button"}
                
                logger.info("✓ זמן תור button clicked successfully")
                
                return {
                    "status": "success",
                    "clicked": True,
                    "screenshot": str(screenshot_path)
                }
            
            elif action == "book_appointment":
                # Book appointment with optional preference for phone vs in-clinic
                appointment_type = cmd["params"].get("appointment_type", "הזמן למרפאה")  # Default to in-clinic
                
                logger.info(f"Starting appointment booking (type: {appointment_type})")
                
                # Click first result (soonest appointment)
                logger.info("Step 1: Select first available slot")
                await self.page.locator(".appointment-result").first.click()  # Adjust selector based on actual HTML
                await asyncio.sleep(2)
                
                # The calendar should open with default slot selected
                logger.info(f"Step 2: Click '{appointment_type}'")
                await self.page.get_by_text(appointment_type).first.click()
                await asyncio.sleep(2)
                
                # Pop-up appears with appointment info
                logger.info("Step 3: Click 'המשך' on pop-up")
                await self.page.get_by_text("המשך").first.click()
                await asyncio.sleep(2)
                
                # Final confirmation
                logger.info("Step 4: Click 'שמור וסיים' to confirm")
                await self.page.get_by_text("שמור וסיים").first.click()
                await asyncio.sleep(3)
                
                logger.info("✓ Appointment booked!")
                
                # Take screenshot of confirmation
                screenshot_path = Path(__file__).parent / "screenshots" / "appointment_confirmed.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                await self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot: {screenshot_path}")
                
                return {
                    "status": "success",
                    "screenshot": str(screenshot_path)
                }
            
            else:
                logger.error(f"Unknown action: {action}")
                return {"status": "error", "message": f"Unknown action: {action}"}
        
        except Exception as e:
            logger.error(f"Command error: {e}")
            logger.error(traceback.format_exc())
            return {"status": "error", "message": str(e)}
    
    async def run(self):
        """Main loop - watch for commands and socket connections."""
        await self.setup()
        
        # Start socket server in background
        server = await self.start_socket_server()
        
        logger.info("")
        logger.info("Agent ready! Send commands via:")
        logger.info(f"  Socket: Connect to {SOCKET_HOST}:{SOCKET_PORT}")
        logger.info(f"  File: Edit {COMMANDS_FILE}")
        logger.info("")
        logger.info("To start, send login command:")
        logger.info('  {"action": "login"}')
        logger.info("")
        
        # Start server task
        server_task = asyncio.create_task(server.serve_forever())
        
        try:
            while True:
                try:
                    # Also check file-based commands
                    cmd = self.load_command()
                    
                    if cmd:
                        logger.info(f"DEBUG: Loaded command: {cmd.get('action')}")
                        cmd_hash = self.get_command_hash(cmd)
                        
                        # Check file modification time
                        file_mtime = COMMANDS_FILE.stat().st_mtime if COMMANDS_FILE.exists() else None
                        logger.info(f"DEBUG: Command hash: {cmd_hash}, Last hash: {self.last_command_hash}")
                        logger.info(f"DEBUG: File mtime: {file_mtime}, Last mtime: {self.last_file_mtime}")
                        
                        # Only execute if command is new or has changed (check both hash AND file modification time)
                        if cmd_hash != self.last_command_hash or file_mtime != self.last_file_mtime:
                            logger.info("DEBUG: Command changed (hash or file modified), executing command")
                            
                            if cmd.get("action") == "login":
                                # Login with infinite retry mechanism
                                retry_count = 0
                                success = False
                                
                                while not success:
                                    if retry_count > 0:
                                        logger.info("")
                                        logger.info(f"🔄 Login retry attempt #{retry_count}")
                                        logger.info("Waiting 10 seconds before retry...")
                                        await asyncio.sleep(10)
                                    
                                    success = await self.login_to_leumit()
                                    retry_count += 1
                                    
                                    if not success:
                                        logger.warning(f"Login attempt #{retry_count} failed, will retry in 10 seconds...")
                                        logger.info("Press Ctrl+C to stop agent if needed")
                                
                                logger.info("✅ Login successful!")
                                
                                self.save_state({
                                    "logged_in": success,
                                    "timestamp": datetime.now().isoformat(),
                                    "last_url": self.page.url if self.page else None
                                })
                                
                                # Don't update command hash yet - keep retrying on same command
                                # Only update hash after successful login
                                self.last_command_hash = cmd_hash
                                self.last_file_mtime = file_mtime
                            else:
                                # Execute non-login commands
                                result = await self.execute_command(cmd)
                                logger.info(f"Result: {result}")
                                
                                # Check if command requires login
                                if isinstance(result, dict) and result.get("requires_login"):
                                    logger.info("")
                                    logger.info("⚠️  Command requires login. Attempting login first...")
                                    
                                    # Perform login with infinite retry
                                    retry_count = 0
                                    success = False
                                    
                                    while not success:
                                        if retry_count > 0:
                                            logger.info("")
                                            logger.info(f"🔄 Login retry attempt #{retry_count}")
                                            logger.info("Waiting 10 seconds before retry...")
                                            await asyncio.sleep(10)
                                        
                                        success = await self.login_to_leumit()
                                        retry_count += 1
                                        
                                        if not success:
                                            logger.warning(f"Login attempt #{retry_count} failed, will retry in 10 seconds...")
                                            logger.info("Press Ctrl+C to stop agent if needed")
                                    
                                    logger.info("✅ Login successful! Will retry command on next cycle...")
                                    
                                    # DON'T update hash - let command retry on next cycle
                                    # The command file hasn't changed, but we need to re-execute after login
                                    self.save_state({
                                        "logged_in": success,
                                        "timestamp": datetime.now().isoformat(),
                                        "last_url": self.page.url if self.page else None,
                                        "last_command": "login",
                                        "result": {"status": "success", "next": cmd.get("action")}
                                    })
                                else:
                                    # Check if command requires retry_later (e.g., no appointments available)
                                    if isinstance(result, dict) and result.get("status") == "retry_later":
                                        retry_seconds = result.get("retry_after_seconds", 900)  # Default 15 minutes
                                        logger.info("")
                                        logger.info(f"Command will retry after delay: {result.get('message', 'Retrying later...')}")
                                        logger.info(f"   Waiting {retry_seconds} seconds ({retry_seconds // 60} minutes) before retry...")
                                        
                                        # IMPORTANT: Update hash NOW before sleeping
                                        # This prevents infinite "command changed" detection in the next loop iteration
                                        # We've already executed this command once, sleep, and want to retry naturally on next cycle
                                        self.last_command_hash = cmd_hash
                                        self.last_file_mtime = file_mtime
                                        
                                        await asyncio.sleep(retry_seconds)
                                        
                                        # After sleep, RESET the hash so command re-executes on next cycle
                                        # This allows the fallback workflow to complete and then search again
                                        self.last_command_hash = None
                                        self.last_file_mtime = None
                                        
                                        logger.info("   Retry time reached, command will re-execute on next cycle")
                                        continue  # Skip to next iteration
                                    
                                    # Check if command succeeded or failed
                                    command_succeeded = (isinstance(result, dict) and result.get("status") != "error")
                                    
                                    if command_succeeded:
                                        # Command succeeded - update hash to prevent re-execution
                                        self.last_command_hash = cmd_hash
                                        self.last_file_mtime = file_mtime
                                        logger.info("Command completed successfully")
                                    else:
                                        # Command failed - DON'T update hash to allow retry
                                        logger.warning("Command failed, will retry on next cycle")
                                        logger.info("   To skip this command, modify commands.json")
                                    
                                    self.save_state({
                                        "logged_in": self.logged_in,
                                        "timestamp": datetime.now().isoformat(),
                                        "last_url": self.page.url if self.page else None,
                                        "last_command": cmd.get("action"),
                                        "result": result
                                    })
                        else:
                            # Command hasn't changed, wait
                            logger.info("DEBUG: Command unchanged, waiting...")
                            await asyncio.sleep(2)
                    else:
                        # No command file
                        logger.info("DEBUG: No command file found")
                        await asyncio.sleep(2)
                
                except KeyboardInterrupt:
                    logger.info("")
                    logger.info("Shutdown requested")
                    break
                except Exception as e:
                    logger.error(f"Main loop error: {e}")
                    logger.error(traceback.format_exc())
                    await asyncio.sleep(2)
        finally:
            # Cleanup
            try:
                server.close()
                await server.wait_closed()
            except:
                pass
            
            try:
                server_task.cancel()
            except:
                pass
            
            try:
                if self.browser:
                    await self.browser.close()
            except:
                pass
            
            try:
                if self.playwright:
                    await self.playwright.stop()
            except:
                pass
            
            logger.info("Agent stopped")


async def main():
    # Ignore interruption signals to prevent cancellation
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    
    agent = PersistentAgent()
    try:
        await agent.run()
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.warning("Agent interrupted - attempting graceful shutdown")
        pass


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Agent stopped by user")
        pass
