"""ach-nacha-toolkit: US Automated Clearing House (NACHA) file generator, parser, validator, and returns handler."""

from .models import (
    FileHeaderRecord,
    BatchHeaderRecord,
    EntryDetailRecord,
    AddendaRecord,
    BatchControlRecord,
    FileControlRecord,
    ACHBatch,
    ACHFile,
    ValidationResult,
    RECORD_LEN,
)
from .routing_utils import calculate_aba_check_digit, validate_aba_routing, generate_valid_routing
from .generator import generate_synthetic_ach, serialize_ach_file
from .parser import parse_ach_file
from .validator import ACHValidator
from .returns import generate_return_file, RETURN_REASON_CODES

__version__ = "0.1.0"
__all__ = [
    "FileHeaderRecord",
    "BatchHeaderRecord",
    "EntryDetailRecord",
    "AddendaRecord",
    "BatchControlRecord",
    "FileControlRecord",
    "ACHBatch",
    "ACHFile",
    "ValidationResult",
    "RECORD_LEN",
    "calculate_aba_check_digit",
    "validate_aba_routing",
    "generate_valid_routing",
    "generate_synthetic_ach",
    "serialize_ach_file",
    "parse_ach_file",
    "ACHValidator",
    "generate_return_file",
    "RETURN_REASON_CODES",
]
