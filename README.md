# Client CSV Cleaner

Client CSV Cleaner is a command-line Python tool for cleaning transaction exports from a fixed five-column CSV format. It normalises usable rows, separates invalid or duplicate rows for review, and produces an exact integer-pence summary.

The tool is intended for repeatable cleanup rather than one-off manual editing. Running it again with the same input replaces its three output files instead of appending duplicate data.

## What it does

- Accepts comma-delimited UTF-8 CSV, including an optional UTF-8 byte-order mark.
- Normalises common header, whitespace, identifier, date, category and GBP amount variations.
- Validates real dates and positive amounts without using binary floating point for money.
- Keeps the first fully valid occurrence of each normalised transaction ID.
- Preserves rejected source values with their logical row number and one stable reason code.
- Writes clean transactions, rejected rows and a JSON summary to a selected directory.
- Fails clearly when the complete file cannot be mapped or processed safely.

## Requirements

- Python 3.12 or newer
- No third-party runtime dependencies

Use a virtual environment so the installation remains isolated from other Python projects.

## Installation from source

From the directory containing `pyproject.toml`, with a Python 3.12+ virtual environment activated:

```bash
python -m pip install -e .
```

For development, testing and linting, install the optional development tools instead:

```bash
python -m pip install -e ".[dev]"
```

This is an editable source installation. This project does not require you to build or publish a distribution before running it.

## Usage

```bash
python -m business_data_cleaner INPUT.csv --output-dir OUTPUT_DIRECTORY
```

For example, run the supplied sample from the project directory:

```bash
python -m business_data_cleaner data/sample/pipeline_sample_input.csv --output-dir output
```

The sample run reports:

```text
Files successfully written to output
Summary:
Input row count: 14
Accepted count: 5
Rejected count: 9
Accepted pence total: 5350
```

Use `--help` to view the command-line arguments:

```bash
python -m business_data_cleaner --help
```

## Input contract

The input must be comma-delimited CSV encoded as UTF-8. An optional UTF-8 byte-order mark is accepted. The filename extension is not used to determine validity.

After header normalisation, the file must contain exactly these five columns, in any order:

```text
transaction_id,date,description,amount,category
```

Header normalisation:

1. removes surrounding whitespace;
2. converts letters to lowercase;
3. replaces each internal run of whitespace or hyphens with one underscore.

For example, ` Transaction ID ` and `transaction-id` both become `transaction_id`. Missing, extra, blank or colliding headers make the complete file unusable.

Normal CSV quoting is supported, including commas and line breaks inside quoted fields. Every data record must contain exactly five fields. Malformed CSV or a structurally short or long record makes the complete file unusable because its field mapping cannot be trusted. Blank physical lines between records are ignored. Leading blank lines before the header are not supported.

A completely empty file is invalid. A header-only file is valid and produces two header-only CSV files plus a zero-valued summary.

### Field rules

| Field | Accepted input | Clean output |
| --- | --- | --- |
| `transaction_id` | Non-empty after trimming; ASCII letters, digits, hyphens and underscores only; no internal whitespace. | Uppercase text. |
| `date` | Exactly `YYYY-MM-DD` or UK-style `DD/MM/YYYY`, using zero-padded ASCII digits and representing a real calendar date. | ISO `YYYY-MM-DD`. |
| `description` | Non-empty after trimming and whitespace normalisation. | Internal whitespace runs become one ordinary space; case and punctuation are preserved. |
| `amount` | Positive ASCII digits with an optional decimal point and one or two fractional digits, such as `12`, `12.3` or `12.34`. | Exact integer pence in `amount_pence`. |
| `category` | Non-empty after trimming and whitespace normalisation. | Internal whitespace runs become one ordinary space and letters become lowercase. |

Leading zeroes are accepted: `001.20` becomes `120` pence. Zero, negative values, signs, currency symbols, comma grouping, exponent notation, `NaN`, `Infinity`, trailing decimal points and more than two fractional digits are rejected.

## Row rejection and duplicate handling

A correctly structured file may contain invalid rows. These are expected data outcomes: the command still succeeds, and each row is written to `rejected_rows.csv` with one reason.

When a row has several problems, only the first reason in this precedence order is recorded:

| Precedence | Reason code |
| ---: | --- |
| 1 | `invalid_transaction_id` |
| 2 | `invalid_date` |
| 3 | `invalid_description` |
| 4 | `invalid_amount` |
| 5 | `invalid_category` |
| 6 | `duplicate_transaction_id` |

Duplicate checking uses the normalised uppercase transaction ID. The first fully valid occurrence wins. An earlier rejected occurrence does not reserve its ID, so a later valid occurrence may still be accepted.

## Outputs

