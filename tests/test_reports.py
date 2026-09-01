import csv
import json
from copy import deepcopy

import pytest

from business_data_cleaner.reports import write_reports


def test_write_reports(tmp_path):
    output_dir = tmp_path / "nested" / "output"
    expected_clean_path = output_dir / "clean_transactions.csv"
    expected_rejected_path = output_dir / "rejected_rows.csv"
    expected_summary_path = output_dir / "summary.json"

    clean_transactions = [
        {
            "transaction_id": "TXN-001",
            "date": "2026-08-01",
            "description": "Office chairs, set of 2",
            "amount_pence": 12999,
            "category": "office equipment",
        },
        {
            "transaction_id": "INV_204",
            "date": "2026-08-04",
            "description": "Monthly hosting",
            "amount_pence": 2500,
            "category": "software",
        },
        {
            "transaction_id": "TXN003",
            "date": "2026-08-05",
            "description": "Coffee",
            "amount_pence": 1,
            "category": "subsistence",
        },
    ]

    original_clean_transactions = deepcopy(clean_transactions)

    rejected_transactions = [
        {
            "source_row_number": 3,
            "transaction_id": " bad id ",
            "date": "03/08/2026",
            "description": " Taxi, station to office ",
            "amount": "18.50",
            "category": "Travel",
            "rejection_reason": "invalid_transaction_id",
        },
        {
            "source_row_number": 6,
            "transaction_id": " txn-001 ",
            "date": "06/08/2026",
            "description": "Replacement cable",
            "amount": "5.00",
            "category": " Office ",
            "rejection_reason": "duplicate_transaction_id",
        },
    ]

    original_rejected_transactions = deepcopy(rejected_transactions)

    expected_clean_headers = [
        "transaction_id",
        "date",
        "description",
        "amount_pence",
        "category",
    ]

    expected_rejected_headers = [
        "source_row_number",
        "transaction_id",
        "date",
        "description",
        "amount",
        "category",
        "rejection_reason",
    ]

    expected_clean_rows = [
        {
            "transaction_id": "TXN-001",
            "date": "2026-08-01",
            "description": "Office chairs, set of 2",
            "amount_pence": "12999",
            "category": "office equipment",
        },
        {
            "transaction_id": "INV_204",
            "date": "2026-08-04",
            "description": "Monthly hosting",
            "amount_pence": "2500",
            "category": "software",
        },
        {
            "transaction_id": "TXN003",
            "date": "2026-08-05",
            "description": "Coffee",
            "amount_pence": "1",
            "category": "subsistence",
        },
    ]

    expected_rejected_rows = [
        {
            "source_row_number": "3",
            "transaction_id": " bad id ",
            "date": "03/08/2026",
            "description": " Taxi, station to office ",
            "amount": "18.50",
            "category": "Travel",
            "rejection_reason": "invalid_transaction_id",
        },
        {
            "source_row_number": "6",
            "transaction_id": " txn-001 ",
            "date": "06/08/2026",
            "description": "Replacement cable",
            "amount": "5.00",
            "category": " Office ",
            "rejection_reason": "duplicate_transaction_id",
        },
    ]

    expected_summary = {
        "input_row_count": 5,
        "accepted_count": 3,
        "rejected_count": 2,
        "accepted_total_pence": 15500,
    }

    write_reports(output_dir, clean_transactions, rejected_transactions)

    unrelated_path = output_dir / "keep.txt"
    unrelated_path.write_text("preserve me", encoding="utf-8")

    summary = write_reports(output_dir, clean_transactions, rejected_transactions)

    assert unrelated_path.read_text(encoding="utf-8") == "preserve me"

    assert clean_transactions == original_clean_transactions
    assert rejected_transactions == original_rejected_transactions
    assert summary == expected_summary
    assert all(type(value) is int for value in summary.values())

    with expected_summary_path.open("r", encoding="utf-8") as written_summary_file:
        written_summary = json.load(written_summary_file)
        assert written_summary == expected_summary
        assert all(type(value) is int for value in written_summary.values())

    expected_text = json.dumps(expected_summary, indent=2) + "\n"
    assert expected_summary_path.read_text(encoding="utf-8") == expected_text

    with expected_clean_path.open(
        "r", encoding="utf-8", newline=""
    ) as written_clean_file:
        reader = csv.DictReader(written_clean_file)
        assert reader.fieldnames == expected_clean_headers
        assert list(reader) == expected_clean_rows

    with expected_rejected_path.open(
        "r", encoding="utf-8", newline=""
    ) as written_rejected_file:
        reader = csv.DictReader(written_rejected_file)
        assert reader.fieldnames == expected_rejected_headers
        assert list(reader) == expected_rejected_rows


def test_write_reports_empty_input(tmp_path):
    output_dir = tmp_path / "output"
    expected_clean_csv_path = output_dir / "clean_transactions.csv"
    expected_rejected_csv_path = output_dir / "rejected_rows.csv"
    expected_summary_path = output_dir / "summary.json"
    empty_input = []

    expected_clean_headers = [
        "transaction_id",
        "date",
        "description",
        "amount_pence",
        "category",
    ]

    expected_rejected_headers = [
        "source_row_number",
        "transaction_id",
        "date",
        "description",
        "amount",
        "category",
        "rejection_reason",
    ]

    expected_summary = {
        "input_row_count": 0,
        "accepted_count": 0,
        "rejected_count": 0,
        "accepted_total_pence": 0,
    }

    summary = write_reports(output_dir, empty_input, empty_input)

    assert summary == expected_summary
    assert all(type(value) is int for value in summary.values())

    with expected_summary_path.open("r", encoding="utf-8") as written_summary_file:
        written_summary = json.load(written_summary_file)
        assert written_summary == expected_summary
        assert all(type(value) is int for value in written_summary.values())

    with expected_clean_csv_path.open(
        "r", encoding="utf-8", newline=""
    ) as clean_csv_file:
        reader = csv.DictReader(clean_csv_file)

        assert reader.fieldnames == expected_clean_headers
        assert len(list(reader)) == 0

    with expected_rejected_csv_path.open(
        "r", encoding="utf-8", newline=""
    ) as rejected_csv_file:
        reader = csv.DictReader(rejected_csv_file)

        assert reader.fieldnames == expected_rejected_headers
        assert len(list(reader)) == 0


def test_reports_directory_creation_failure(tmp_path):
    output_dir = tmp_path / "output.txt"
    output_dir.write_text("blocking file", encoding="utf-8")

    with pytest.raises(OSError):
        write_reports(output_dir, [], [])


def test_reports_file_write_failure(tmp_path):
    output_dir = tmp_path / "output"
    output_dir.mkdir()

    blocking_dir_path = output_dir / "clean_transactions.csv"
    blocking_dir_path.mkdir()

    with pytest.raises(OSError):
        write_reports(output_dir, [], [])
