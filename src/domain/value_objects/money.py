from dataclasses import dataclass
from decimal import Decimal

@dataclass(frozen=True)
class Money:
    amount: Decimal

    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Amount cannot be negative")

    @classmethod
    def from_float(cls, value: float) -> 'Money':
        return cls(Decimal(str(value)))

    def __str__(self):
        return f"${self.amount:.2f}"
