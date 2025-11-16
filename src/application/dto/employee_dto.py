from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class RegisterEmployeeRequest:
    telegram_id: str
    name: str
    phone: Optional[str] = None
    role: Optional[str] = None
    date_start_work: Optional[str] = None  # Will be parsed to datetime
    probation_months: Optional[int] = None
    base_salary: Optional[float] = None
    bonus: Optional[float] = None

@dataclass
class EmployeeResponse:
    id: int
    telegram_id: str
    name: str
    phone: Optional[str] = None
    role: Optional[str] = None
    date_start_work: Optional[str] = None
    probation_months: Optional[int] = None
    base_salary: Optional[float] = None
    bonus: Optional[float] = None
    created_at: Optional[str] = None
