"""
Test scenarios with mock browser responses for integration testing.
Each scenario simulates a specific workflow path with canned responses.
"""
from mock_browser import MockBrowser, MockElement, MockFrame


def scenario_fresh_login_to_sms_validation():
    """
    Scenario: Fresh login → SMS validation reached
    Steps: 1-6 (login steps), Step 0-7 (search), Steps 18-24 (approval loop)
    Expected: SMS validation screen reached
    
    NOTE: This scenario represents the state AFTER login has been completed.
    When search_doctor is called, agent is already logged in (zimun torim button visible).
    """
    return {
        "name": "fresh_login_to_sms_validation",
        "url": "https://www.leumit.co.il",
        "frames": [],
        "elements": {
            # Login state check - AFTER successful login
            "button:has-text('זימון תורים')": MockElement(text="זימון תורים", visible=True),
            "button:has-text('אזור אישי')": MockElement(text="אזור אישי", visible=False),
            
            # Search flow step 2: Click "בצע חיפוש חדש"
            "div.appointments_large_button_text[onclick='newSearch()']": MockElement(text="בצע חיפוש חדש", visible=True),
            "div.appointments_large_button_text:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            "div.appointments_large_button:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            "div:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            
            # Search flow step 3: Click "רופאים ומטפלים"
            "input[type='radio'][value*='doctor']": MockElement(visible=True),
            "input[type='radio'][value*='Doctor']": MockElement(visible=True),
            "label:has-text('רופאים ומטפלים')": MockElement(text="רופאים ומטפלים", visible=True),
            "*:has-text('רופאים ומטפלים')": MockElement(text="רופאים ומטפלים", visible=True),
            
            # Search flow step 4: Select specialty
            "input.select2-input": MockElement(visible=True),
            "li.select2-result": MockElement(text="עיניים", visible=True),
            "li.select2-result:has-text('עיניים')": MockElement(text="עיניים", visible=True),
            
            # Search flow step 5: Select subcategory  
            "input.select2-search-field": MockElement(visible=True),
            
            # Search flow step 6: Doctor name filter
            "input[placeholder*='חיפוש']": MockElement(visible=True),
            "input[placeholder*='שם רופא']": MockElement(visible=True),
            
            # Search flow step 7: Click search button
            "div:has-text('חפש')": MockElement(text="חפש", visible=True),
            "span:has-text('חפש')": MockElement(text="חפש", visible=True),
            
            # Search flow step 8: Click appointment button
            "span:has-text('זמן תור')": MockElement(text="זמן תור", visible=True),
            "span#ctl00_MainContentPlaceHolder_ucSearchResults_RepeaterDoctorsResults_ctl00_LabelButtonTextForMakingAppointment": MockElement(text="זמן תור", visible=True),
            
            # Calendar flow step 16-17: Appointment calendar
            "#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedDate": MockElement(text="15.03.26", visible=True),
            "#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedTime": MockElement(text="10:00", visible=True),
            "#divCalendarButtonsBoxForDoctor": MockElement(visible=True),
            
            # Step 18-19: Appointment type selection - ALL possible button patterns
            "div#divCalendarButtonsBoxForDoctor .appointments_large_button_blue_2": MockElement(text="זמן לוידאו", visible=True),
            ".appointment_calendar_buttons_box .appointments_large_button_blue_2": MockElement(text="זמן לוידאו", visible=True),
            "div:has-text('זמן לוידאו')": MockElement(text="זמן לוידאו", visible=True),
            "div:has-text('זמן לטלפון')": MockElement(text="זמן לטלפון", visible=True),
            "div:has-text('זמן למרפאה')": MockElement(text="זמן למרפאה", visible=True),
            "span:has-text('זמן לוידאו')": MockElement(text="זמן לוידאו", visible=True),
            "span:has-text('זמן לטלפון')": MockElement(text="זמן לטלפון", visible=True),
            "span:has-text('זמן למרפאה')": MockElement(text="זמן למרפאה", visible=True),
            
            # Step 22+: Approval loop - SMS validation and continuation buttons
            "div.appointments_approve_video_validation_row_1": MockElement(visible=True),
            "div:has-text('ברגעים אלה נשלחת אליך הודעת')": MockElement(text="ברגעים אלה נשלחת אליך הודעת SMS", visible=True),
            "div:has-text('SMS')": MockElement(text="SMS validation code received", visible=True),
            
            # Continuation buttons in approval loop
            "span.button_text:has-text('המשך')": MockElement(text="המשך", visible=True),
            ".appointments_large_button_blue_2:has-text('המשך')": MockElement(text="המשך", visible=True),
            "span.button_text:has-text('שמור וסיים')": MockElement(text="שמור וסיים", visible=True),
            ".appointments_large_button_blue_2:has-text('שמור וסיים')": MockElement(text="שמור וסיים", visible=True),
        }
    }


