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

## Implementation Phases

1. **Phase 1**: Basic login automation with Playwright
2. **Phase 2**: Navigate to appointment section
3. **Phase 3**: Parse available slots (DOM scraping or AI vision)
4. **Phase 4**: Apply your criteria (date ranges, doctors, etc.)
5. **Phase 5**: Book appointment or notify you

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
