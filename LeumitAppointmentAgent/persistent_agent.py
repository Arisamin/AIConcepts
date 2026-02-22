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

sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)

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
        self.socket_server = None
    
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
        
        try:
            context = await self.playwright.chromium.launch_persistent_context(
                str(user_data_dir),
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                ]
            )
        except Exception as e:
            if "Target" in str(e) or "closed" in str(e):
                logger.error(f"Browser profile locked! Close existing browser window or delete .browser_profile/ folder")
                logger.error(f"Error: {e}")
                raise
            else:
                raise
        
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
        """Complete login flow."""
        logger.info("=" * 60)
        logger.info("LOGIN FLOW")
        logger.info("=" * 60)
        logger.info("")
        
        try:
            # Navigate to Google
            logger.info("Navigating to Google...")
            await self.page.goto("https://www.google.com", wait_until="domcontentloaded")
            
            # Search for Leumit
            logger.info("Searching for 'לאומית'...")
            await self.page.fill("textarea[name='q'], input[name='q']", "לאומית")
            await self.page.click("input[name='btnK']")
            await asyncio.sleep(3)
            
            # Click Leumit link
            logger.info("Clicking Leumit link...")
            await self.page.click("a[href*='leumit.co.il']")
            await asyncio.sleep(3)
            
            # Click "אזור אישי" button
            logger.info("Clicking 'אזור אישי' button...")
            try:
                await self.page.get_by_text("אזור אישי").first.click()
            except:
                logger.warning("Could not click via text, trying selector...")
                await self.page.click("button:has-text('אזור אישי'), a:has-text('אזור אישי')")
            
            await asyncio.sleep(8)  # Wait for login modal to load
            
            # Find and fill login form
            logger.info("Looking for login form...")
            
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
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("⏳ WAITING FOR OTP VERIFICATION")
            logger.info("=" * 60)
            logger.info("Please complete OTP verification in the browser window")
            logger.info("Agent will continue once you're logged in...")
            logger.info("")
            
            # Wait for successful login by checking URL or page content
            # For now, just wait for user action
            max_wait = 300  # 5 minutes
            waited = 0
            check_interval = 2
            
            while waited < max_wait:
                await asyncio.sleep(check_interval)
                waited += check_interval
                
                current_url = self.page.url
                
                # Check if we're past the login page
                if "HomePage" not in current_url and "Login" not in current_url:
                    logger.info(f"✓ Login successful! URL: {current_url}")
                    self.logged_in = True
                    logger.info("")
                    return True
                
                # Show progress every 30 seconds
                if waited % 30 == 0:
                    logger.info(f"Still waiting... ({waited}s / {max_wait}s)")
            
            logger.error("Login timeout - OTP not verified in time")
            return False
            
        except Exception as e:
            logger.error(f"Login error: {e}")
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
                logger.info(f"DEBUG: Loaded command: {cmd}")
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
                
                # Recovery mechanism: Try to find the "זימון תורים" button
                # If not found, do fresh navigation from Google
                logger.info("Step 0: Looking for 'זימון תורים' button...")
                try:
                    # Quick check if button exists (3 second timeout)
                    await self.page.get_by_text("זימון תורים").first.wait_for(timeout=3000, state="visible")
                    logger.info("  ✓ Button found, already on correct page")
                except:
                    logger.info("  Button not found - performing recovery navigation")
                    logger.info("  → Navigating to Google...")
                    await self.page.goto("https://www.google.com", wait_until="domcontentloaded")
                    await asyncio.sleep(1)
                    
                    logger.info("  → Searching for 'לאומית'...")
                    search_box = await self.page.query_selector("textarea[name='q'], input[name='q']")
                    if search_box:
                        await search_box.fill("לאומית")
                        await search_box.press("Enter")
                        await asyncio.sleep(3)
                    
                    logger.info("  → Clicking first Leumit link...")
                    # Click first link that contains "leumit.co.il"
                    first_link = await self.page.query_selector("a[href*='leumit.co.il']")
                    if first_link:
                        await first_link.click()
                        await asyncio.sleep(5)  # Wait for page to fully load
                    
                    logger.info("  → Checking if logged in...")
                    # Now check if we landed on logged-in page or login page
                    try:
                        await self.page.get_by_text("זימון תורים").first.wait_for(timeout=3000, state="visible")
                        logger.info("  ✓ Logged in - 'זימון תורים' button found")
                    except:
                        logger.info("  Not logged in yet - checking for login form...")
                        # Check if we're on a login page
                        current_url = self.page.url
                        if "login" in current_url.lower():
                            logger.info("  → On login page - need to perform login")
                            # Trigger login flow
                            await self.login_to_leumit()
                            # After login, should be on homepage with the button
                        else:
                            logger.info("  → Clicking 'אזור אישי' to reach login...")
                            try:
                                await self.page.get_by_text("אזור אישי").first.click(timeout=5000)
                                await asyncio.sleep(3)
                                await self.login_to_leumit()
                            except Exception as e:
                                logger.error(f"  Could not find login path: {e}")
                                raise Exception("Failed to navigate to login or logged-in state")
                
                # Navigate to appointments section
                logger.info("Step 1: Click 'זימון תורים'")
                await self.page.get_by_text("זימון תורים").first.click(timeout=30000)
                await asyncio.sleep(2)
                
                logger.info("Step 2: Click 'בצע חיפוש חדש'")
                await self.page.get_by_text("בצע חיפוש חדש").first.click(timeout=60000)
                await asyncio.sleep(2)
                
                logger.info("Step 3: Click 'רופאים ומטפלים'")
                await self.page.get_by_text("רופאים ומטפלים").first.click()
                await asyncio.sleep(2)
                
                # Select specialty
                logger.info(f"Step 4: Select specialty '{specialty}'")
                try:
                    await self.page.click("text=תחום טיפול")
                    await asyncio.sleep(1)
                    await self.page.get_by_text(specialty, exact=True).first.click()
                    await asyncio.sleep(2)
                except Exception as e:
                    logger.error(f"Error selecting specialty: {e}")
                
                # Select subcategory if dropdown appears
                logger.info(f"Step 5: Select subcategory '{subcategory}'")
                try:
                    await self.page.get_by_text(subcategory, exact=True).first.click(timeout=3000)
                    await asyncio.sleep(1)
                except:
                    logger.info("No subcategory dropdown (or already selected)")
                
                # Fill doctor name if provided
                if doctor_name:
                    logger.info(f"Step 6: Filter by doctor name '{doctor_name}'")
                    try:
                        # Look for doctor name input field
                        doctor_input = await self.page.query_selector("input[placeholder*='שם רופא'], input[id*='doctor'], input[id*='Doctor']")
                        if doctor_input:
                            await doctor_input.fill(doctor_name)
                            await asyncio.sleep(1)
                            logger.info(f"  ✓ Doctor name entered")
                        else:
                            logger.warning("  Could not find doctor name input field")
                    except Exception as e:
                        logger.warning(f"  Error filling doctor name: {e}")
                
                # Click search
                logger.info("Step 7: Click 'חפש'")
                await self.page.get_by_text("חפש").first.click()
                await asyncio.sleep(3)
                
                logger.info("✓ Search complete - results should be displayed")
                
                # Take screenshot
                screenshot_path = Path(__file__).parent / "screenshots" / "search_results.png"
                screenshot_path.parent.mkdir(exist_ok=True)
                await self.page.screenshot(path=str(screenshot_path))
                logger.info(f"Screenshot: {screenshot_path}")
                
                return {
                    "status": "success",
                    "specialty": specialty,
                    "subcategory": subcategory,
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
                        logger.info(f"DEBUG: Command hash: {cmd_hash}, Last hash: {self.last_command_hash}")
                        
                        # Only execute if command is new or has changed
                        if cmd_hash != self.last_command_hash:
                            logger.info("DEBUG: Hash changed, executing command")
                            self.last_command_hash = cmd_hash
                            
                            if cmd.get("action") == "login":
                                success = await self.login_to_leumit()
                                self.save_state({
                                    "logged_in": success,
                                    "timestamp": datetime.now().isoformat(),
                                    "last_url": self.page.url if self.page else None
                                })
                            else:
                                # With persistent context, cookies may restore session
                                # Let commands try - if session is invalid, they'll fail with useful errors
                                result = await self.execute_command(cmd)
                                logger.info(f"Result: {result}")
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
