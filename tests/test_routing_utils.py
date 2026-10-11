"""Unit tests for ABA Routing Transit Number check-digit engine."""

import unittest
from ach_nacha_toolkit.routing_utils import (
    calculate_aba_check_digit,
    validate_aba_routing,
    generate_valid_routing,
)


class TestRoutingUtils(unittest.TestCase):
    def test_known_routing_numbers(self):
        # 071000288 (Federal Reserve Bank of Chicago)
        self.assertEqual(calculate_aba_check_digit("07100028"), "8")
        valid, msg = validate_aba_routing("071000288")
        self.assertTrue(valid, msg)

        # 021000021 (JPMorgan Chase NY)
        self.assertEqual(calculate_aba_check_digit("02100002"), "1")
        valid, msg = validate_aba_routing("021000021")
        self.assertTrue(valid, msg)

    def test_corrupted_routing_fails(self):
        # Corrupt check digit of 071000288 -> 071000289
        valid, msg = validate_aba_routing("071000289")
        self.assertFalse(valid)
        self.assertIn("Invalid ABA check digit", msg)

    def test_generated_routing_is_valid(self):
        for _ in range(10):
            rtn = generate_valid_routing()
            self.assertEqual(len(rtn), 9)
            valid, msg = validate_aba_routing(rtn)
            self.assertTrue(valid, f"Generated RTN {rtn} was invalid: {msg}")


if __name__ == "__main__":
    unittest.main()
