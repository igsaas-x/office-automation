from dataclasses import dataclass
from typing import Optional

@dataclass
class RecordAllowanceRequest:
    employee_id: int
    amount: float
    allowance_type: str
    created_by: str
    note: Optional[str] = None

@dataclass
class AllowanceResponse:
    id: int
    employee_id: int
    amount: float
    allowance_type: str
    note: Optional[str]
    created_by: str
    timestamp: str
