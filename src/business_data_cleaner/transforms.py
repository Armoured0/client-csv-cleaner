import string
from datetime import date
from decimal import Decimal, InvalidOperation


def strip_string(string: str) -> str:
    return string.strip()


def normalise_validate_id(transaction_id: str) -> tuple[str, str]:
    allowed_characters = set(string.ascii_letters + string.digits + "-_")
    stripped_transaction_id = strip_string(transaction_id)

    if not stripped_transaction_id:
        return "", "invalid_transaction_id"

    for character in stripped_transaction_id:
        if character not in allowed_characters:
            return "", "invalid_transaction_id"

    return stripped_transaction_id.upper(), ""


def normalise_validate_date(date_string: str) -> tuple[str, str]:
    date_stripped = strip_string(date_string)

    if "-" in date_stripped:
        split_character = "-"
        date_components_length = [4, 2, 2]
    elif "/" in date_stripped:
        split_character = "/"
        date_components_length = [2, 2, 4]
    else:
        return "", "invalid_date"

    date_split = date_stripped.split(split_character)
    date_values_joined = "".join(date_split)

    if not date_values_joined.isascii() or not date_values_joined.isdigit():
        return "", "invalid_date"

    if len(date_split) != 3:
        return "", "invalid_date"

    if [
        len(date_split[0]),
        len(date_split[1]),
        len(date_split[2]),
    ] == date_components_length:
        if split_character == "-":
            date_split.reverse()
        try:
            date_object = date(
                day=int(date_split[0]),
                month=int(date_split[1]),
                year=int(date_split[2]),
            )
        except ValueError:
            return "", "invalid_date"

        return date_object.isoformat(), ""

    return "", "invalid_date"


def normalise_validate_description(description: str) -> tuple[str, str]:
    description_stripped = strip_string(description)
    description_normalised = " ".join(description_stripped.split())

    if not description_normalised:
        return "", "invalid_description"
    else:
        return description_normalised, ""


def normalise_validate_amount(amount: str) -> tuple[int, str]:
    amount_stripped = strip_string(amount)

    if "." in amount_stripped:
        amount_split = amount_stripped.split(".")
        whole_valid = amount_split[0].isascii() and amount_split[0].isdigit()
        decimal_valid = amount_split[1].isascii() and amount_split[1].isdigit()
        if (
            not whole_valid
            or not decimal_valid
            or len(amount_split) != 2
            or len(amount_split[1]) > 2
        ):
            return -1, "invalid_amount"
        zeros_to_add = 1 if len(amount_split[1]) == 1 else 0
        pence_str = "".join(amount_split) + "0" * zeros_to_add
    else:
        if not amount_stripped.isascii() or not amount_stripped.isdigit():
            return -1, "invalid_amount"
        pence_str = amount_stripped + "00"

    try:
        amount_decimal = Decimal(amount_stripped)
    except InvalidOperation:
        return -1, "invalid_amount"

    if amount_decimal == 0:
        return -1, "invalid_amount"

    amount_pence = int(pence_str)

    return amount_pence, ""


def normalise_validate_category(category: str) -> tuple[str, str]:
    category_stripped = strip_string(category)
    category_normalised = " ".join(category_stripped.split()).lower()

    if not category_normalised:
        return "", "invalid_category"
    else:
        return category_normalised, ""


def construct_rejected_record(
    record: dict[str, str], rejection_reason: str, record_number: int
) -> dict[str, str | int]:
    rejected_record = {
        "source_row_number": record_number,
        "transaction_id": record["transaction_id"],
        "date": record["date"],
        "description": record["description"],
        "amount": record["amount"],
        "category": record["category"],
        "rejection_reason": rejection_reason,
    }

    return rejected_record


def normalise_validate_transaction_records(
    transaction_records: list[dict[str, str]],
) -> tuple[list[dict[str, str | int]], list[dict[str, str | int]]]:
    """Process records in input order using the specified validation precedence
    and accepted-ID deduplication rule.

    Return normalised accepted records and rejected records containing raw fields,
    source row numbers and rejection reasons, without mutating the input records.
    """
    accepted_ids = set()
    accepted_records = []
    rejected_records = []

    for index in range(len(transaction_records)):
        transaction = transaction_records[index]
        source_record_number = index + 2
        rejection_reason = ""

        normalised_id, rejection_reason = normalise_validate_id(
            transaction["transaction_id"]
        )
        if rejection_reason:
            rejected_records.append(
                construct_rejected_record(
                    transaction, rejection_reason, source_record_number
                )
            )
            continue

        normalised_date, rejection_reason = normalise_validate_date(transaction["date"])
        if rejection_reason:
            rejected_records.append(
                construct_rejected_record(
                    transaction, rejection_reason, source_record_number
                )
            )
            continue

        normalised_description, rejection_reason = normalise_validate_description(
            transaction["description"]
        )
        if rejection_reason:
            rejected_records.append(
                construct_rejected_record(
                    transaction, rejection_reason, source_record_number
                )
            )
            continue

        amount_pence, rejection_reason = normalise_validate_amount(
            transaction["amount"]
        )
        if rejection_reason:
            rejected_records.append(
                construct_rejected_record(
                    transaction, rejection_reason, source_record_number
                )
            )
            continue

        normalised_category, rejection_reason = normalise_validate_category(
            transaction["category"]
        )
        if rejection_reason:
            rejected_records.append(
                construct_rejected_record(
                    transaction, rejection_reason, source_record_number
                )
            )
            continue

        if normalised_id in accepted_ids:
            rejected_records.append(
                construct_rejected_record(
                    transaction, "duplicate_transaction_id", source_record_number
                )
            )
            continue

        clean_transaction = {
            "transaction_id": normalised_id,
            "date": normalised_date,
            "description": normalised_description,
            "amount_pence": amount_pence,
            "category": normalised_category,
        }

        accepted_records.append(clean_transaction)
        accepted_ids.add(normalised_id)

    return accepted_records, rejected_records
