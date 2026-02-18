"""Logic for making decisions about appointments."""

import logging
from datetime import datetime, time
from typing import List, Optional

from config.settings import PREFERRED_HOURS

logger = logging.getLogger(__name__)


class AppointmentDecisionMaker:
    """Makes intelligent decisions about which appointments to book."""
    
    def __init__(self, preferred_times: Optional[List[str]] = None):
        """Initialize decision maker.
        
        Args:
            preferred_times: List of preferred appointment times (e.g., ["09:00", "14:00"])
        """
        self.preferred_times = preferred_times or PREFERRED_HOURS
    
    def filter_by_time(self, appointments: List[dict]) -> List[dict]:
        """Filter appointments by preferred times.
        
        Args:
            appointments: List of appointment dictionaries
            
        Returns:
            List of filtered appointments
        """
        filtered = []
        
        for appointment in appointments:
            time_str = appointment.get('time', '')
            
            # Extract time from string (handles various formats)
            for preferred_time in self.preferred_times:
                if preferred_time in time_str:
                    filtered.append(appointment)
                    break
        
        logger.info(f"Filtered {len(filtered)} appointments matching preferred times")
        return filtered
    
    def filter_by_doctor(self, appointments: List[dict], doctor_names: List[str]) -> List[dict]:
        """Filter appointments by doctor names.
        
        Args:
            appointments: List of appointment dictionaries
            doctor_names: List of acceptable doctor names
            
        Returns:
            List of filtered appointments
        """
        filtered = []
        
        for appointment in appointments:
            doctor = appointment.get('doctor', '')
            
            for doctor_name in doctor_names:
                if doctor_name.lower() in doctor.lower():
                    filtered.append(appointment)
                    break
        
        logger.info(f"Filtered {len(filtered)} appointments matching preferred doctors")
        return filtered
    
    def rank_appointments(self, appointments: List[dict]) -> List[dict]:
        """Rank appointments by preference.
        
        Args:
            appointments: List of appointment dictionaries
            
        Returns:
            Sorted list of appointments (best first)
        """
        def get_time_score(appointment: dict) -> int:
            """Calculate score based on preferred time."""
            time_str = appointment.get('time', '')
            
            for i, preferred_time in enumerate(self.preferred_times):
                if preferred_time in time_str:
                    return len(self.preferred_times) - i  # Higher score for earlier preferences
            
            return 0
        
        # Sort by time score (descending)
        ranked = sorted(appointments, key=get_time_score, reverse=True)
        
        logger.info(f"Ranked {len(ranked)} appointments")
        return ranked
    
    def select_best_appointment(
        self,
        appointments: List[dict],
        doctor_names: Optional[List[str]] = None
    ) -> Optional[dict]:
        """Select the best appointment based on criteria.
        
        Args:
            appointments: List of available appointments
            doctor_names: Optional list of preferred doctor names
            
        Returns:
            Best appointment or None if no suitable appointments found
        """
        if not appointments:
            logger.info("No appointments available")
            return None
        
        # Filter by preferred times
        filtered = self.filter_by_time(appointments)
        
        # Filter by doctors if specified
        if doctor_names:
            filtered = self.filter_by_doctor(filtered, doctor_names)
        
        # If no matches after filtering, use original list
        if not filtered:
            logger.warning("No appointments match preferences, considering all options")
            filtered = appointments
        
        # Rank and select best
        ranked = self.rank_appointments(filtered)
        
        if ranked:
            best = ranked[0]
            logger.info(f"Selected best appointment: {best['time']} with {best['doctor']}")
            return best
        
        return None
