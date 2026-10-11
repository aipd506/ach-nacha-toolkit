"""Unit tests for NACHA file generation and 94-char fixed-width compliance."""

import unittest
from ach_nacha_toolkit.generator import generate_synthetic_ach, serialize_ach_file
from ach_nacha_toolkit.models import RECORD_LEN


class TestGenerator(unittest.TestCase):
    def test_generate_and_serialize_compliance(self):
        ach = generate_synthetic_ach(count=3, amount_per_entry_cents=250000, sec_code="PPD")
        text = serialize_ach_file(ach, pad_blocks=True)
        lines = text.splitlines()

        # All lines must be exactly 94 chars
        for idx, line in enumerate(lines, start=1):
            self.assertEqual(len(line), RECORD_LEN, f"Line {idx} length {len(line)} != {RECORD_LEN}")

        # Total line count must be multiple of 10
        self.assertEqual(len(lines) % 10, 0, f"Total lines {len(lines)} not multiple of 10")

        # First line is Record 1
        self.assertEqual(lines[0][0], "1")
        # Second line is Record 5
        self.assertEqual(lines[1][0], "5")
        # Has Record 6 entries
        entry_lines = [l for l in lines if l[0] == "6"]
        self.assertEqual(len(entry_lines), 3)


if __name__ == "__main__":
    unittest.main()
