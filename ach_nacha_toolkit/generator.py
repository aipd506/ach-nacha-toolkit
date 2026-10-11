"""Generator and serializer for NACHA ACH 94-character fixed-width files."""

import math
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from .models import (
    FileHeaderRecord,
    BatchHeaderRecord,
    EntryDetailRecord,
    AddendaRecord,
    BatchControlRecord,
    FileControlRecord,
    ACHBatch,
    ACHFile,
    RECORD_LEN,
)
from .routing_utils import generate_valid_routing, calculate_aba_check_digit


def generate_synthetic_ach(
    count: int = 5,
    amount_per_entry_cents: int = 150000,
    sec_code: str = "PPD",
    transaction_code: str = "22",  # Checking Credit
    company_name: str = "GLOBAL TECH LLC",
    originating_routing: str = "07100028",
) -> ACHFile:
    """Generate a fully conforming ACH file with valid check digits and balanced controls."""
    now = datetime.now(timezone.utc)
    yymmdd = now.strftime("%y%m%d")
    hhmm = now.strftime("%H%M")

    # File Header
    file_hdr = FileHeaderRecord(
        immediate_destination=" " + originating_routing + calculate_aba_check_digit(originating_routing),
        immediate_origin=" 1123456789",
        file_creation_date=yymmdd,
        file_creation_time=hhmm,
        immediate_origin_name=company_name,
    )

    # Determine service class
    if transaction_code in ["22", "32"]:
        service_class = "220"  # Credits only
    elif transaction_code in ["27", "37"]:
        service_class = "225"  # Debits only
    else:
        service_class = "200"

    # Batch Header
    batch_hdr = BatchHeaderRecord(
        service_class_code=service_class,
        company_name=company_name,
        company_id="1123456789",
        sec_code=sec_code,
        company_entry_description="PAYROLL" if sec_code == "PPD" else "INVOICE",
        effective_entry_date=yymmdd,
        originating_dfi_id=originating_routing[:8],
        batch_number=1,
    )

    entries: List[EntryDetailRecord] = []
    total_debits = 0
    total_credits = 0
    entry_hash = 0

    for i in range(count):
        rec_routing = generate_valid_routing()
        dfi_8 = rec_routing[:8]
        check_d = rec_routing[8]

        trace = f"{originating_routing[:8]}{i+1:07d}"
        amt = amount_per_entry_cents + (i * 1000)

        entry = EntryDetailRecord(
            transaction_code=transaction_code,
            receiving_dfi_id=dfi_8,
            check_digit=check_d,
            dfi_account_number=f"ACC{10000000 + i}",
            amount_cents=amt,
            individual_id=f"ID{1000 + i}",
            individual_name=f"RECIPIENT {i+1}",
            trace_number=trace,
        )
        entries.append(entry)

        entry_hash += int(dfi_8)
        if transaction_code in ["22", "32"]:
            total_credits += amt
        else:
            total_debits += amt

    # Batch Control
    batch_ctl = BatchControlRecord(
        service_class_code=service_class,
        entry_addenda_count=len(entries),
        entry_hash=entry_hash % (10**10),
        total_debit_cents=total_debits,
        total_credit_cents=total_credits,
        company_id="1123456789",
        originating_dfi_id=originating_routing[:8],
        batch_number=1,
    )

    batch = ACHBatch(header=batch_hdr, entries=entries, control=batch_ctl)

    # File Control (initial block count will be recalculated on serialize)
    file_ctl = FileControlRecord(
        batch_count=1,
        block_count=1,
        entry_addenda_count=len(entries),
        entry_hash=entry_hash % (10**10),
        total_debit_cents=total_debits,
        total_credit_cents=total_credits,
    )

    return ACHFile(header=file_hdr, batches=[batch], control=file_ctl)


def serialize_ach_file(ach: ACHFile, pad_blocks: bool = True) -> str:
    """Serialize ACHFile into 94-character fixed-width string with optional blocking factor 10 padding."""
    lines: List[str] = []
    lines.append(ach.header.format())

    for b in ach.batches:
        lines.append(b.header.format())
        for e in b.entries:
            lines.append(e.format())
            if e.addenda:
                lines.append(e.addenda.format())
        if b.control:
            lines.append(b.control.format())

    # Pre-calculate block count before formatting File Control
    # Total records so far + 1 (for file control itself)
    unpadded_count = len(lines) + 1
    block_count = math.ceil(unpadded_count / 10.0) if pad_blocks else 1

    if ach.control:
        ach.control.block_count = block_count
        lines.append(ach.control.format())

    # Pad with 9s to multiple of 10 if requested
    if pad_blocks:
        filler = "9" * RECORD_LEN
        while len(lines) % 10 != 0:
            lines.append(filler)

    return "\n".join(lines) + "\n"
