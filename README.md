# ach-nacha-toolkit

US Automated Clearing House (NACHA) 94-character fixed-width file generator, parser, validator, and returns handler.

Provides an enterprise-grade toolkit for generating, parsing, and validating NACHA ACH files across direct deposit payrolls, vendor disbursements, consumer bill debits, and automated payment return processing.

## Key Capabilities

1. 94-Character Fixed-Width Record Support:
   - Record 1: File Header Record (Destination, Origin, Format Code, Reference).
   - Record 5: Company / Batch Header Record (SEC codes: PPD, CCD, WEB, TEL).
   - Record 6: Entry Detail Record (Transaction codes: 22 Checking Credit, 27 Checking Debit, 32 Savings Credit, 37 Savings Debit).
   - Record 7: Addenda Record (Type 05 standard payment details, Type 99 payment returns).
   - Record 8: Batch Control Record (Entry hash, debit/credit totals, count).
   - Record 9: File Control Record (Batch count, block count, file totals).
2. Blocking Factor 10 Engine: Automatically calculates block counts and pads files with 94-character '9' filler lines conforming to Federal Reserve and EPN clearing standards.
3. ABA Routing Transit Check-Digit Algorithm: Validates and generates Federal Reserve 9-digit routing transit numbers using the official weighting algorithm `(3, 7, 1, 3, 7, 1, 3, 7) mod 10`.
4. Automated Return File Generator: Generates standard NACHA return files with Record 7 Type 99 for standard return codes (e.g. `R01` Insufficient Funds, `R02` Account Closed, `R03` Unable to Locate Account, `R08` Payment Stopped, `R10` Unauthorized).
5. Mathematical Invariant Verification: Cross-reconciles entry counts, debit/credit dollar sums, and 10-digit entry hashes across batch and file controls.
6. Zero External Dependencies: Pure Python standard library with zero runtime dependencies.

## Installation

```bash
pip install ach-nacha-toolkit
```

Or install locally in editable mode:

```bash
git clone https://github.com/aipd506/ach-nacha-toolkit.git
cd ach-nacha-toolkit
pip install -e .
```

## Quick Start

### 1. Generate Synthetic Direct Deposit Payroll ACH File

```bash
nachatool generate --sec PPD --count 10 --amount 3250.00 --company "ACME CORP" -o payroll.ach
```

### 2. Parse and Inspect ACH File

```bash
nachatool parse payroll.ach
```

Output:
```text
============================================================
NACHA ACH File Summary: payroll.ach
============================================================
Destination:  FEDERAL RESERVE BANK (071000288)
Origin:       ACME CORP (112345678)
Created:      20261011 2004
Batches:      1
  Batch 1: SEC=PPD Company=ACME CORP Entries=10
Total Debits:   $0.00
Total Credits:  $32950.00
Block Count:    2
============================================================
```

### 3. Validate File Compliance and Entry Hash

```bash
nachatool validate payroll.ach
```

Output:
```text
Validation Status: PASSED
Batch Count:       1
Total Entries:     10
Total Debits:      $0.00
Total Credits:     $32950.00
Entry Hash:        2109847120
```

### 4. Generate Automated Return File (e.g. R01 Insufficient Funds)

```bash
nachatool return payroll.ach --reason R01 -o payroll_returns.ach
```

### 5. Validate ABA Routing Number

```bash
nachatool routing 071000288
```

Output:
```text
Routing 071000288: VALID (Valid)
```

## Python API Usage

```python
from ach_nacha_toolkit import generate_synthetic_ach, serialize_ach_file, parse_ach_file, ACHValidator

# Generate ACH File
ach = generate_synthetic_ach(count=5, amount_per_entry_cents=150000, sec_code="PPD")
raw_text = serialize_ach_file(ach, pad_blocks=True)

# Parse ACH File
parsed_ach = parse_ach_file(raw_text)

# Validate File
validator = ACHValidator()
result = validator.validate_file(parsed_ach)

assert result.is_valid
print(f"Validated {result.entry_count} entries totalling ${result.total_credits_cents / 100:.2f}")
```

## License

Apache-2.0
