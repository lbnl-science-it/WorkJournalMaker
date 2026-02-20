# ABOUTME: Timezone detection, conversion, and formatting utilities.
# ABOUTME: Provides consistent local-time display across the web interface.
"""
Timezone utilities for handling system timezone detection and conversions.
Ensures all dates display correctly in the system's local timezone.
"""

import time
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import os


class TimezoneManager:
    """Manages timezone detection and conversion for the application."""
    
    def __init__(self):
        self._system_timezone = None
        self._detect_system_timezone()
    
    def _detect_system_timezone(self):
        """Detect the system's local timezone."""
        try:
            # Method 1: Use time.tzname and time.timezone
            if time.daylight:
                # Daylight saving time is in effect
                offset_seconds = -time.altzone
                tz_name = time.tzname[1]
            else:
                # Standard time
                offset_seconds = -time.timezone
                tz_name = time.tzname[0]
            
            # Create timezone object
            offset_hours = offset_seconds / 3600
            self._system_timezone = timezone(timedelta(hours=offset_hours))
            
            print(f"Detected system timezone: {tz_name} (UTC{offset_hours:+.1f})")
            
        except Exception as e:
            print(f"Failed to detect system timezone: {e}")
            # Fallback to UTC
            self._system_timezone = timezone.utc
    
    def get_system_timezone(self) -> timezone:
        """Get the system's timezone object."""
        return self._system_timezone
    
    def now_local(self) -> datetime:
        """Get current datetime in system timezone."""
        return datetime.now(self._system_timezone)
    
    def now_utc(self) -> datetime:
        """Get current datetime in UTC."""
        return datetime.now(timezone.utc)
    
    def to_local(self, dt: datetime) -> datetime:
        """Convert datetime to system timezone."""
        if dt is None:
            return None
        
        # If datetime is naive, assume it's in UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # Convert to system timezone
        return dt.astimezone(self._system_timezone)
    
    def to_utc(self, dt: datetime) -> datetime:
        """Convert datetime to UTC."""
        if dt is None:
            return None
        
        # If datetime is naive, assume it's in system timezone
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=self._system_timezone)
        
        # Convert to UTC
        return dt.astimezone(timezone.utc)
    
    def format_local_datetime(self, dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
        """Format datetime in system timezone."""
        if dt is None:
            return ""
        
        local_dt = self.to_local(dt)
        return local_dt.strftime(format_str)
    
    def format_local_date(self, dt: datetime, format_str: str = "%Y-%m-%d") -> str:
        """Format date part in system timezone."""
        if dt is None:
            return ""
        
        local_dt = self.to_local(dt)
        return local_dt.strftime(format_str)
    
    def get_timezone_info(self) -> dict:
        """Get timezone information for debugging."""
        now_local = self.now_local()
        now_utc = self.now_utc()
        
        return {
            "system_timezone": str(self._system_timezone),
            "current_local_time": now_local.isoformat(),
            "current_utc_time": now_utc.isoformat(),
            "local_date": now_local.date().isoformat(),
            "utc_date": now_utc.date().isoformat(),
            "offset_hours": now_local.utcoffset().total_seconds() / 3600,
            "timezone_name": time.tzname,
            "daylight_saving": time.daylight
        }
    
    def create_timezone_aware_datetime(self, year: int, month: int, day: int, 
                                     hour: int = 0, minute: int = 0, second: int = 0) -> datetime:
        """Create a timezone-aware datetime in system timezone."""
        return datetime(year, month, day, hour, minute, second, tzinfo=self._system_timezone)


# Global timezone manager instance
timezone_manager = TimezoneManager()


def get_timezone_manager() -> TimezoneManager:
    """Get the global timezone manager instance."""
    return timezone_manager


def now_local() -> datetime:
    """Convenience function to get current local time."""
    return timezone_manager.now_local()


def now_utc() -> datetime:
    """Convenience function to get current UTC time."""
    return timezone_manager.now_utc()


def to_local(dt: datetime) -> datetime:
    """Convenience function to convert datetime to local timezone."""
    return timezone_manager.to_local(dt)


def to_utc(dt: datetime) -> datetime:
    """Convenience function to convert datetime to UTC."""
    return timezone_manager.to_utc(dt)


def format_local_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Convenience function to format datetime in local timezone."""
    return timezone_manager.format_local_datetime(dt, format_str)


def format_local_date(dt: datetime, format_str: str = "%Y-%m-%d") -> str:
    """Convenience function to format date in local timezone."""
    return timezone_manager.format_local_date(dt, format_str)