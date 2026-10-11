"""Data models for NACHA ACH 94-character fixed-width files and records."""

from dataclasses import dataclass, field, asdict
from decimal import Decimal
from typing import List, Optional, Dict, Any
import json
import math

RECORD_LEN = 94


@dataclass
class FileHeaderRecord:
    immediate_destination: str = " 071000288"  # 10 chars
    immediate_origin: str = " 123456789"       # 10 chars
    file_creation_date: str = "261011"         # 6 chars (YYMMDD)
    file_creation_time: str = "1200"           # 4 chars (HHMM)
    file_id_modifier: str = "A"                # 1 char
    record_size: str = "094"                   # 3 chars
    blocking_factor: str = "10"                # 2 chars
    format_code: str = "1"                     # 1 char
    immediate_destination_name: str = "FEDERAL RESERVE BANK"   # 23 chars
    immediate_origin_name: str = "ORIGINATING BANK CORP"       # 23 chars
    reference_code: str = "00000000"           # 8 chars

    def format(self) -> str:
        line = (
            "1"
            + "01"
            + f"{self.immediate_destination[:10]:>10}"
            + f"{self.immediate_origin[:10]:>10}"
            + f"{self.file_creation_date[:6]:6}"
            + f"{self.file_creation_time[:4]:4}"
            + f"{self.file_id_modifier[:1]:1}"
            + f"{self.record_size[:3]:3}"
            + f"{self.blocking_factor[:2]:2}"
            + f"{self.format_code[:1]:1}"
            + f"{self.immediate_destination_name[:23]:<23}"
            + f"{self.immediate_origin_name[:23]:<23}"
            + f"{self.reference_code[:8]:<8}"
        )
        assert len(line) == RECORD_LEN, f"Record 1 length {len(line)} != {RECORD_LEN}"
        return line


@dataclass
class BatchHeaderRecord:
    service_class_code: str = "200"            # 3 chars: 200 mixed, 220 credits, 225 debits
    company_name: str = "ACME PAYROLL CORP"    # 16 chars
    company_discretionary_data: str = ""       # 20 chars
    company_id: str = "1123456789"             # 10 chars
    sec_code: str = "PPD"                      # 3 chars: PPD, CCD, WEB, TEL, CTX
    company_entry_description: str = "PAYROLL" # 10 chars
    company_descriptive_date: str = ""         # 6 chars
    effective_entry_date: str = "261012"       # 6 chars (YYMMDD)
    settlement_date: str = "   "               # 3 chars (blanks)
    originator_status_code: str = "1"          # 1 char
    originating_dfi_id: str = "07100028"       # 8 chars
    batch_number: int = 1                      # 7 chars

    def format(self) -> str:
        line = (
            "5"
            + f"{self.service_class_code[:3]:3}"
            + f"{self.company_name[:16]:<16}"
            + f"{self.company_discretionary_data[:20]:<20}"
            + f"{self.company_id[:10]:<10}"
            + f"{self.sec_code[:3]:3}"
            + f"{self.company_entry_description[:10]:<10}"
            + f"{self.company_descriptive_date[:6]:<6}"
            + f"{self.effective_entry_date[:6]:6}"
            + f"{self.settlement_date[:3]:3}"
            + f"{self.originator_status_code[:1]:1}"
            + f"{self.originating_dfi_id[:8]:8}"
            + f"{self.batch_number:07d}"
        )
        assert len(line) == RECORD_LEN, f"Record 5 length {len(line)} != {RECORD_LEN}"
        return line


@dataclass
class AddendaRecord:
    addenda_type_code: str = "05"              # 05 for detail addenda, 99 for return
    payment_related_info: str = ""             # 80 chars
    addenda_sequence_number: int = 1           # 4 chars
    entry_detail_sequence: int = 1             # 7 chars

    def format(self) -> str:
        line = (
            "7"
            + f"{self.addenda_type_code[:2]:2}"
            + f"{self.payment_related_info[:80]:<80}"
            + f"{self.addenda_sequence_number:04d}"
            + f"{self.entry_detail_sequence:07d}"
        )
        assert len(line) == RECORD_LEN, f"Record 7 length {len(line)} != {RECORD_LEN}"
        return line


