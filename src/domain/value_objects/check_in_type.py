from enum import Enum

class CheckInType(str, Enum):
    """Enum for check-in types"""
    CHECKIN = 'checkin'
    CHECKOUT = 'checkout'
