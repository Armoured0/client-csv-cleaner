import csv
import re
from pathlib import Path


def normalise_fieldnames(fieldnames: list[str]) -> list[str]:
    normalised_headers = []

    for header in fieldnames:
        normalised_header = re.sub(r"[\s-]+", "_", header.strip().lower())
        normalised_headers.append(normalised_header)

    return normalised_headers


def validate_headers(normalised_headers: list[str]) -> None:
    required_headers = {
        "transaction_id",
        "date",
        "description",
        "amount",
        "category",
    }
    normalised_headers_set = set(normalised_headers)

    valid_headers = normalised_headers_set == required_headers
    no_duplicated_headers = len(normalised_headers_set) == len(normalised_headers)

    if not valid_headers or not no_duplicated_headers:
        raise csv.Error("Invalid CSV headers")


def validate_rows_structure(
    transaction_records: list[dict[str | None, str | None]],
) -> None:
    """Raise csv.Error if any transaction record has missing or extra fields."""
    for record in transaction_records:
        if None in record or None in record.values():
            raise csv.Error("Malformed CSV rows")


def load_transactions(input_path: Path) -> list[dict[str, str]]:
    """Load CSV transaction rows in input order with normalised headers and raw field values."""
    with input_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file, strict=True)
        if reader.fieldnames is not None:
            raw_headers = reader.fieldnames
            normalised_headers = normalise_fieldnames(raw_headers)
            validate_headers(normalised_headers)
        else:
            raise csv.Error("CSV file is empty")

        reader.fieldnames = normalised_headers
        transaction_records = list(reader)
        validate_rows_structure(transaction_records)

    return transaction_records
