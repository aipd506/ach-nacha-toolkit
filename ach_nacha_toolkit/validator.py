"""Validation engine for NACHA ACH files and mathematical invariants."""

from typing import List
from .models import ACHFile, ValidationResult, RECORD_LEN
from .routing_utils import validate_aba_routing


class ACHValidator:
    """Validates structural compliance and mathematical invariants of NACHA files."""

    def __init__(self):
        pass

    def validate_file(self, ach: ACHFile) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        total_batches = len(ach.batches)
        total_entries = 0
        file_calc_debits = 0
        file_calc_credits = 0
        file_calc_hash = 0

        for b_idx, b in enumerate(ach.batches, start=1):
            batch_num = b.header.batch_number
            batch_calc_debits = 0
            batch_calc_credits = 0
            batch_calc_hash = 0
            entry_addenda_count = 0

            for e_idx, e in enumerate(b.entries, start=1):
                entry_addenda_count += 1
                if e.addenda:
                    entry_addenda_count += 1

                # Validate routing number
                full_routing = e.receiving_dfi_id + e.check_digit
                is_valid_rtn, rtn_msg = validate_aba_routing(full_routing)
                if not is_valid_rtn:
                    errors.append(f"Batch {b_idx} Entry {e_idx}: Invalid ABA routing '{full_routing}': {rtn_msg}")

                batch_calc_hash += int(e.receiving_dfi_id)

                if e.transaction_code in ["27", "37"]:
                    batch_calc_debits += e.amount_cents
                elif e.transaction_code in ["22", "32"]:
                    batch_calc_credits += e.amount_cents
                else:
                    warnings.append(f"Batch {b_idx} Entry {e_idx}: Unusual transaction code '{e.transaction_code}'")

            # Check batch control
            if b.control:
                if b.control.batch_number != batch_num:
                    errors.append(f"Batch {b_idx}: Batch number mismatch between header ({batch_num}) and control ({b.control.batch_number})")
                if b.control.entry_addenda_count != entry_addenda_count:
                    errors.append(f"Batch {b_idx}: Entry/Addenda count mismatch: declared {b.control.entry_addenda_count}, counted {entry_addenda_count}")
                if b.control.entry_hash != (batch_calc_hash % (10**10)):
                    errors.append(f"Batch {b_idx}: Entry hash mismatch: declared {b.control.entry_hash}, calculated {batch_calc_hash % (10**10)}")
                if b.control.total_debit_cents != batch_calc_debits:
                    errors.append(f"Batch {b_idx}: Total debits mismatch: declared {b.control.total_debit_cents}, calculated {batch_calc_debits}")
                if b.control.total_credit_cents != batch_calc_credits:
                    errors.append(f"Batch {b_idx}: Total credits mismatch: declared {b.control.total_credit_cents}, calculated {batch_calc_credits}")
            else:
                errors.append(f"Batch {b_idx}: Missing mandatory Batch Control Record (Record 8)")

            total_entries += entry_addenda_count
            file_calc_debits += batch_calc_debits
            file_calc_credits += batch_calc_credits
            file_calc_hash += batch_calc_hash

        # Check file control
        if ach.control:
            if ach.control.batch_count != total_batches:
                errors.append(f"File Control: Batch count mismatch: declared {ach.control.batch_count}, found {total_batches}")
            if ach.control.entry_addenda_count != total_entries:
                errors.append(f"File Control: Entry/Addenda count mismatch: declared {ach.control.entry_addenda_count}, calculated {total_entries}")
            if ach.control.entry_hash != (file_calc_hash % (10**10)):
                errors.append(f"File Control: Entry hash mismatch: declared {ach.control.entry_hash}, calculated {file_calc_hash % (10**10)}")
            if ach.control.total_debit_cents != file_calc_debits:
                errors.append(f"File Control: Total debits mismatch: declared {ach.control.total_debit_cents}, calculated {file_calc_debits}")
            if ach.control.total_credit_cents != file_calc_credits:
                errors.append(f"File Control: Total credits mismatch: declared {ach.control.total_credit_cents}, calculated {file_calc_credits}")
        else:
            errors.append("File Control: Missing mandatory File Control Record (Record 9)")

        return ValidationResult(
            is_valid=len(errors) == 0,
            batch_count=total_batches,
            entry_count=total_entries,
            total_debits_cents=file_calc_debits,
            total_credits_cents=file_calc_credits,
            entry_hash=file_calc_hash % (10**10),
            errors=errors,
            warnings=warnings,
        )

    def validate_raw(self, raw_text: str) -> ValidationResult:
        lines = [l.rstrip("\r\n") for l in raw_text.splitlines() if l.strip()]
        for idx, line in enumerate(lines, start=1):
            if len(line) != RECORD_LEN:
                return ValidationResult(
                    is_valid=False,
                    errors=[f"Line {idx} length {len(line)} != {RECORD_LEN}"],
                )
        from .parser import parse_ach_file
        try:
            ach = parse_ach_file(raw_text)
        except Exception as e:
            return ValidationResult(is_valid=False, errors=[f"Parse failure: {e}"])
        return self.validate_file(ach)
