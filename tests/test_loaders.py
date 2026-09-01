import csv

import pytest

from business_data_cleaner.loaders import load_transactions


def test_valid_transaction_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "Amount, Transaction \u2003--\u00a0 ID ,Category,Date,Description\n"
        '12.30, tx-001 , Expenses ,2026-08-28," Office, supplies "\n'
        "7,TX_002,Transport,29/08/2026,Travel\n",
        encoding="utf-8",
    )

    expected_transactions = [
        {
            "amount": "12.30",
            "transaction_id": " tx-001 ",
            "category": " Expenses ",
            "date": "2026-08-28",
            "description": " Office, supplies ",
        },
        {
            "amount": "7",
            "transaction_id": "TX_002",
            "category": "Transport",
            "date": "29/08/2026",
            "description": "Travel",
        },
    ]

    actual_transactions = load_transactions(input_path)

    assert actual_transactions == expected_transactions


def test_valid_transaction_load_BOM(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "Amount, Transaction \t-- ID ,Category,Date,Description\n"
        '12.30, tx-001 , Expenses ,2026-08-28," Office, supplies "\n'
        "7,TX_002,Transport,29/08/2026,Travel\n",
        encoding="utf-8-sig",
    )

    expected_transactions = [
        {
            "amount": "12.30",
            "transaction_id": " tx-001 ",
            "category": " Expenses ",
            "date": "2026-08-28",
            "description": " Office, supplies ",
        },
        {
            "amount": "7",
            "transaction_id": "TX_002",
            "category": "Transport",
            "date": "29/08/2026",
            "description": "Travel",
        },
    ]

    actual_transactions = load_transactions(input_path)

    assert actual_transactions == expected_transactions


def test_missing_header_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "transaction_id,date,description,amount\n"
        "TX-001,2026-08-28,Office supplies,12.30\n",
        encoding="utf-8",
    )

    with pytest.raises(csv.Error) as error:
        load_transactions(input_path)
    assert str(error.value) == "Invalid CSV headers"


def test_extra_header_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "transaction_id,date,description,amount,category,notes\n"
        "TX-001,2026-08-28,Office supplies,12.30,expenses,Example\n",
        encoding="utf-8",
    )

    with pytest.raises(csv.Error) as error:
        load_transactions(input_path)
    assert str(error.value) == "Invalid CSV headers"


def test_blank_header_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "transaction_id,date,description,amount,category,\n"
        "TX-001,2026-08-28,Office supplies,12.30,expenses,\n",
        encoding="utf-8",
    )

    with pytest.raises(csv.Error) as error:
        load_transactions(input_path)
    assert str(error.value) == "Invalid CSV headers"


def test_colliding_header_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "Transaction ID,transaction-id,date,description,amount,category\n"
        "TX-001,TX-002,2026-08-28,Office supplies,12.30,expenses\n",
        encoding="utf-8",
    )

    with pytest.raises(csv.Error) as error:
        load_transactions(input_path)
    assert str(error.value) == "Invalid CSV headers"


def test_empty_file_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"
    input_path.write_text("", encoding="utf-8")

    with pytest.raises(csv.Error) as error:
        load_transactions(input_path)
    assert str(error.value) == "CSV file is empty"


def test_header_only_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "transaction_id,date,description,amount,category\n",
        encoding="utf-8",
    )

    assert load_transactions(input_path) == []


def test_short_row_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "transaction_id,date,description,amount,category\n"
        "TX-001,2026-08-28,Office supplies,12.30\n",
        encoding="utf-8",
    )

    with pytest.raises(csv.Error) as error:
        load_transactions(input_path)
    assert str(error.value) == "Malformed CSV rows"


def test_long_row_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "transaction_id,date,description,amount,category\n"
        "TX-001,2026-08-28,Office supplies,12.30,expenses,unexpected\n",
        encoding="utf-8",
    )

    with pytest.raises(csv.Error) as error:
        load_transactions(input_path)
    assert str(error.value) == "Malformed CSV rows"


def test_malformed_quoting_load(tmp_path):
    input_path = tmp_path / "test_transactions.csv"

    input_path.write_text(
        "transaction_id,date,description,amount,category\n"
        'TX-001,2026-08-28,"Office supplies,12.30,expenses\n',
        encoding="utf-8",
    )

    with pytest.raises(csv.Error):
        load_transactions(input_path)
