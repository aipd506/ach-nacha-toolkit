"""Unit tests for NACHA returns engine and reason code mapping."""

import unittest
from ach_nacha_toolkit.generator import generate_synthetic_ach, serialize_ach_file
from ach_nacha_toolkit.returns import generate_return_file
from ach_nacha_toolkit.validator import ACHValidator


class TestReturns(unittest.TestCase):
    def test_generate_return_file(self):
        orig_ach = generate_synthetic_ach(count=2, amount_per_entry_cents=50000)
        return_ach = generate_return_file(orig_ach, reason_code="R01")

        # Each return entry must have Addenda indicator '1' and Record 7 Type 99
        self.assertEqual(len(return_ach.batches), 1)
        batch = return_ach.batches[0]
        self.assertEqual(batch.header.company_entry_description, "RETURN")
        self.assertEqual(len(batch.entries), 2)

        for e in batch.entries:
            self.assertEqual(e.addenda_indicator, "1")
            self.assertIsNotNone(e.addenda)
            self.assertEqual(e.addenda.addenda_type_code, "99")
            self.assertTrue(e.addenda.payment_related_info.startswith("R01"))

        # Check total entries in batch control includes addenda (2 entries + 2 addenda = 4)
        self.assertEqual(batch.control.entry_addenda_count, 4)

        # Validate with ACHValidator
        validator = ACHValidator()
        res = validator.validate_file(return_ach)
        self.assertTrue(res.is_valid, f"Validation failed: {res.errors}")


if __name__ == "__main__":
    unittest.main()
