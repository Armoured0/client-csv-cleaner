from copy import deepcopy

from business_data_cleaner.transforms import (
    normalise_validate_amount,
    normalise_validate_category,
    normalise_validate_date,
    normalise_validate_description,
    normalise_validate_id,
    normalise_validate_transaction_records,
)


def test_valid_id_normalisation():
    input_expected_result = {
        "ID-123": "ID-123",
        "test-677": "TEST-677",
        " TXn-450  ": "TXN-450",
        "ID_456": "ID_456",
        "testid": "TESTID",
        "12345": "12345",
    }

    for test_input, expected_result in input_expected_result.items():
        assert normalise_validate_id(test_input) == (expected_result, "")


def test_invalid_id_validation():
    invalid_inputs = ["ID 123", "ID's-456", "TXN-１２", "ÌD_400", "ß", ""]

    for test_input in invalid_inputs:
        assert normalise_validate_id(test_input) == ("", "invalid_transaction_id")


def test_valid_date_normalisation():
    input_expected_result = {
        "2020-12-25": "2020-12-25",
        "2024-02-29": "2024-02-29",
        "01/03/2012": "2012-03-01",
        "17/08/1956": "1956-08-17",
        "  10/09/2022 ": "2022-09-10",
    }

    for test_input, expected_result in input_expected_result.items():
        assert normalise_validate_date(test_input) == (expected_result, "")


def test_invalid_date_validation():
    invalid_inputs = [
        "2026-10-32",
        "2026-09-aa",
        "2026-5-2",
        "25-4-10",
        "2025-１２-24",
        "2023-06-07-12",
        "aaaa-aa-aa",
        "2026-13-05",
        "xx/xx/2025",
        "1/4/1950",
        "xx/xx/xxxx",
        "12.11.2022",
        "---",
        "///",
        "",
    ]

    for test_input in invalid_inputs:
        assert normalise_validate_date(test_input) == ("", "invalid_date")


def test_valid_description_normalisation():
    input_expected_result = {
        "i am a description": "i am a description",
        "CAPITAL lowercase": "CAPITAL lowercase",
        "   strip me  ": "strip me",
        "internal   whitespace    run": "internal whitespace run",
        "tab  \t\nnewline": "tab newline",
        "   run    and   strip  ": "run and strip",
        '"quotes" fullstop.': '"quotes" fullstop.',
        "unicode  \u00a0\u2009 whitespace": "unicode whitespace",
    }

    for test_input, expected_result in input_expected_result.items():
        assert normalise_validate_description(test_input) == (expected_result, "")


def test_invalid_description_validation():
    assert normalise_validate_description("") == ("", "invalid_description")


def test_valid_amount_parse():
    input_expected_result = {
        "12.25": 1225,
        "4006.16": 400616,
        "17.00": 1700,
        "20.2": 2020,
        "19": 1900,
        "12345678901234567890123456789.12": 1234567890123456789012345678912,
    }

    for test_input, expected_result in input_expected_result.items():
        assert normalise_validate_amount(test_input) == (expected_result, "")


def test_invalid_amount_validation():
    invalid_inputs = [
        "NaN",
        "Infinity",
        "4.08E+10",
        "１２.３０",
        "abc",
        "x.x",
        ".x",
        "x.",
        "x.x.x",
        "0",
        "-0.01",
        "-10",
        "+0.10",
        "+10",
        ".10",
        "10.",
        "£10",
        "x.10",
        "10.x",
        "12.6x",
        "10.123",
        "30.12.6",
        "1,000.00",
    ]

    for test_input in invalid_inputs:
        assert normalise_validate_amount(test_input) == (-1, "invalid_amount")


def test_valid_category_normalisation():
    input_expected_output = {
        "test_category": "test_category",
        "CAPITAL lower": "capital lower",
        "   strip me   ": "strip me",
        "replace   run": "replace run",
        "   strip    replace ": "strip replace",
        "tab   \t\n newline": "tab newline",
        '"quotes" fullstop.': '"quotes" fullstop.',
        "unicode  \u00a0\u2009 whitespace": "unicode whitespace",
    }

    for test_input, expected_result in input_expected_output.items():
        assert normalise_validate_category(test_input) == (expected_result, "")


def test_invalid_category_validation():
    assert normalise_validate_category("") == ("", "invalid_category")


