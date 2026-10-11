"""Unit tests for NACHA file parser."""

import unittest
from ach_nacha_toolkit.generator import generate_synthetic_ach, serialize_ach_file
from ach_nacha_toolkit.parser import parse_ach_file


class TestParser(unittest.TestCase):
    def test_roundtrip_parse(self):
        ach = generate_synthetic_ach(count=4, amount_per_entry_cents=100000, sec_code="CCD")
        serialized = serialize_ach_file(ach, pad_blocks=True)

        parsed = parse_ach_file(serialized)

        self.assertEqual(parsed.header.format_code, "1")
        self.assertEqual(len(parsed.batches), 1)
        batch = parsed.batches[0]
        self.assertEqual(batch.header.sec_code, "CCD")
        self.assertEqual(len(batch.entries), 4)

        # Check total credits
        total_credits = sum(e.amount_cents for e in batch.entries)
        self.assertEqual(batch.control.total_credit_cents, total_credits)


if __name__ == "__main__":
    unittest.main()
