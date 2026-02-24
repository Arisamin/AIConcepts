"""
Bridge process - maintains Chrome connection and handles commands.
This process stays running and keeps the browser debugging port active.
"""
import asyncio
import logging
import subprocess
import sys
import platform
import time
from pathlib import Path
import socket
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from playwright.async_api import async_playwright, Browser, Page
from bridge_protocol import (
    Command, Response, CommandType,
    BRIDGE_HOST, BRIDGE_PORT, MESSAGE_DELIMITER
)

GOOGLE_URL = "https://www.google.com"
DEBUG_PORT = 9222
CHROME_DATA_DIR = Path(__file__).parent / ".chrome_data"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class BridgeServer:
    """Bridge server that manages Chrome and handles commands."""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.playwright = None
        self.server_socket = None
        self.running = False
        self.chrome_process = None
    
    def find_chrome(self):
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
    
    async def start_chrome(self):
        """Launch Chrome with debugging port."""
        logger.info("=" * 60)
        logger.info("BRIDGE: Launching Chrome")
        logger.info("=" * 60)
        
        chrome_exe = self.find_chrome()
        if not chrome_exe:
            raise Exception("Chrome not found")
        
        logger.info(f"Chrome: {chrome_exe}")
        logger.info(f"Debug port: {DEBUG_PORT}")
        logger.info(f"Profile: {CHROME_DATA_DIR}")
        
        # Launch Chrome
        if platform.system() == "Windows":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = 5
            
            self.chrome_process = subprocess.Popen(
                [
                    chrome_exe,
                    "--new-window",
                    f"--remote-debugging-port={DEBUG_PORT}",
                    f"--user-data-dir={CHROME_DATA_DIR}",
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    GOOGLE_URL
                ],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NEW_CONSOLE,
                startupinfo=startupinfo,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        else:
            self.chrome_process = subprocess.Popen(
                [
                    chrome_exe,
                    "--new-window",
                    f"--remote-debugging-port={DEBUG_PORT}",
                    f"--user-data-dir={CHROME_DATA_DIR}",
                    "--disable-blink-features=AutomationControlled",
                    "--start-maximized",
                    GOOGLE_URL
                ],
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        
        logger.info(f"✓ Chrome launched (PID: {self.chrome_process.pid})")
        logger.info("Waiting for Chrome to initialize...")
        time.sleep(7)
        
        # Connect via CDP
        logger.info("Connecting via CDP...")
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(
            f"http://127.0.0.1:{DEBUG_PORT}"
        )
        
        # Get the page
        if self.browser.contexts:
            pages = self.browser.contexts[0].pages
            if pages:
                self.page = pages[0]
        
        logger.info("✓ Connected to browser")
        logger.info(f"✓ Current URL: {self.page.url if self.page else 'N/A'}")
        logger.info("")
    
    async def handle_command(self, cmd: Command) -> Response:
        """Execute a command and return response."""
        try:
            if cmd.action == CommandType.PING:
                return Response.success({"status": "alive"})
            
            elif cmd.action == CommandType.NAVIGATE:
                url = cmd.params.get("url")
                await self.page.goto(url, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                return Response.success({"url": self.page.url})
            
            elif cmd.action == CommandType.FILL:
                selector = cmd.params.get("selector")
                value = cmd.params.get("value")
                frame_name = cmd.params.get("frame")
                
                if frame_name:
                    # Find frame by index, URL, or name
                    frame = None
                    
                    if frame_name.startswith("index:"):
                        # Match by index
                        idx = int(frame_name.split(":")[1])
                        if idx < len(self.page.frames):
                            frame = self.page.frames[idx]
                            logger.info(f"  Matched frame by index {idx}: {frame.url}")
                    else:
                        # Match by URL or name
                        for f in self.page.frames:
                            if frame_name in f.url or f.name == frame_name:
                                frame = f
                                logger.info(f"  Matched frame: {f.name or '(no name)'} - {f.url}")
                                break
                    
                    if frame:
                        # Use JavaScript to fill - try getElementById first, then querySelector
                        try:
                            result = await frame.evaluate("""(args) => {
                                let elem = document.getElementById(args.selector);
                                if (!elem) {
                                    elem = document.querySelector(args.selector);
                                }
                                if (elem) {
                                    elem.value = args.value;
                                    elem.dispatchEvent(new Event('input', { bubbles: true }));
                                    elem.dispatchEvent(new Event('change', { bubbles: true }));
                                    return true;
                                }
                                return false;
                            }""", {"selector": selector, "value": value})
                            
                            if result:
                                logger.info(f"  Filled {selector[:20]}... with {value[:3]}***")
                            else:
                                return Response.error(f"Element not found: {selector}")
                        except Exception as e:
                            return Response.error(f"Fill error: {str(e)}")
                    else:
                        return Response.error(f"Frame not found: {frame_name}")
                else:
                    await self.page.fill(selector, value)
                
                return Response.success()
            
            elif cmd.action == CommandType.CLICK:
                selector = cmd.params.get("selector")
                text = cmd.params.get("text")
                
                if text:
                    # Click by text content
                    elem = await self.page.get_by_text(text).first.click()
                    await asyncio.sleep(2)
                    return Response.success()
                else:
                    # Click by selector
                    elem = await self.page.query_selector(selector)
                    if elem:
                        await elem.click()
                        await asyncio.sleep(2)
                        return Response.success()
                    else:
                        return Response.error(f"Element not found: {selector}")
            
            elif cmd.action == CommandType.WAIT:
                seconds = cmd.params.get("seconds", 1)
                await asyncio.sleep(seconds)
                return Response.success()
            
            elif cmd.action == CommandType.SCREENSHOT:
                path = cmd.params.get("path", "screenshot.png")
                await self.page.screenshot(path=path)
                return Response.success({"path": path})
            
            elif cmd.action == CommandType.GET_URL:
                return Response.success({"url": self.page.url})
            
            elif cmd.action == CommandType.QUERY_SELECTOR:
                selector = cmd.params.get("selector")
                frame_name = cmd.params.get("frame")
                
                if frame_name:
                    frame = None
                    for f in self.page.frames:
                        if f.name == frame_name or frame_name == "main":
                            frame = f
                            break
                    if frame:
                        elem = await frame.query_selector(selector)
                        return Response.success({"found": elem is not None})
                    else:
                        return Response.error(f"Frame not found: {frame_name}")
                else:
                    elem = await self.page.query_selector(selector)
                    return Response.success({"found": elem is not None})
            
            elif cmd.action == CommandType.GET_FRAMES:
                frames = [{"name": f.name or "main", "url": f.url} for f in self.page.frames]
                return Response.success({"frames": frames})
            
            elif cmd.action == CommandType.GET_INPUTS:
                frame_name = cmd.params.get("frame")
                frame = None
                
                if frame_name:
                    for f in self.page.frames:
                        if f.name == frame_name or (frame_name == "main" and not f.name):
                            frame = f
                            break
                else:
                    frame = self.page
                
                if frame:
                    inputs = await frame.evaluate("""() => {
                        const inputs = Array.from(document.querySelectorAll('input, textarea'));
                        return inputs.map(input => ({
                            tag: input.tagName,
                            type: input.type,
                            id: input.id,
                            name: input.name,
                            placeholder: input.placeholder
                        }));
                    }""")
                    return Response.success({"inputs": inputs})
                else:
                    return Response.error(f"Frame not found: {frame_name}")
            
            elif cmd.action == CommandType.SHUTDOWN:
                logger.info("Shutdown command received")
                self.running = False
                return Response.success()
            
            else:
                return Response.error(f"Unknown command: {cmd.action}")
        
        except Exception as e:
            logger.error(f"Error executing command: {e}")
            return Response.error(str(e))
    
    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """Handle a client connection."""
        addr = writer.get_extra_info('peername')
        logger.info(f"Client connected: {addr}")
        
        try:
            while self.running:
                # Read command
                data = await reader.readuntil(MESSAGE_DELIMITER)
                if not data:
                    break
                
                message = data.decode().strip()
                logger.info(f"← Command: {message[:100]}")
                
                # Parse and execute
                cmd = Command.from_json(message)
                response = await self.handle_command(cmd)
                
                # Send response
                response_data = response.to_json() + "\n"
                writer.write(response_data.encode())
                await writer.drain()
                logger.info(f"→ Response: {response.status}")
        
        except asyncio.IncompleteReadError:
            logger.info(f"Client disconnected: {addr}")
        except Exception as e:
            logger.error(f"Error handling client: {e}")
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def start_server(self):
        """Start TCP server."""
        logger.info(f"Starting bridge server on {BRIDGE_HOST}:{BRIDGE_PORT}")
        
        server = await asyncio.start_server(
            self.handle_client,
            BRIDGE_HOST,
            BRIDGE_PORT
        )
        
        logger.info("✓ Bridge server ready")
        logger.info("")
        logger.info("=" * 60)
        logger.info("Bridge is running - waiting for workflow commands...")
        logger.info("=" * 60)
        logger.info("")
        
        self.running = True
        
        async with server:
            await server.serve_forever()
    
    async def run(self):
        """Main bridge run loop."""
        try:
            await self.start_chrome()
            await self.start_server()
        except KeyboardInterrupt:
            logger.info("\nShutdown requested")
        finally:
            if self.playwright:
                await self.playwright.stop()
            logger.info("Bridge stopped")


async def main():
    bridge = BridgeServer()
    await bridge.run()


if __name__ == "__main__":
    asyncio.run(main())
