import csv
import json
from pathlib import Path


def write_summary_json(
    output_dir: Path,
    summary_data: dict[str, int],
) -> None:
    """Replace summary.json with the supplied summary data."""
    summary_json_path = output_dir / "summary.json"

    with summary_json_path.open("w", encoding="utf-8") as summary_json_file:
        json.dump(summary_data, summary_json_file, indent=2)
        summary_json_file.write("\n")


def write_output_csvs(
    output_dir: Path,
    clean_transactions: list[dict[str, str | int]],
    rejected_transactions: list[dict[str, str | int]],
) -> None:
    """Replace both stable-schema CSV outputs without mutating the inputs."""
    clean_csv_path = output_dir / "clean_transactions.csv"
    rejected_csv_path = output_dir / "rejected_rows.csv"

    clean_fieldnames = [
        "transaction_id",
        "date",
        "description",
        "amount_pence",
        "category",
    ]

    with clean_csv_path.open("w", encoding="utf-8", newline="") as clean_csv_file:
        writer = csv.DictWriter(clean_csv_file, fieldnames=clean_fieldnames)
        writer.writeheader()
        writer.writerows(clean_transactions)

    rejected_fieldnames = [
        "source_row_number",
        "transaction_id",
        "date",
        "description",
        "amount",
        "category",
        "rejection_reason",
    ]

    with rejected_csv_path.open("w", encoding="utf-8", newline="") as rejected_csv_file:
        writer = csv.DictWriter(rejected_csv_file, fieldnames=rejected_fieldnames)
        writer.writeheader()
        writer.writerows(rejected_transactions)


def generate_summary(
    clean_transactions: list[dict[str, str | int]],
    rejected_transactions: list[dict[str, str | int]],
) -> dict[str, int]:
    """Return the exact four-field summary without mutating either input."""
    accepted_count = len(clean_transactions)
    rejected_count = len(rejected_transactions)
    total_row_count = accepted_count + rejected_count
    accepted_total_pence = 0

    for transaction in clean_transactions:
        accepted_total_pence += transaction["amount_pence"]

    summary_data = {
        "input_row_count": total_row_count,
        "accepted_count": accepted_count,
        "rejected_count": rejected_count,
        "accepted_total_pence": accepted_total_pence,
    }

    return summary_data


def write_reports(
    output_dir: Path,
    clean_transactions: list[dict[str, str | int]],
    rejected_transactions: list[dict[str, str | int]],
) -> dict[str, int]:
    """Create the output directory, replace all report files, and return the summary."""
    summary_data = generate_summary(clean_transactions, rejected_transactions)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_output_csvs(output_dir, clean_transactions, rejected_transactions)
    write_summary_json(output_dir, summary_data)

    return summary_data
