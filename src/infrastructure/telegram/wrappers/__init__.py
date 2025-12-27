"""
Telegram Bot Handler Wrappers

This package contains wrapper modules that organize bot handlers by functionality.
Each module exports a factory function that creates wrapper functions for specific handlers.
"""

from .employee_wrappers import create_employee_wrappers
from .salary_wrappers import create_salary_wrappers
from .registration_wrappers import create_registration_wrappers
from .menu_wrappers import create_menu_wrappers
from .setup_wrappers import create_setup_wrappers
from .vehicle_operations_wrappers import create_vehicle_operations_wrappers
from .report_wrappers import create_report_wrappers

__all__ = [
    'create_employee_wrappers',
    'create_salary_wrappers',
    'create_registration_wrappers',
    'create_menu_wrappers',
    'create_setup_wrappers',
    'create_vehicle_operations_wrappers',
    'create_report_wrappers',
]
