"""Parser for 94-character fixed-width NACHA ACH files."""

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


def parse_ach_file(raw_text: str) -> ACHFile:
    """Parse raw NACHA text into structured ACHFile."""
    lines = [l.rstrip("\r\n") for l in raw_text.splitlines() if l.strip()]

    file_header: Optional[FileHeaderRecord] = None
    file_control: Optional[FileControlRecord] = None
    batches: List[ACHBatch] = []

    current_batch: Optional[ACHBatch] = None

    for idx, line in enumerate(lines, start=1):
        if len(line) != RECORD_LEN:
            raise ValueError(f"Line {idx} length {len(line)} != {RECORD_LEN}")

        rec_type = line[0]

        if rec_type == "1":
            file_header = FileHeaderRecord(
                immediate_destination=line[3:13],
                immediate_origin=line[13:23],
                file_creation_date=line[23:29],
                file_creation_time=line[29:33],
                file_id_modifier=line[33:34],
                record_size=line[34:37],
                blocking_factor=line[37:39],
                format_code=line[39:40],
                immediate_destination_name=line[40:63],
                immediate_origin_name=line[63:86],
                reference_code=line[86:94],
            )

        elif rec_type == "5":
            b_hdr = BatchHeaderRecord(
                service_class_code=line[1:4],
                company_name=line[4:20],
                company_discretionary_data=line[20:40],
                company_id=line[40:50],
                sec_code=line[50:53],
                company_entry_description=line[53:63],
                company_descriptive_date=line[63:69],
                effective_entry_date=line[69:75],
                settlement_date=line[75:78],
                originator_status_code=line[78:79],
                originating_dfi_id=line[79:87],
                batch_number=int(line[87:94]),
            )
            current_batch = ACHBatch(header=b_hdr, entries=[])
            batches.append(current_batch)

        elif rec_type == "6":
            if current_batch is None:
                raise ValueError(f"Entry record at line {idx} without preceding batch header")
            entry = EntryDetailRecord(
                transaction_code=line[1:3],
                receiving_dfi_id=line[3:11],
                check_digit=line[11:12],
                dfi_account_number=line[12:29].strip(),
                amount_cents=int(line[29:39]),
                individual_id=line[39:54].strip(),
                individual_name=line[54:76].strip(),
                discretionary_data=line[76:78],
                addenda_indicator=line[78:79],
                trace_number=line[79:94],
            )
            current_batch.entries.append(entry)

        elif rec_type == "7":
            if current_batch is None or not current_batch.entries:
                raise ValueError(f"Addenda record at line {idx} without preceding entry")
            addenda = AddendaRecord(
                addenda_type_code=line[1:3],
                payment_related_info=line[3:83],
                addenda_sequence_number=int(line[83:87]),
                entry_detail_sequence=int(line[87:94]),
            )
            current_batch.entries[-1].addenda = addenda

        elif rec_type == "8":
            if current_batch is None:
                raise ValueError(f"Batch control at line {idx} without preceding batch")
            current_batch.control = BatchControlRecord(
                service_class_code=line[1:4],
                entry_addenda_count=int(line[4:10]),
                entry_hash=int(line[10:20]),
                total_debit_cents=int(line[20:32]),
                total_credit_cents=int(line[32:44]),
                company_id=line[44:54],
                message_auth_code=line[54:73],
                reserved=line[73:79],
                originating_dfi_id=line[79:87],
                batch_number=int(line[87:94]),
            )

        elif rec_type == "9":
            # Check if it's a filler line (all '9's)
            if line == "9" * RECORD_LEN:
                continue
            file_control = FileControlRecord(
                batch_count=int(line[1:7]),
                block_count=int(line[7:13]),
                entry_addenda_count=int(line[13:21]),
                entry_hash=int(line[21:31]),
                total_debit_cents=int(line[31:43]),
                total_credit_cents=int(line[43:55]),
                reserved=line[55:94],
            )

    if file_header is None:
        raise ValueError("Missing mandatory File Header Record (Record 1)")

    return ACHFile(header=file_header, batches=batches, control=file_control)