The output directory and any missing parents are created when possible. A successful run replaces only these three fixed files and leaves unrelated files untouched.

### `clean_transactions.csv`

Contains accepted rows in input order with this exact schema:

```text
transaction_id,date,description,amount_pence,category
```

`amount_pence` is positive base-10 integer text. For example, GBP `12.30` is written as `1230`.

### `rejected_rows.csv`

Contains rejected rows in input order with this exact schema:

```text
source_row_number,transaction_id,date,description,amount,category,rejection_reason
```

The five source fields preserve the values returned by the CSV parser before trimming or normalisation. `source_row_number` counts logical CSV records with the header as record 1, so the first data record is 2. A quoted record spanning several physical lines still counts as one record.

### `summary.json`

Contains exactly four integer fields:

```json
{
  "input_row_count": 14,
  "accepted_count": 5,
  "rejected_count": 9,
  "accepted_total_pence": 5350
}
```

`input_row_count` always equals `accepted_count + rejected_count`. The total includes accepted rows only.

## Compact before-and-after example

Input:

```csv
transaction_id,date,description,amount,category
" txn-001 ",01/08/2026,"  Office   supplies  ",12.3," Office   Costs "
BAD_DATE,2026-02-30,Travel booking,18.50,Travel
TXN-001,03/08/2026,Duplicate purchase,5.00,Office
```

`clean_transactions.csv`:

```csv
transaction_id,date,description,amount_pence,category
TXN-001,2026-08-01,Office supplies,1230,office costs
```

`rejected_rows.csv`:

```csv
source_row_number,transaction_id,date,description,amount,category,rejection_reason
3,BAD_DATE,2026-02-30,Travel booking,18.50,Travel,invalid_date
4,TXN-001,03/08/2026,Duplicate purchase,5.00,Office,duplicate_transaction_id
```

`summary.json`:

```json
{
  "input_row_count": 3,
  "accepted_count": 1,
  "rejected_count": 2,
  "accepted_total_pence": 1230
}
```

## Errors and exit statuses

| Status | Meaning |
| ---: | --- |
| `0` | The file was processed successfully. Individual rejected rows may still be present. |
| `1` | The input could not be read, decoded or mapped safely; an input/output collision was detected; or an output could not be written. |
| `2` | Command-line arguments were missing or invalid; `argparse` prints the usage error. |

Successful summaries are printed to standard output. Expected usage, input and output failures are printed to standard error.

The program validates the complete file before writing reports. An unusable input therefore does not create or modify the three target output files. It also refuses to run when the resolved input path is one of its intended output paths, including when an output filename is a symbolic link to the input.

## Repeatability and file safety

- Successful runs regenerate the three outputs instead of appending.
- Input and output row order is deterministic.
- The source CSV is opened read-only and is not modified.
- Existing target outputs remain unchanged when decoding or CSV-structure validation fails.
- Unrelated files in the output directory are preserved.

## Testing and quality checks

Install the development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Then run:

```bash
pytest
ruff check .
ruff format --check .
```

The tests cover field validation and normalisation, rejection precedence, accepted-only duplicate state, raw rejected values, non-mutation, stable output schemas, exact summaries, empty input data, repeat execution, command statuses, malformed files, preservation of existing outputs and direct or symbolic-link input/output collisions.

## Design overview

The project separates deterministic business rules from files and process behaviour:

- `loaders.py` reads CSV and rejects untrustworthy file structure.
- `transforms.py` contains field and row validation, normalisation and deduplication.
- `reports.py` calculates the summary and writes the three deterministic reports.
- `cli.py` owns arguments, terminal messages, expected file errors and process statuses.
- `__main__.py` is the thin entry point used by `python -m business_data_cleaner`.

Accepted money is represented as integer pence throughout reporting. No accepted money calculation uses binary floating point.

## Limitations

Version 1.0.0 deliberately supports a narrow contract:

- one input file per command;
- comma-delimited UTF-8 CSV only;
- exactly five known input columns;
- positive GBP-style amounts only—no zero values, refunds, negative transactions, other currencies, conversion or tax calculation;
- only ISO `YYYY-MM-DD` and UK `DD/MM/YYYY` dates;
- no automatic delimiter, encoding, locale, currency or date-format detection;
- no fuzzy correction, category remapping, arbitrary-column pass-through or interactive repair;
- no Excel, JSON, database, API, graphical interface, scheduling or hosted service support;
- no streaming or guarantee for files too large to fit comfortably in memory.

The three output files are not replaced as one atomic transaction. If an unexpected write failure occurs after one output has been written, previously written sibling outputs are not rolled back. Input/output identity protection covers resolved paths and symbolic links; hard-link aliases are outside the v1 contract.

## License

This project is licensed under the MIT License. See [MIT License](LICENSE).
