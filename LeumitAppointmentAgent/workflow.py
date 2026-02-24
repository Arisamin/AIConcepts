"""
Workflow client - sends commands to bridge process.
This script can exit and restart without losing the Chrome session.
"""
import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from bridge_protocol import (
    Command, Response, CommandType,
    BRIDGE_HOST, BRIDGE_PORT, MESSAGE_DELIMITER
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


class BridgeClient:
    """Client that communicates with bridge process."""
    
    def __init__(self):
        self.reader = None
        self.writer = None
    
    async def connect(self):
        """Connect to bridge."""
        logger.info(f"Connecting to bridge at {BRIDGE_HOST}:{BRIDGE_PORT}...")
        self.reader, self.writer = await asyncio.open_connection(
            BRIDGE_HOST, BRIDGE_PORT
        )
        logger.info("✓ Connected to bridge")
    
    async def send_command(self, cmd: Command) -> Response:
        """Send command and wait for response."""
        # Send command
        message = cmd.to_json() + "\n"
        self.writer.write(message.encode())
        await self.writer.drain()
        
        # Read response
        data = await self.reader.readuntil(MESSAGE_DELIMITER)
        response = Response.from_json(data.decode().strip())
        
        if response.status == "error":
            raise Exception(f"Bridge error: {response.error}")
        
        return response
    
    async def navigate(self, url: str):
        """Navigate to URL."""
        logger.info(f"Navigating to: {url}")
        cmd = Command(CommandType.NAVIGATE, url=url)
        await self.send_command(cmd)
    
    async def fill(self, selector: str, value: str, frame: str = None):
        """Fill input field."""
        logger.info(f"Filling {selector}")
        cmd = Command(CommandType.FILL, selector=selector, value=value, frame=frame)
        await self.send_command(cmd)
    
    async def click(self, selector: str = None, text: str = None):
        """Click element by selector or text."""
        if text:
            logger.info(f"Clicking text: {text}")
            cmd = Command(CommandType.CLICK, text=text)
        else:
            logger.info(f"Clicking {selector}")
            cmd = Command(CommandType.CLICK, selector=selector)
        await self.send_command(cmd)
    
    async def wait(self, seconds: float):
        """Wait for seconds."""
        logger.info(f"Waiting {seconds}s...")
        cmd = Command(CommandType.WAIT, seconds=seconds)
        await self.send_command(cmd)
    
    async def screenshot(self, path: str):
        """Take screenshot."""
        logger.info(f"Taking screenshot: {path}")
        cmd = Command(CommandType.SCREENSHOT, path=path)
        await self.send_command(cmd)
    
    async def get_url(self) -> str:
        """Get current URL."""
        cmd = Command(CommandType.GET_URL)
        response = await self.send_command(cmd)
        return response.data["url"]
    
    async def query_selector(self, selector: str, frame: str = None) -> bool:
        """Check if selector exists."""
        cmd = Command(CommandType.QUERY_SELECTOR, selector=selector, frame=frame)
        response = await self.send_command(cmd)
        return response.data["found"]
    
    async def get_frames(self) -> list:
        """Get list of frames."""
        cmd = Command(CommandType.GET_FRAMES)
        response = await self.send_command(cmd)
        return response.data["frames"]
    
    async def get_inputs(self, frame: str = None) -> list:
        """Get all input fields in page or frame."""
        cmd = Command(CommandType.GET_INPUTS, frame=frame)
        response = await self.send_command(cmd)
        return response.data["inputs"]
    
    def close(self):
        """Close connection."""
        if self.writer:
            self.writer.close()


async def leumit_login_workflow():
    """Main workflow - login to Leumit."""
    logger.info("=" * 60)
    logger.info("LEUMIT LOGIN WORKFLOW")
    logger.info("=" * 60)
    logger.info("")
    
    # Get credentials
    leumit_id = os.getenv("LEUMIT_ID")
    leumit_mobile = os.getenv("LEUMIT_MOBILE")
    
    if not leumit_id or not leumit_mobile:
        raise Exception("Missing credentials in .env file")
    
    client = BridgeClient()
    
    try:
        await client.connect()
        
        # Check current URL
        current_url = await client.get_url()
        logger.info(f"Current URL: {current_url}")
        logger.info("")
        
        # Navigate to Google if not there
        if "google.com" not in current_url:
            await client.navigate("https://www.google.com")
        
        # Search for "לאומית"
        logger.info("Searching for 'לאומית' on Google...")
        await client.fill("textarea[name='q']", "לאומית")
        await client.click("input[name='btnK']")
        await client.wait(3)
        
        # Click Leumit link
        logger.info("Clicking Leumit website link...")
        await client.click("a[href*='leumit.co.il']")
        await client.wait(3)
        
        # DOM-based login state detection
        logger.info("Checking login state via DOM...")
        is_personal_area = await client.query_selector("button:has-text('אזור אישי'), a:has-text('אזור אישי')")
        is_appointments = await client.query_selector("button:has-text('זימון תורים'), a:has-text('זימון תורים')")
        
        if is_personal_area:
            logger.info("'אזור אישי' button found: NOT logged in. Proceeding with login.")
            try:
                await client.click(text="אזור אישי")
                logger.info("✓ Clicked 'אזור אישי' button")
                await client.wait(8)  # Wait for modal/iframe to load
            except Exception as e:
                logger.warning(f"⚠ Could not click button: {e}")
                logger.warning("Continuing anyway...")
        elif is_appointments:
            logger.info("'זימון תורים' button found: Already logged in. Skipping login workflow.")
            logger.info("✅ Already logged in. Workflow complete.")
            return
        else:
            logger.warning("Neither 'אזור אישי' nor 'זימון תורים' button found. Retrying login workflow.")
            await leumit_login_workflow()
            return
        # Check current URL after clicking
        current_url = await client.get_url()
        logger.info(f"After button click, URL: {current_url}")
        
        # Look for login form in frames
        logger.info("Searching for login form...")
        frames = await client.get_frames()
        logger.info(f"Found {len(frames)} frame(s)")
        
        for frame in frames:
            logger.info(f"  Frame: {frame['name']} - {frame['url']}")
        
        # Check the login frame specifically
        login_frame_url = "https://online2.leumit.co.il/Online/login/LoginForHomepageNew.aspx"
        login_frame = None
        login_frame_index = None
        
        for i, frame in enumerate(frames):
            if login_frame_url in frame['url']:
                login_frame = frame['name']
                login_frame_index = i
                logger.info(f"✓ Found login frame at index {i}: {login_frame} - {frame['url']}")
                break
        
        if login_frame:
            logger.info("Getting input fields from login frame...")
            # Wait a bit more for frame to be fully interactive
            await client.wait(2)
            
            inputs = await client.get_inputs(frame=login_frame_url)
            logger.info(f"Found {len(inputs)} input fields:")
            
            # Find the ID and phone fields
            id_field = None
            phone_field = None
            
            for inp in inputs:
                if inp['type'] == 'text' and not inp['name'] in ['FormId', 'FormName', '125f428408c3436ab9bc91b77a606520']:
                    id_field = inp['id']
                    logger.info(f"  ✓ ID field: {id_field}")
                elif inp['type'] == 'tel':
                    phone_field = inp['id']
                    logger.info(f"  ✓ Phone field: {phone_field}")
            
            if id_field and phone_field:
                logger.info("")
                logger.info("Filling login form...")
                logger.info(f"Using frame index: {login_frame_index}")
                # Use frame index - the second frame (index 1)
                # Use getElementById instead of querySelector with attribute selector
                await client.fill(id_field, leumit_id, frame=f"index:{login_frame_index}")
                logger.info("✓ Entered ID")
                
                await client.fill(phone_field, leumit_mobile, frame=f"index:{login_frame_index}")
                logger.info("✓ Entered phone")
                
                # Screenshot
                screenshot_path = str(Path(__file__).parent / "screenshots" / "login_filled.png")
                Path(screenshot_path).parent.mkdir(exist_ok=True)
                await client.screenshot(screenshot_path)
                logger.info(f"✓ Screenshot saved: {screenshot_path}")
                
                logger.info("")
                logger.info("=" * 60)
                logger.info("✅ WORKFLOW COMPLETE")
                logger.info("=" * 60)
                logger.info("")
                logger.info("Chrome window is still open with login form filled.")
                logger.info("Please complete OTP verification manually.")
                logger.info("The bridge process will keep running in the background.")
                logger.info("")
                return
        
        # Old fallback code below
        form_found = False
        form_frame = None
        
        for frame in frames:
            frame_name = frame["name"]
            logger.info(f"  Checking frame: {frame_name}")
            
            found = await client.query_selector("#TextBoxIdNumForOTP", frame=frame_name)
            if found:
                logger.info(f"  ✓ Found ID input in frame: {frame_name}")
                form_frame = frame_name
                form_found = True
                break
        
        if not form_found:
            logger.warning("⚠ Login form not found in current frames")
            logger.info("Retrying from Google search...")
            logger.info("")
            # Recursive retry
            await leumit_login_workflow()
            return
        
        # Fill the form
        logger.info("")
        logger.info("Filling login form...")
        await client.fill("#TextBoxIdNumForOTP", leumit_id, frame=form_frame)
        logger.info("✓ Entered ID")
        
        await client.fill("#TextBoxCellphone", leumit_mobile, frame=form_frame)
        logger.info("✓ Entered phone")
        
        # Screenshot
        screenshot_path = str(Path(__file__).parent / "screenshots" / "login_filled.png")
        Path(screenshot_path).parent.mkdir(exist_ok=True)
        await client.screenshot(screenshot_path)
        logger.info(f"✓ Screenshot saved: {screenshot_path}")
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ WORKFLOW COMPLETE")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Chrome window is still open with login form filled.")
        logger.info("Please complete OTP verification manually.")
        logger.info("The bridge process will keep running in the background.")
        logger.info("")
    
    finally:
        client.close()


async def main():
    try:
        await leumit_login_workflow()
    except ConnectionRefusedError:
        logger.error("=" * 60)
        logger.error("❌ Cannot connect to bridge!")
        logger.error("=" * 60)
        logger.error("")
        logger.error("Please start the bridge process first:")
        logger.error("  python bridge.py")
        logger.error("")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