def scenario_already_logged_in():
    """
    Scenario: Already logged in → skip login
    Steps: 0 (check login state) → proceed to search
    Expected: Search flow executes directly
    """
    return {
        "name": "already_logged_in",
        "url": "https://www.leumit.co.il/",
        "frames": [],
        "elements": {
            # Login state check
            "button:has-text('זימון תורים')": MockElement(text="זימון תורים", visible=True),
            "button:has-text('אזור אישי')": MockElement(text="אזור אישי", visible=False),
            
            # Search flow
            "div:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            "input[placeholder*='חיפוש']": MockElement(),
            "li.select2-result": MockElement(text="בדיקה כללית", visible=True),
            "div:has-text('חפש')": MockElement(text="חפש", visible=True),
            "span:has-text('זמן תור')": MockElement(text="זמן תור", visible=True),
        }
    }


def scenario_date_out_of_range_triggers_fallback():
    """
    Scenario: Appointment date is outside requested range
    Steps: 1-9 (search), 16-17 (validate date), 100-106 (fallback workflow)
    Expected: Fallback workflow triggers, waits 15 minutes, retries
    """
    return {
        "name": "date_out_of_range_triggers_fallback",
        "url": "https://www.leumit.co.il/",
        "frames": [],
        "elements": {
            # Login check
            "button:has-text('זימון תורים')": MockElement(text="זימון תורים", visible=True),
            
            # Search flow
            "div:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            "input[placeholder*='חיפוש']": MockElement(),
            "li.select2-result": MockElement(text="בדיקה כללית", visible=True),
            "div:has-text('חפש')": MockElement(text="חפש", visible=True),
            "span:has-text('זמן תור')": MockElement(text="זמן תור", visible=True),
            
            # Calendar - with OUT OF RANGE date (May 2026, outside Feb-Apr range)
            "#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedDate": MockElement(text="15.05.26"),
            "#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedTime": MockElement(text="10:00"),
            
            # Fallback workflow - page still on calendar after refresh
            "#divCalendarButtonsBoxForDoctor": MockElement(),
        }
    }


def scenario_no_doctors_found():
    """
    Scenario: Search returns no results
    Steps: 1-7 (search)
    Expected: Error state with no appointment button to click
    """
    return {
        "name": "no_doctors_found",
        "url": "https://www.leumit.co.il/",
        "frames": [],
        "elements": {
            "button:has-text('זימון תורים')": MockElement(text="זימון תורים", visible=True),
            "div:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            "input[placeholder*='חיפוש']": MockElement(),
            "li.select2-result": MockElement(text="בדיקה כללית", visible=True),
            "div:has-text('חפש')": MockElement(text="חפש", visible=True),
            # NO זמן תור button - search returned no results
            "span:has-text('זמן תור')": MockElement(text="זמן תור", visible=False),
        }
    }


