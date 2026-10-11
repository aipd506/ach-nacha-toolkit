"""Return file generator and return reason code resolver for NACHA ACH."""

from datetime import datetime, timezone
from typing import Dict, List, Optional
from .models import (
    ACHFile,
    ACHBatch,
    BatchHeaderRecord,
    EntryDetailRecord,
    AddendaRecord,
    BatchControlRecord,
    FileHeaderRecord,
    FileControlRecord,
)

RETURN_REASON_CODES: Dict[str, str] = {
    "R01": "Insufficient Funds",
    "R02": "Account Closed",
    "R03": "No Account / Unable to Locate Account",
    "R04": "Invalid Account Number Structure",
    "R05": "Unauthorized Debit to Consumer Account Using Corporate SEC",
    "R07": "Authorization Revoked by Customer",
    "R08": "Payment Stopped",
    "R10": "Customer Advises Unauthorized",
    "R16": "Account Frozen",
    "R20": "Non-Transaction Account",
    "R29": "Corporate Customer Advises Not Authorized",
}


def create_return_addenda(
    return_reason_code: str,
    original_trace: str,
    original_dfi_id: str,
    seq: int = 1,
) -> AddendaRecord:
    """Create Record 7 Type 99 Return Addenda."""
    code = return_reason_code.upper()
    if code not in RETURN_REASON_CODES:
        raise ValueError(f"Unknown return reason code '{return_reason_code}'. Standard: {list(RETURN_REASON_CODES.keys())}")

    # Layout for Record 7 Type 99 (80 chars payment_related_info):
    # pos 04-06: Return Reason Code (3)
    # pos 07-21: Original Trace Number (15)
    # pos 22-27: Date of Death / Blanks (6)
    # pos 28-35: Original Receiving DFI ID (8)
    # pos 36-83: Addenda Information / Blanks (48)
    info = (
        f"{code[:3]:3}"
        + f"{original_trace[:15]:15}"
        + " " * 6
        + f"{original_dfi_id[:8]:8}"
        + " " * 48
    )

    return AddendaRecord(
        addenda_type_code="99",
        payment_related_info=info,
        addenda_sequence_number=1,
        entry_detail_sequence=seq,
    )


def generate_return_file(
    original_ach: ACHFile,
    reason_code: str = "R01",
    return_company_name: str = "RETURN NOTIFICATION",
) -> ACHFile:
    """Generate an automated NACHA Return ACH file based on an input ACH file."""
    now = datetime.now(timezone.utc)
    yymmdd = now.strftime("%y%m%d")
    hhmm = now.strftime("%H%M")

    # Invert Origin and Destination
    return_dest = original_ach.header.immediate_origin
    return_origin = original_ach.header.immediate_destination

    file_hdr = FileHeaderRecord(
        immediate_destination=return_dest,
        immediate_origin=return_origin,
        file_creation_date=yymmdd,
        file_creation_time=hhmm,
        immediate_destination_name=original_ach.header.immediate_origin_name,
        immediate_origin_name=return_company_name,
    )

    return_batches: List[ACHBatch] = []
    file_total_debits = 0
    file_total_credits = 0
    file_entry_hash = 0
    file_total_entries = 0

    for b_idx, orig_b in enumerate(original_ach.batches, start=1):
        batch_hdr = BatchHeaderRecord(
            service_class_code=orig_b.header.service_class_code,
            company_name=return_company_name[:16],
            company_id=orig_b.header.company_id,
            sec_code=orig_b.header.sec_code,
            company_entry_description="RETURN",
            effective_entry_date=yymmdd,
            originating_dfi_id=orig_b.header.originating_dfi_id,
            batch_number=b_idx,
        )

        return_entries: List[EntryDetailRecord] = []
        batch_debits = 0
        batch_credits = 0
        batch_hash = 0

        for e_idx, orig_e in enumerate(orig_b.entries, start=1):
            addenda = create_return_addenda(
                return_reason_code=reason_code,
                original_trace=orig_e.trace_number,
                original_dfi_id=orig_e.receiving_dfi_id,
                seq=e_idx,
            )

            # Return entry keeps amount and original receiving DFI
            ret_entry = EntryDetailRecord(
                transaction_code=orig_e.transaction_code,
                receiving_dfi_id=orig_e.receiving_dfi_id,
                check_digit=orig_e.check_digit,
                dfi_account_number=orig_e.dfi_account_number,
                amount_cents=orig_e.amount_cents,
                individual_id=orig_e.individual_id,
                individual_name=orig_e.individual_name,
                addenda_indicator="1",
                trace_number=f"{orig_b.header.originating_dfi_id[:8]}{e_idx:07d}",
                addenda=addenda,
            )
            return_entries.append(ret_entry)

            batch_hash += int(orig_e.receiving_dfi_id)
            if orig_e.transaction_code in ["27", "37"]:
                batch_debits += orig_e.amount_cents
            else:
                batch_credits += orig_e.amount_cents

        # In return files, entry count includes both Record 6 and Record 7
        entry_addenda_count = len(return_entries) * 2

        batch_ctl = BatchControlRecord(
            service_class_code=orig_b.header.service_class_code,
            entry_addenda_count=entry_addenda_count,
            entry_hash=batch_hash % (10**10),
            total_debit_cents=batch_debits,
            total_credit_cents=batch_credits,
            company_id=orig_b.header.company_id,
            originating_dfi_id=orig_b.header.originating_dfi_id,
            batch_number=b_idx,
        )

        return_batches.append(ACHBatch(header=batch_hdr, entries=return_entries, control=batch_ctl))

        file_total_entries += entry_addenda_count
        file_total_debits += batch_debits
        file_total_credits += batch_credits
        file_entry_hash += batch_hash

    file_ctl = FileControlRecord(
        batch_count=len(return_batches),
        block_count=1,
        entry_addenda_count=file_total_entries,
        entry_hash=file_entry_hash % (10**10),
        total_debit_cents=file_total_debits,
        total_credit_cents=file_total_credits,
    )

    return ACHFile(header=file_hdr, batches=return_batches, control=file_ctl)
