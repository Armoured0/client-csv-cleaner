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

    input_path = Path(cli_input_path)
    output_dir = Path(cli_output_dir_path)

    output_paths = {
        (output_dir / "clean_transactions.csv"),
        (output_dir / "rejected_rows.csv"),
        (output_dir / "summary.json"),
    }

    try:
        if input_path.is_symlink():
            print(
                f"Input path is unsupported, is a symlink: {cli_input_path}",
                file=sys.stderr,
            )
            return 1
        elif output_dir.is_symlink():
            print(
                f"Output path is unsupported, is a symlink: {cli_output_dir_path}",
                file=sys.stderr,
            )
            return 1

        for path in output_paths:
            if path.is_symlink():
                print(
                    f"Existing file in output dir is unsupported symlink: {path!s}",
                    file=sys.stderr,
                )
                return 1

        resolved_output_paths = set()

        for path in output_paths:
            resolved_output_paths.add(path.resolve())

        if input_path.resolve() in resolved_output_paths:
            print(f"Input and output path collide: {args.input_path}", file=sys.stderr)
            return 1
    except (OSError, RuntimeError) as error:
        print(f"Could not verify input/output dir paths: {error}", file=sys.stderr)
        return 1

    try:
        transaction_records = load_transactions(input_path)
    except (OSError, UnicodeError, csv.Error) as error:
        print(f"Could not process file {args.input_path}: {error}", file=sys.stderr)
        return 1

    clean_transactions, rejected_transactions = normalise_validate_transaction_records(
        transaction_records
    )

    try:
        summary = write_reports(output_dir, clean_transactions, rejected_transactions)
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