def test_normalise_validate_transaction_records():
    input_records = [
        # Accepted and reserves the normalised ID TX-001.
        {
            "amount": "12.3",
            "category": "  OFFICE   EQUIPMENT ",
            "transaction_id": " tx-001 ",
            "description": "  Office   Chair  ",
            "date": "2026-08-29",
        },
        # Date appears before ID, but invalid_transaction_id must win.
        {
            "date": "not-a-date",
            "transaction_id": "bad id",
            "description": "Valid description",
            "amount": "10",
            "category": "office",
        },
        # Description appears before date, but invalid_date must win.
        {
            "description": "   ",
            "date": "29/02/2025",
            "transaction_id": "DATE-FIRST",
            "amount": "10",
            "category": "office",
        },
        # Amount appears before description, but invalid_description must win.
        {
            "amount": "0",
            "description": "   ",
            "transaction_id": "DESC-FIRST",
            "date": "2026-08-29",
            "category": "office",
        },
        # Category appears before amount, but invalid_amount must win.
        {
            "category": "   ",
            "amount": "0",
            "transaction_id": "AMOUNT-FIRST",
            "date": "2026-08-29",
            "description": "Valid description",
        },
        # Duplicate ID appears before category, but invalid_category must win.
        {
            "transaction_id": "TX-001",
            "category": "   ",
            "date": "2026-08-30",
            "description": "Another chair",
            "amount": "20.00",
        },
        # Rejected, so RETRY_1 must not be reserved.
        {
            "amount": "0.00",
            "transaction_id": " retry_1 ",
            "category": "Hardware",
            "description": "Replacement cable",
            "date": "28/08/2026",
        },
        # Accepted because the earlier RETRY_1 row was rejected.
        {
            "category": " HARDWARE ",
            "description": "  Replacement   cable  ",
            "amount": "001.20",
            "date": "29/08/2026",
            "transaction_id": "RETRY_1",
        },
        # Fully valid duplicate of the first accepted row.
        {
            "transaction_id": " tx-001 ",
            "amount": "25.00",
            "description": "Third chair",
            "category": "Furniture",
            "date": "2026-08-31",
        },
        # Additional accepted date and normalisation boundary.
        {
            "date": "29/02/2024",
            "category": " Services ",
            "transaction_id": "leap_1",
            "amount": "5",
            "description": "Annual subscription (renewal)",
        },
    ]

    expected_accepted = [
        {
            "transaction_id": "TX-001",
            "date": "2026-08-29",
            "description": "Office Chair",
            "amount_pence": 1230,
            "category": "office equipment",
        },
        {
            "transaction_id": "RETRY_1",
            "date": "2026-08-29",
            "description": "Replacement cable",
            "amount_pence": 120,
            "category": "hardware",
        },
        {
            "transaction_id": "LEAP_1",
            "date": "2024-02-29",
            "description": "Annual subscription (renewal)",
            "amount_pence": 500,
            "category": "services",
        },
    ]

    expected_rejected = [
        {
            "source_row_number": 3,
            "transaction_id": "bad id",
            "date": "not-a-date",
            "description": "Valid description",
            "amount": "10",
            "category": "office",
            "rejection_reason": "invalid_transaction_id",
        },
        {
            "source_row_number": 4,
            "transaction_id": "DATE-FIRST",
            "date": "29/02/2025",
            "description": "   ",
            "amount": "10",
            "category": "office",
            "rejection_reason": "invalid_date",
        },
        {
            "source_row_number": 5,
            "transaction_id": "DESC-FIRST",
            "date": "2026-08-29",
            "description": "   ",
            "amount": "0",
            "category": "office",
            "rejection_reason": "invalid_description",
        },
        {
            "source_row_number": 6,
            "transaction_id": "AMOUNT-FIRST",
            "date": "2026-08-29",
            "description": "Valid description",
            "amount": "0",
            "category": "   ",
            "rejection_reason": "invalid_amount",
        },
        {
            "source_row_number": 7,
            "transaction_id": "TX-001",
            "date": "2026-08-30",
            "description": "Another chair",
            "amount": "20.00",
            "category": "   ",
            "rejection_reason": "invalid_category",
        },
        {
            "source_row_number": 8,
            "transaction_id": " retry_1 ",
            "date": "28/08/2026",
            "description": "Replacement cable",
            "amount": "0.00",
            "category": "Hardware",
            "rejection_reason": "invalid_amount",
        },
        {
            "source_row_number": 10,
            "transaction_id": " tx-001 ",
            "date": "2026-08-31",
            "description": "Third chair",
            "amount": "25.00",
            "category": "Furniture",
            "rejection_reason": "duplicate_transaction_id",
        },
    ]

    original_input = deepcopy(input_records)

    assert normalise_validate_transaction_records(input_records) == (
        expected_accepted,
        expected_rejected,
    )

    assert original_input == input_records


def test_normalise_validate_empty_record():
    assert normalise_validate_transaction_records([]) == ([], [])
