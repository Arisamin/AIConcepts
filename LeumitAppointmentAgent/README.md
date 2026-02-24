# Leumit Appointment Agent

An automated tool that logs into your Leumit medical care service provider site and finds appointments for you.

## Architecture Overview

**Browser Automation + AI for intelligent decision-making**

## Core Technologies

### 1. **Playwright**
- Modern, fast, and reliable Chrome automation
- Handles dynamic content, waits, and modern web apps
- Built-in features for screenshots, tracing, debugging

### 2. **Python**
- Rich ecosystem for both automation and AI
- Clean async support for Playwright
- Easy credential management

### 3. **AI Integration**

**Hybrid approach**: DOM-based automation when possible, with AI vision as fallback for complex scenarios

## Project Structure

```
LeumitAppointmentAgent/
├── src/
│   ├── browser/
│   │   ├── automation.py      # Playwright automation logic
│   │   └── selectors.py       # Element selectors/locators
│   ├── ai/
│   │   ├── vision_agent.py    # AI vision analysis
│   │   └── decision_maker.py  # Logic for finding appointments
│   ├── config/
│   │   ├── credentials.py     # Secure credential handling
│   │   └── settings.py        # Configuration
│   └── main.py                # Entry point
├── tests/
├── requirements.txt
└── README.md
```

## Key Components

1. **Credential Management**: Secure credential storage using environment variables
2. **Error Handling**: Robust retry logic, screenshot capture on failures
3. **Logging**: Track actions, decisions, and errors
4. **Scheduling**: Optional automatic scheduling to check for appointments

## Workflow Overview

### Complete Appointment Booking Flow

**Steps 1-8**: Authentication & Navigation
- Step 1: Launch browser with persistent profile
- Step 2: Navigate to Leumit service login page
- Step 3: Google OAuth authentication
- Step 4: Navigate to appointments section (זימון תורים)
- Steps 5-8: Doctor search and selection with error handling

**Step 9: Calendar Date Validation & Retry Logic** ⭐ *Key Update*
- Step 9.1: Wait for calendar to load (2 seconds)
- Step 9.2: Take full-page screenshot
- Step 9.3: Read pre-selected appointment date/time from calendar
- Step 9.4: Validate selected date is within requested range (date_from to date_to)

**Branching Logic Based on Date Validity:**

| Condition | Flow | Actions |
|-----------|------|---------|
| **Date OUTSIDE Range** | Retry Workflow | 9.5a: Refresh page → 9.5b: Screenshot → 9.5c: Wait 15 minutes → 9.5d: Refresh again → 9.5e: Screenshot → 9.5f: Check for "זימון תורים" button |
| **Date WITHIN Range** | Proceed to Booking | Steps 10-11: Select appointment type and process multi-step approval |

**Steps 10-11**: Appointment Booking
- Step 10: Find and click appointment type button (זמן לטלפון/וידאו/מרפאה)
- Step 11: Click through multi-step approval (המשך buttons) until SMS validation

### Key Features

1. **SMS Validation Detection**: Uses visibility checks to prevent false positives from hidden DOM elements
2. **Date Range Validation**: Parses DD.MM.YY format, converts YY→YYYY, validates against date_from/date_to parameters
3. **Session Recovery**: On out-of-range dates, waits 15 minutes and checks for session recovery point
4. **Full-Page Screenshots**: Captures complete page state for debugging
5. **Clear Decision Tree**: Explicit branching logic based on date validity

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Configure credentials in `.env`:
   ```
   LEUMIT_USERNAME=your_username
   LEUMIT_PASSWORD=your_password
   OPENAI_API_KEY=your_api_key  # Optional, for AI features
   ```

3. Run the agent:
   ```bash
   python src/main.py
   ```

## Dependencies

- playwright - Browser automation
- python-dotenv - Environment variable management
- openai - AI vision capabilities (optional)
- beautifulsoup4 - HTML parsing

## Security Notes

- Never commit your `.env` file
- Credentials are stored securely and never logged
- All sensitive actions are logged with timestamps
