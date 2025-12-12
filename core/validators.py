import re
from typing import Tuple


PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]$"


def normalize_pan(pan: str) -> str:
    """Normalize PAN input to uppercase and strip whitespace."""
    if not isinstance(pan, str):
        return ""
    return pan.strip().upper()


def is_valid_pan(pan: str) -> bool:
    """Validate PAN using regex after normalization."""
    pan = normalize_pan(pan)
    return bool(re.match(PAN_REGEX, pan))


def parse_int(value: str) -> Tuple[bool, int]:
    """
    Try to parse an integer from a string.
    Returns (success, value_or_0)
    Allows commas in numbers (e.g., '1,00,000').
    """
    if value is None:
        return False, 0
    try:
        # remove commas and whitespace
        cleaned = str(value).replace(",", "").strip()
        num = int(float(cleaned))
        return True, num
    except Exception:
        return False, 0


def is_reasonable_loan_request(requested: int, hard_limit: int) -> bool:
    """
    Consider a request unreasonable if it's more than 2x the hard limit.
    """
    if hard_limit is None:
        return False
    return requested <= 2 * hard_limit


def sanitize_text(value: str) -> str:
    """Minimal sanitization for display (strip leading/trailing spaces)."""
    if value is None:
        return ""
    return str(value).strip()
