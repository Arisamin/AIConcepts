"""Configuration settings for the Leumit Appointment Agent."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent.parent
SCREENSHOTS_DIR = BASE_DIR / "screenshots"
LOGS_DIR = BASE_DIR / "logs"

# Ensure directories exist
SCREENSHOTS_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Leumit website settings
LEUMIT_BASE_URL = "https://www.leumit.co.il"
LEUMIT_HOME_URL = LEUMIT_BASE_URL

# Browser settings
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
BROWSER_TIMEOUT = int(os.getenv("BROWSER_TIMEOUT", "30000"))
VIEWPORT_WIDTH = 1920
VIEWPORT_HEIGHT = 1080

# Retry settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Appointment search settings
SEARCH_DAYS_AHEAD = 30  # How many days to look ahead
PREFERRED_HOURS = ["09:00", "10:00", "11:00", "14:00", "15:00"]  # Preferred appointment times

# Logging settings
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
