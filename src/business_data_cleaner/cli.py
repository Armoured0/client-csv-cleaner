import argparse
import csv
import sys
from pathlib import Path

from business_data_cleaner.loaders import load_transactions
from business_data_cleaner.reports import write_reports
from business_data_cleaner.transforms import normalise_validate_transaction_records


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_path", help="specify input csv path")
    parser.add_argument(
        "--output-dir", required=True, help="specify output directory path"
    )

    args = parser.parse_args(arguments)
    cli_input_path = args.input_path
    cli_output_dir_path = args.output_dir

    input_path_resolved = Path(cli_input_path).resolve()
    output_dir_resolved = Path(cli_output_dir_path).resolve()

    output_paths = {
        (output_dir_resolved / "clean_transactions.csv").resolve(),
        (output_dir_resolved / "rejected_rows.csv").resolve(),
        (output_dir_resolved / "summary.json").resolve(),
    }

    if input_path_resolved in output_paths:
        print(f"Input and output path collide: {args.input_path}", file=sys.stderr)
        return 1

    try:
        transaction_records = load_transactions(input_path_resolved)
    except (OSError, UnicodeError, csv.Error) as error:
        print(f"Could not process file {args.input_path}: {error}", file=sys.stderr)
        return 1

    clean_transactions, rejected_transactions = normalise_validate_transaction_records(
        transaction_records
    )

    try:
        summary = write_reports(
            output_dir_resolved, clean_transactions, rejected_transactions
        )
    except OSError as error:
        print(
            f"Could not write to directory {args.output_dir}: {error}", file=sys.stderr
        )
        return 1

    summary_str = (
        f"Input row count: {summary['input_row_count']}\n"
        f"Accepted count: {summary['accepted_count']}\n"
        f"Rejected count: {summary['rejected_count']}\n"
        f"Accepted pence total: {summary['accepted_total_pence']}"
    )

    print(f"Files successfully written to {args.output_dir}\nSummary:")
    print(summary_str)

    return 0
