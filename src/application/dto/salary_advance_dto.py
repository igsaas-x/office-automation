from dataclasses import dataclass
from typing import Optional

@dataclass
class SalaryAdvanceRequest:
    employee_name: str
    amount: float
    created_by: str
    note: Optional[str] = None

@dataclass
class SalaryAdvanceResponse:
    success: bool
    message: str
    employee_name: str
    amount: str
    timestamp: str
