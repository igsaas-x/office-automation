import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedExpense:
    amount_value: float
    currency: str  # USD | KHR | UNKNOWN
    purpose: str
    confidence: float
    raw_text: str


class ExpenseParserClient:
    """Lightweight in-process parser; can be swapped to real LLM later."""

    def __init__(self, default_currency: str = "USD"):
        self.default_currency = default_currency

    def parse_message(self, text: str) -> Optional[ParsedExpense]:
        if not text:
            return None

        normalized = self._to_ascii_digits(text.strip())
        amount = self._extract_amount(normalized)
        if amount is None:
            return None

        currency = self._detect_currency(normalized)
        purpose = self._extract_purpose(normalized, amount)

        if not purpose:
            return ParsedExpense(
                amount_value=amount,
                currency=currency,
                purpose="",
                confidence=0.35,
                raw_text=text
            )

        return ParsedExpense(
            amount_value=amount,
            currency=currency,
            purpose=purpose,
            confidence=0.8,
            raw_text=text
        )

    def _to_ascii_digits(self, text: str) -> str:
        """Convert Khmer digits to ASCII for consistent parsing."""
        khmer_digits = "០១២៣៤៥៦៧៨៩"
        ascii_digits = "0123456789"
        translation = str.maketrans(khmer_digits, ascii_digits)
        return text.translate(translation)

    def _extract_amount(self, text: str) -> Optional[float]:
        """
        Extract the first numeric amount.
        Supports commas, decimals, and shorthand like 10k / 10K.
        """
        amount_pattern = r"(?P<num>(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?)\s*(?P<suffix>[kK])?"
        match = re.search(amount_pattern, text)
        if not match:
            return None

        num_str = match.group("num").replace(",", "")
        suffix = match.group("suffix")
        try:
            value = float(num_str)
            if suffix:
                value *= 1000
            return value
        except ValueError:
            return None

    def _detect_currency(self, text: str) -> str:
        lowered = text.lower()
        if "$" in text or "usd" in lowered or "dollar" in lowered:
            return "USD"
        if "៛" in text or "riel" in lowered or "khr" in lowered:
            return "KHR"
        return self.default_currency if self.default_currency else "UNKNOWN"

    def _extract_purpose(self, text: str, amount: float) -> str:
        """Remove amount and currency markers to get a concise purpose."""
        amount_pattern = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?\s*[kK]?"
        currency_pattern = r"(\$|usd|dollar|៛|riel|khr)"

        cleaned = re.sub(amount_pattern, " ", text, flags=re.IGNORECASE)
        cleaned = re.sub(currency_pattern, " ", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip(" -,:")

        # Short strings like "for" are not useful
        if len(cleaned) < 3:
            return ""
        return cleaned