def scenario_session_expired_during_search():
    """
    Scenario: Session expires during search (זימון תורים button disappears)
    Steps: 0-1 (search start)
    Expected: Error indicating re-login required
    """
    return {
        "name": "session_expired_during_search",
        "url": "https://www.leumit.co.il/",
        "frames": [],
        "elements": {
            "button:has-text('זימון תורים')": MockElement(text="זימון תורים", visible=False),  # Disappeared!
            "button:has-text('אזור אישי')": MockElement(text="אזור אישי", visible=True),  # Back to login
        }
    }


def scenario_appointment_confirmation_reached():
    """
    Scenario: Full flow to appointment confirmation
    Steps: 1-24 (full booking)
    Expected: Success - appointment confirmed
    """
    return {
        "name": "appointment_confirmation_reached",
        "url": "https://www.leumit.co.il/",
        "frames": [],
        "elements": {
            # Login check
            "button:has-text('זימון תורים')": MockElement(text="זימון תורים", visible=True),
            
            # Search flow
            "div:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            "input[placeholder*='חיפוש']": MockElement(),
            "li.select2-result": MockElement(text="בדיקה כללית", visible=True),
            "div:has-text('חפש')": MockElement(text="חפש", visible=True),
            "span:has-text('זמן תור')": MockElement(text="זמן תור", visible=True),
            
            # Calendar - WITHIN RANGE
            "#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedDate": MockElement(text="15.03.26"),
            "#ctl00_MainContentPlaceHolder_ucAppointmentCalendar_LabelSelectedTime": MockElement(text="14:30"),
            
            # Appointment selection
            "div:has-text('זמן לטלפון')": MockElement(text="זמן לטלפון", visible=True),
            ".appointments_large_button_blue_2:has-text('המשך')": MockElement(text="המשך", visible=True),
            ".appointments_large_button_blue_2:has-text('שמור וסיים')": MockElement(text="שמור וסיים", visible=True),
            
            # Confirmation message
            "div:has-text('התור הוזמן בהצלחה')": MockElement(text="התור הוזמן בהצלחה", visible=True),
        }
    }


def scenario_multiple_subspecialties():
    """
    Scenario: Specialty has multiple subcategories
    Steps: 1-5 (search with subcategory selection)
    Expected: Both specialty and subcategory selected successfully
    """
    return {
        "name": "multiple_subspecialties",
        "url": "https://www.leumit.co.il/",
        "frames": [],
        "elements": {
            "button:has-text('זימון תורים')": MockElement(text="זימון תורים", visible=True),
            "div:has-text('בצע חיפוש חדש')": MockElement(text="בצע חיפוש חדש", visible=True),
            
            # Specialty selection
            "input.select2-input": MockElement(),
            "li.select2-result:has-text('כירורגיה')": MockElement(text="כירורגיה", visible=True),
            
            # Subcategory selection (second Select2)
            "input.select2-input:nth(1)": MockElement(),
            "li.select2-result:has-text('כירורגיה פלסטית')": MockElement(text="כירורגיה פלסטית", visible=True),
            
            # Continue with search
            "input[placeholder*='שם רופא']": MockElement(),
            "div:has-text('חפש')": MockElement(text="חפש", visible=True),
        }
    }


def get_scenario(name: str):
    """Get a scenario by name."""
    scenarios = {
        "fresh_login_to_sms_validation": scenario_fresh_login_to_sms_validation,
        "already_logged_in": scenario_already_logged_in,
        "date_out_of_range_triggers_fallback": scenario_date_out_of_range_triggers_fallback,
        "no_doctors_found": scenario_no_doctors_found,
        "session_expired_during_search": scenario_session_expired_during_search,
        "appointment_confirmation_reached": scenario_appointment_confirmation_reached,
        "multiple_subspecialties": scenario_multiple_subspecialties,
    }
    
    if name not in scenarios:
        raise ValueError(f"Unknown scenario: {name}. Available: {list(scenarios.keys())}")
    
    return scenarios[name]()
