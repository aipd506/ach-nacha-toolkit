"""ABA Routing Transit Number (RTN) check-digit verification and generation."""

import random
from typing import Tuple

# Federal Reserve 9-digit routing weights: 3, 7, 1, 3, 7, 1, 3, 7, 1
WEIGHTS = [3, 7, 1, 3, 7, 1, 3, 7]


def calculate_aba_check_digit(first_eight_digits: str) -> str:
    """Calculate the 9th check digit of an ABA routing number."""
    clean = first_eight_digits.strip()
    if len(clean) != 8 or not clean.isdigit():
        raise ValueError(f"Expected 8 numeric digits, got '{first_eight_digits}'")

    s = sum(int(clean[i]) * WEIGHTS[i] for i in range(8))
    remainder = s % 10
    check_digit = (10 - remainder) % 10
    return str(check_digit)


def validate_aba_routing(routing: str) -> Tuple[bool, str]:
    """Validate a 9-digit ABA routing transit number using the Federal Reserve checksum."""
    clean = routing.strip()
    if len(clean) != 9:
        return False, f"ABA routing number must be 9 digits, found {len(clean)}"
    if not clean.isdigit():
        return False, "ABA routing number must contain only digits"

    expected_check = calculate_aba_check_digit(clean[:8])
    if clean[8] != expected_check:
        return False, f"Invalid ABA check digit: expected {expected_check}, found {clean[8]}"

    return True, "Valid"


def generate_valid_routing() -> str:
    """Generate a mathematically valid synthetic 9-digit ABA routing transit number."""
    # Common Fed districts: 01 to 12 or 21 to 32
    prefix = f"{random.choice([1, 2, 7, 12]):02d}"
    middle = f"{random.randint(100000, 999999):06d}"
    first_eight = prefix + middle
    check = calculate_aba_check_digit(first_eight)
    return first_eight + check
