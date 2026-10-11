"""Unit tests for the nachatool CLI."""

import unittest
import tempfile
from pathlib import Path
from ach_nacha_toolkit.cli import main


class TestCLI(unittest.TestCase):
    def test_cli_full_workflow(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ach_path = Path(tmpdir) / "test_payroll.ach"
            ret_path = Path(tmpdir) / "return.ach"

            # 1. Routing calculation
            ret_rtn = main(["routing", "071000288"])
            self.assertEqual(ret_rtn, 0)

            # 2. Generate ACH file
            ret_gen = main(["generate", "--sec", "PPD", "-c", "3", "--amount", "2500", "-o", str(ach_path)])
            self.assertEqual(ret_gen, 0)
            self.assertTrue(ach_path.exists())

            # 3. Parse ACH file
            ret_parse = main(["parse", str(ach_path)])
            self.assertEqual(ret_parse, 0)

            # 4. Validate ACH file
            ret_val = main(["validate", str(ach_path)])
            self.assertEqual(ret_val, 0)

            # 5. Return ACH file
            ret_ret = main(["return", str(ach_path), "--reason", "R01", "-o", str(ret_path)])
            self.assertEqual(ret_ret, 0)
            self.assertTrue(ret_path.exists())

            # 6. Validate Return ACH file
            ret_val_ret = main(["validate", str(ret_path)])
            self.assertEqual(ret_val_ret, 0)


if __name__ == "__main__":
    unittest.main()
