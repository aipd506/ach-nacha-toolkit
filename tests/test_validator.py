"""Unit tests for NACHA mathematical validation and tamper detection."""

import unittest
from ach_nacha_toolkit.generator import generate_synthetic_ach, serialize_ach_file
from ach_nacha_toolkit.validator import ACHValidator


class TestValidator(unittest.TestCase):
    def setUp(self):
        self.validator = ACHValidator()

    def test_valid_file_passes(self):
        ach = generate_synthetic_ach(count=5, amount_per_entry_cents=200000, sec_code="PPD")
        res = self.validator.validate_file(ach)
        self.assertTrue(res.is_valid, f"Validation failed: {res.errors}")
        self.assertEqual(res.entry_count, 5)

    def test_corrupted_hash_detected(self):
        ach = generate_synthetic_ach(count=2)
        # Tamper batch entry hash
        ach.batches[0].control.entry_hash = 9999999999
        res = self.validator.validate_file(ach)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Entry hash mismatch" in err for err in res.errors))

    def test_corrupted_credits_detected(self):
        ach = generate_synthetic_ach(count=2)
        # Tamper batch total credits
        ach.batches[0].control.total_credit_cents = 12345
        res = self.validator.validate_file(ach)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("Total credits mismatch" in err for err in res.errors))

    def test_raw_text_invalid_line_length(self):
        ach = generate_synthetic_ach(count=1)
        raw = serialize_ach_file(ach)
        # Truncate first line
        tampered = raw[:50] + "\n" + raw[95:]
        res = self.validator.validate_raw(tampered)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("length" in err for err in res.errors))


if __name__ == "__main__":
    unittest.main()
