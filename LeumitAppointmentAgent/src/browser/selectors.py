"""CSS selectors and locators for Leumit website elements."""


class LeumitSelectors:
    """Centralized selectors for Leumit website elements.
    
    Note: These selectors are placeholders and need to be updated
    based on the actual Leumit website structure.
    """
    
    # Home page selectors
    PERSONAL_AREA_BUTTON = "button:has-text('אזור אישי'), a:has-text('אזור אישי')"
    
    # Login page selectors (exact IDs from Leumit website)
    LOGIN_ID_INPUT = "#TextBoxIdNumForOTP"
    LOGIN_MOBILE_INPUT = "#TextBoxCellphone"
    LOGIN_SUBMIT_BUTTON = "#ButtonSendCellPhoneNew"
    
    # Navigation selectors
    APPOINTMENTS_MENU = "#ctl00_LinkButton3, a:has-text('זימון תורים')"
    NEW_APPOINTMENT_BUTTON = "button:has-text('תור חדש'), a:has-text('קביעת תור')"
    
    # Appointment search selectors
    NEW_SEARCH_BUTTON = "div.appointments_large_button_text, div[onclick*='newSearch']"
    DOCTORS_THERAPISTS_BUTTON = "div.appointments_large_button_text, div[onclick*='doctor'], div[onclick*='Doctor']"
    
    # Search form fields
    SEARCH_DOCTOR_INPUT = "input[placeholder*='תמחום טיפול'], input[placeholder*='חפש']"
    SEARCH_CLINIC_INPUT = "input[placeholder*='הקלד שם רופא'], input[placeholder*='קליניקה']"
    SEARCH_DATE_INPUT = "input[type='date'], input[placeholder*='תאריך']"
    
    # Category selection
    CATEGORY_DOCTOR = "input[value='קבוע למרקם מומומי'], label:has-text('קבוע למרקם')"
    CATEGORY_SMS = "input[value='יישום'], label:has-text('יישום')"
    CATEGORY_DIRECT = "input[value='כיוונית'], label:has-text('כיוונית')"
    
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
