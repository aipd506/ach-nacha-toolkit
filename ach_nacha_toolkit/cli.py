"""Command-line interface for ach-nacha-toolkit."""

import argparse
import sys
from pathlib import Path
from .generator import generate_synthetic_ach, serialize_ach_file
from .parser import parse_ach_file
from .validator import ACHValidator
from .returns import generate_return_file, RETURN_REASON_CODES
from .routing_utils import validate_aba_routing, calculate_aba_check_digit


def cmd_generate(args) -> int:
    sec = args.sec.upper()
    count = args.count
    amount_cents = int(args.amount * 100)
    tx_code = "27" if args.debit else "22"

    ach = generate_synthetic_ach(
        count=count,
        amount_per_entry_cents=amount_cents,
        sec_code=sec,
        transaction_code=tx_code,
        company_name=args.company,
    )

    out_text = serialize_ach_file(ach, pad_blocks=not args.no_padding)

    if args.output:
        out_p = Path(args.output)
        out_p.write_text(out_text, encoding="utf-8")
        print(f"Generated NACHA ACH file saved to {out_p} ({len(out_text.splitlines())} records)")
    else:
        sys.stdout.write(out_text)

    return 0


def cmd_parse(args) -> int:
    file_p = Path(args.file)
    if not file_p.exists():
        sys.stderr.write(f"Error: File '{file_p}' not found.\n")
        return 1

    text = file_p.read_text(encoding="utf-8")
    try:
        ach = parse_ach_file(text)
    except Exception as e:
        sys.stderr.write(f"Parse error: {e}\n")
        return 1

    if args.json:
        import json
        from dataclasses import asdict
        # Simple dict representation
        batches_data = []
        for b in ach.batches:
            batches_data.append({
                "header": asdict(b.header),
                "entries_count": len(b.entries),
                "control": asdict(b.control) if b.control else None,
            })
        data = {
            "header": asdict(ach.header),
            "batches": batches_data,
            "control": asdict(ach.control) if ach.control else None,
        }
        print(json.dumps(data, indent=2))
    else:
        print("=" * 60)
        print(f"NACHA ACH File Summary: {file_p.name}")
        print("=" * 60)
        print(f"Destination:  {ach.header.immediate_destination_name.strip()} ({ach.header.immediate_destination.strip()})")
        print(f"Origin:       {ach.header.immediate_origin_name.strip()} ({ach.header.immediate_origin.strip()})")
        print(f"Created:      20{ach.header.file_creation_date} {ach.header.file_creation_time}")
        print(f"Batches:      {len(ach.batches)}")
        for idx, b in enumerate(ach.batches, start=1):
            print(f"  Batch {idx}: SEC={b.header.sec_code} Company={b.header.company_name.strip()} Entries={len(b.entries)}")
        if ach.control:
            print(f"Total Debits:   ${ach.control.total_debit_cents / 100:.2f}")
            print(f"Total Credits:  ${ach.control.total_credit_cents / 100:.2f}")
            print(f"Block Count:    {ach.control.block_count}")
        print("=" * 60)

    return 0


def cmd_validate(args) -> int:
    file_p = Path(args.file)
    if not file_p.exists():
        sys.stderr.write(f"Error: File '{file_p}' not found.\n")
        return 1

    text = file_p.read_text(encoding="utf-8")
    validator = ACHValidator()
    result = validator.validate_raw(text)

    print(result.summary())
    return 0 if result.is_valid else 1


def cmd_return(args) -> int:
    file_p = Path(args.file)
    if not file_p.exists():
        sys.stderr.write(f"Error: File '{file_p}' not found.\n")
        return 1

    text = file_p.read_text(encoding="utf-8")
    orig_ach = parse_ach_file(text)

    reason = args.reason.upper()
    return_ach = generate_return_file(orig_ach, reason_code=reason)
    serialized = serialize_ach_file(return_ach, pad_blocks=True)

    if args.output:
        out_p = Path(args.output)
        out_p.write_text(serialized, encoding="utf-8")
        desc = RETURN_REASON_CODES.get(reason, "Return")
        print(f"Generated return ACH file ({reason}: {desc}) saved to {out_p}")
    else:
        sys.stdout.write(serialized)

    return 0


def cmd_routing(args) -> int:
    rtn = args.routing.strip()
    if len(rtn) == 8:
        chk = calculate_aba_check_digit(rtn)
        print(f"Calculated check digit for {rtn} is: {chk} (Full routing: {rtn}{chk})")
        return 0
    elif len(rtn) == 9:
        valid, msg = validate_aba_routing(rtn)
        status = "VALID" if valid else "INVALID"
        print(f"Routing {rtn}: {status} ({msg})")
        return 0 if valid else 1
    else:
        sys.stderr.write("Error: Expected 8 or 9 numeric digits.\n")
        return 1


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="nachatool",
        description="US Automated Clearing House (NACHA) file generator, 94-char fixed-width parser, check-digit validator, and returns handler",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate synthetic NACHA ACH file")
    p_gen.add_argument("--sec", choices=["PPD", "CCD", "WEB", "TEL"], default="PPD", help="SEC code (default: PPD)")
    p_gen.add_argument("-c", "--count", type=int, default=5, help="Number of entries")
    p_gen.add_argument("--amount", type=float, default=1500.00, help="Amount per entry in dollars")
    p_gen.add_argument("--debit", action="store_true", help="Generate debits instead of credits")
    p_gen.add_argument("--company", default="GLOBAL TECH CORP", help="Company Name")
    p_gen.add_argument("--no-padding", action="store_true", help="Disable multiple-of-10 blocking padding")
    p_gen.add_argument("-o", "--output", help="Output file path")
    p_gen.set_defaults(func=cmd_generate)

    # parse
    p_parse = subparsers.add_parser("parse", help="Parse a NACHA ACH file")
    p_parse.add_argument("file", help="Path to ACH file")
    p_parse.add_argument("--json", action="store_true", help="Output JSON structure")
    p_parse.set_defaults(func=cmd_parse)

    # validate
    p_val = subparsers.add_parser("validate", help="Validate NACHA ACH file compliance and checksums")
    p_val.add_argument("file", help="Path to ACH file")
    p_val.set_defaults(func=cmd_validate)

    # return
    p_ret = subparsers.add_parser("return", help="Generate automated return file for an ACH file")
    p_ret.add_argument("file", help="Original ACH file")
    p_ret.add_argument("--reason", default="R01", help="Return reason code (e.g. R01, R02, R03)")
    p_ret.add_argument("-o", "--output", help="Output return file path")
    p_ret.set_defaults(func=cmd_return)

    # routing
    p_rtn = subparsers.add_parser("routing", help="Validate or calculate 9-digit ABA routing check digit")
    p_rtn.add_argument("routing", help="8-digit or 9-digit ABA routing number")
    p_rtn.set_defaults(func=cmd_routing)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
