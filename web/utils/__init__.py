"""
Web utilities package for timezone handling, resource path resolution, and other common functions.
"""

from .timezone_utils import (
    TimezoneManager,
    get_timezone_manager,
    now_local,
    now_utc,
    to_local,
    to_utc,
    format_local_datetime,
    format_local_date
)

# Import resource_path from the parent directory
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from resource_utils import resource_path

__all__ = [
    'TimezoneManager',
    'get_timezone_manager',
    'now_local',
    'now_utc',
    'to_local',
    'to_utc',
    'format_local_datetime',
    'format_local_date',
    'resource_path'
]