@dataclass
class EntryDetailRecord:
    transaction_code: str = "22"               # 22 checking credit, 27 checking debit
    receiving_dfi_id: str = "07100028"         # 8 digits
    check_digit: str = "8"                     # 1 digit
    dfi_account_number: str = "1234567890"     # 17 chars
    amount_cents: int = 100000                 # 10 chars (cents)
    individual_id: str = "EMP0001"             # 15 chars
    individual_name: str = "JOHN DOE"          # 22 chars
    discretionary_data: str = "  "             # 2 chars
    addenda_indicator: str = "0"               # 1 char: 0 or 1
    trace_number: str = "071000280000001"      # 15 chars
    addenda: Optional[AddendaRecord] = None

    def format(self) -> str:
        has_addenda = "1" if self.addenda is not None else self.addenda_indicator
        line = (
            "6"
            + f"{self.transaction_code[:2]:2}"
            + f"{self.receiving_dfi_id[:8]:8}"
            + f"{self.check_digit[:1]:1}"
            + f"{self.dfi_account_number[:17]:<17}"
            + f"{self.amount_cents:010d}"
            + f"{self.individual_id[:15]:<15}"
            + f"{self.individual_name[:22]:<22}"
            + f"{self.discretionary_data[:2]:2}"
            + f"{has_addenda[:1]:1}"
            + f"{self.trace_number[:15]:15}"
        )
        assert len(line) == RECORD_LEN, f"Record 6 length {len(line)} != {RECORD_LEN}"
        return line


@dataclass
class BatchControlRecord:
    service_class_code: str = "200"
    entry_addenda_count: int = 0
    entry_hash: int = 0
    total_debit_cents: int = 0
    total_credit_cents: int = 0
    company_id: str = "1123456789"
    message_auth_code: str = " " * 19
    reserved: str = " " * 6
    originating_dfi_id: str = "07100028"
    batch_number: int = 1

    def format(self) -> str:
        line = (
            "8"
            + f"{self.service_class_code[:3]:3}"
            + f"{self.entry_addenda_count:06d}"
            + f"{self.entry_hash % (10**10):010d}"
            + f"{self.total_debit_cents:012d}"
            + f"{self.total_credit_cents:012d}"
            + f"{self.company_id[:10]:<10}"
            + f"{self.message_auth_code[:19]:19}"
            + f"{self.reserved[:6]:6}"
            + f"{self.originating_dfi_id[:8]:8}"
            + f"{self.batch_number:07d}"
        )
        assert len(line) == RECORD_LEN, f"Record 8 length {len(line)} != {RECORD_LEN}"
        return line


@dataclass
class FileControlRecord:
    batch_count: int = 1
    block_count: int = 1
    entry_addenda_count: int = 0
    entry_hash: int = 0
    total_debit_cents: int = 0
    total_credit_cents: int = 0
    reserved: str = " " * 39

    def format(self) -> str:
        line = (
            "9"
            + f"{self.batch_count:06d}"
            + f"{self.block_count:06d}"
            + f"{self.entry_addenda_count:08d}"
            + f"{self.entry_hash % (10**10):010d}"
            + f"{self.total_debit_cents:012d}"
            + f"{self.total_credit_cents:012d}"
            + f"{self.reserved[:39]:39}"
        )
        assert len(line) == RECORD_LEN, f"Record 9 length {len(line)} != {RECORD_LEN}"
        return line


@dataclass
class ACHBatch:
    header: BatchHeaderRecord
    entries: List[EntryDetailRecord] = field(default_factory=list)
    control: Optional[BatchControlRecord] = None


@dataclass
class ACHFile:
    header: FileHeaderRecord
    batches: List[ACHBatch] = field(default_factory=list)
    control: Optional[FileControlRecord] = None


@dataclass
class ValidationResult:
    is_valid: bool
    batch_count: int = 0
    entry_count: int = 0
    total_debits_cents: int = 0
    total_credits_cents: int = 0
    entry_hash: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASSED" if self.is_valid else "FAILED"
        lines = [
            f"Validation Status: {status}",
            f"Batch Count:       {self.batch_count}",
            f"Total Entries:     {self.entry_count}",
            f"Total Debits:      ${self.total_debits_cents / 100:.2f}",
            f"Total Credits:     ${self.total_credits_cents / 100:.2f}",
            f"Entry Hash:        {self.entry_hash}",
        ]
        if self.errors:
            lines.append("Errors:")
            for err in self.errors:
                lines.append(f"  - {err}")
        if self.warnings:
            lines.append("Warnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")
        return "\n".join(lines)
