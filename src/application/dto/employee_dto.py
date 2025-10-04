from dataclasses import dataclass

@dataclass
class RegisterEmployeeRequest:
    telegram_id: str
    name: str

@dataclass
class EmployeeResponse:
    id: int
    telegram_id: str
    name: str
