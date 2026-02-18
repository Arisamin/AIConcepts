"""CSS selectors and locators for Leumit website elements."""


class LeumitSelectors:
    """Centralized selectors for Leumit website elements.
    
    Note: These selectors are placeholders and need to be updated
    based on the actual Leumit website structure.
    """
    
    # Home page selectors
    PERSONAL_AREA_BUTTON = "button:has-text('אזור אישי'), a:has-text('אזור אישי')"
    
    # Login page selectors (using Hebrew placeholders)
    LOGIN_ID_INPUT = "input[placeholder*='תעודת זהות'], input[placeholder*='זהות']"
    LOGIN_MOBILE_INPUT = "input[placeholder*='מספר נייד'], input[placeholder*='נייד']"
    LOGIN_SUBMIT_BUTTON = "button[type='submit'], button:has-text('כניסה'), button:has-text('התחבר')"
    
    # Navigation selectors
    APPOINTMENTS_MENU = "a[href*='appointment'], button:has-text('תורים')"
    NEW_APPOINTMENT_BUTTON = "button:has-text('תור חדש'), a:has-text('קביעת תור')"
    
    # Appointment search selectors
    DOCTOR_SELECT = "select[name='doctor'], #doctor-select"
    DATE_PICKER = "input[type='date'], .date-picker"
    SEARCH_BUTTON = "button:has-text('חפש'), button[type='submit']"
    
    # Results selectors
    AVAILABLE_SLOTS = ".appointment-slot, .time-slot"
    SLOT_TIME = ".slot-time, .appointment-time"
    SLOT_DOCTOR = ".slot-doctor, .doctor-name"
    BOOK_BUTTON = "button:has-text('קבע'), button.book-appointment"
    
    # Confirmation selectors
    CONFIRM_BUTTON = "button:has-text('אשר'), button.confirm"
    SUCCESS_MESSAGE = ".success-message, .confirmation"
    
    @staticmethod
    def get_selector_by_text(text: str) -> str:
        """Generate a selector that finds elements by text content."""
        return f":text('{text}')"
