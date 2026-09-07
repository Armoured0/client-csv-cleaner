import pytest

from pathlib import Path

from business_data_cleaner.cli import main


def test_valid_file(tmp_path, capsys):
    test_input_file_path = tmp_path / "input.csv"
    test_output_dir_path = tmp_path / "output"
    expected_clean_output_path = test_output_dir_path / "clean_transactions.csv"
    expected_rejected_output_path = test_output_dir_path / "rejected_rows.csv"
    expected_summary_output_path = test_output_dir_path / "summary.json"

    input_csv_content = (
        "transaction_id,date,description,amount,category\n"
        '" txn-001 ",01/08/2026,"  Office   supplies  ",12.3,'
        '" Office   Costs "\n'
        'INV_204,2026-08-02,"Café subscription, August",001.20,SOFTWARE\n'
        "BAD_DATE,2026-02-30,Travel booking,18.50,Travel\n"
        '" TXN-001 ",03/08/2026,Duplicate purchase,5.00,Office\n'
        "ITEM_3,2026-08-04,Coffee,0.01,Meals\n"
    )

    test_input_file_path.write_text(input_csv_content, encoding="utf-8")

    expected_clean_output = (
        "transaction_id,date,description,amount_pence,category\n"
        "TXN-001,2026-08-01,Office supplies,1230,office costs\n"
        'INV_204,2026-08-02,"Café subscription, August",120,software\n'
        "ITEM_3,2026-08-04,Coffee,1,meals\n"
    )

    expected_rejected_output = (
        "source_row_number,transaction_id,date,description,amount,category,"
        "rejection_reason\n"
        "4,BAD_DATE,2026-02-30,Travel booking,18.50,Travel,invalid_date\n"
        "5, TXN-001 ,03/08/2026,Duplicate purchase,5.00,Office,"
        "duplicate_transaction_id\n"
    )

    expected_summary_output = (
        "{\n"
        '  "input_row_count": 5,\n'
        '  "accepted_count": 3,\n'
        '  "rejected_count": 2,\n'
        '  "accepted_total_pence": 1351\n'
        "}\n"
    )

    expected_stdout = (
        f"Files successfully written to {test_output_dir_path!s}\n"
        "Summary:\n"
        "Input row count: 5\n"
        "Accepted count: 3\n"
        "Rejected count: 2\n"
        "Accepted pence total: 1351\n"
    )

    assert (
        main([str(test_input_file_path), "--output-dir", str(test_output_dir_path)])
        == 0
    )

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == expected_stdout

    assert (
        expected_clean_output_path.read_text(encoding="utf-8") == expected_clean_output
    )
    assert (
        expected_rejected_output_path.read_text(encoding="utf-8")
        == expected_rejected_output
    )
    assert (
        expected_summary_output_path.read_text(encoding="utf-8")
        == expected_summary_output
    )


def test_header_only_input(tmp_path, capsys):
    test_input_file_path = tmp_path / "header_only.csv"
    test_output_dir_path = tmp_path / "output"
    expected_clean_output_path = test_output_dir_path / "clean_transactions.csv"
    expected_rejected_output_path = test_output_dir_path / "rejected_rows.csv"
    expected_summary_output_path = test_output_dir_path / "summary.json"

    header_only_input = "transaction_id,date,description,amount,category\n"

    test_input_file_path.write_text(header_only_input, encoding="utf-8")

    expected_clean_output = "transaction_id,date,description,amount_pence,category\n"

    expected_rejected_output = (
        "source_row_number,transaction_id,date,description,amount,category,"
        "rejection_reason\n"
    )

    expected_summary_output = (
        "{\n"
        '  "input_row_count": 0,\n'
        '  "accepted_count": 0,\n'
        '  "rejected_count": 0,\n'
        '  "accepted_total_pence": 0\n'
        "}\n"
    )

    expected_stdout = (
        f"Files successfully written to {test_output_dir_path!s}\n"
        "Summary:\n"
        "Input row count: 0\n"
        "Accepted count: 0\n"
        "Rejected count: 0\n"
        "Accepted pence total: 0\n"
    )

    assert (
        main([str(test_input_file_path), "--output-dir", str(test_output_dir_path)])
        == 0
    )

    captured = capsys.readouterr()
    assert captured.err == ""
    assert captured.out == expected_stdout

    assert (
        expected_clean_output_path.read_text(encoding="utf-8") == expected_clean_output
    )
    assert (
        expected_rejected_output_path.read_text(encoding="utf-8")
        == expected_rejected_output
    )
    assert (
        expected_summary_output_path.read_text(encoding="utf-8")
        == expected_summary_output
    )


def test_invalid_arguments(capsys):
    with pytest.raises(SystemExit) as error:
        main([])

    assert error.value.code == 2

    captured = capsys.readouterr()
    assert "usage:" in captured.err
    assert captured.out == ""


def test_missing_input(tmp_path, capsys):
    test_input_file_path = tmp_path / "input.csv"
    test_output_dir_path = tmp_path / "output"

    assert (
        main([str(test_input_file_path), "--output-dir", str(test_output_dir_path)])
        == 1
    )

    captured = capsys.readouterr()
    assert "Could not process file" in captured.err and "input.csv:" in captured.err
    assert captured.out == ""
    assert not test_output_dir_path.exists()


def test_decoding_failure(tmp_path, capsys):
    test_input_file_path = tmp_path / "invalid.csv"
    test_output_dir_path = tmp_path / "output"
    existing_output_paths = {
        test_output_dir_path / "summary.json",
        test_output_dir_path / "clean_transactions.csv",
        test_output_dir_path / "rejected_rows.csv",
    }

    test_output_dir_path.mkdir(parents=True, exist_ok=True)
    
    for file_path in existing_output_paths:
        file_path.write_text("existing file", encoding="utf-8")

    test_input_file_path.write_bytes(
        b"transaction_id,date,description,amount,category\n"
        b"TXN-1,2026-08-01,\xff,10.00,test\n"
    )

    assert (
        main([str(test_input_file_path), "--output-dir", str(test_output_dir_path)])
        == 1
    )

    captured = capsys.readouterr()
    assert (
        "Could not process file" in captured.err
        and "invalid.csv:" in captured.err
        and "utf-8" in captured.err
    )
    assert captured.out == ""

    for existing_file in existing_output_paths:
        assert existing_file.read_text(encoding="utf-8") == "existing file"


def test_csv_structure_failure(tmp_path, capsys):
    test_input_file_path = tmp_path / "invalid_structure.csv"
    test_output_dir_path = tmp_path / "output"
    existing_output_paths = {
        test_output_dir_path / "summary.json",
        test_output_dir_path / "clean_transactions.csv",
        test_output_dir_path / "rejected_rows.csv",
    }

    test_output_dir_path.mkdir(parents=True, exist_ok=True)
    for file_path in existing_output_paths:
        file_path.write_text("existing file", encoding="utf-8")

    malformed_csv = (
        "transaction_id,date,description,amount,category\n"
        "TXN-001,2026-08-01,Office supplies,12.50,test\n"
        "TXN-002,2024-07-22,Calculators,30.00\n"
    )

    test_input_file_path.write_text(malformed_csv, encoding="utf-8")

    assert (
        main([str(test_input_file_path), "--output-dir", str(test_output_dir_path)])
        == 1
    )

    captured = capsys.readouterr()
    assert (
        "Could not process file" in captured.err
        and "invalid_structure.csv" in captured.err
    )
    assert captured.out == ""

    for existing_file in existing_output_paths:
        assert existing_file.read_text(encoding="utf-8") == "existing file"


def test_path_collision_failure(tmp_path, capsys):
    test_input_file_path = tmp_path / "output" / "summary.json"
    test_output_dir_path = tmp_path / "output"
    existing_output_path = test_output_dir_path / "summary.json"

    test_output_dir_path.mkdir(parents=True, exist_ok=True)
    existing_output_path.write_text("collision test", encoding="utf-8")

    assert (
        main([str(test_input_file_path), "--output-dir", str(test_output_dir_path)])
        == 1
    )

    captured = capsys.readouterr()
    assert (
        "Input and output path collide:" in captured.err
        and "summary.json" in captured.err
    )
    assert captured.out == ""

    assert test_input_file_path.read_text(encoding="utf-8") == "collision test"


def test_path_verification_failure(tmp_path, capsys, monkeypatch):
    input_path = tmp_path / "input.csv"
    output_dir = tmp_path / "output"

    original_input = (
        "transaction_id,date,description,amount,category\n"
        "ABC-001,2026-08-27,Office supplies,12.50,expenses\n"
    )
    input_path.write_text(original_input, encoding="utf-8")

    # This function deliberately fails whenever it is called.
    def fail_resolution(path, strict=False):
        raise OSError("Deliberate test failure")

    # Temporarily replace resolve() while main() runs.
    with monkeypatch.context() as patch:
        patch.setattr(Path, "resolve", fail_resolution)

        result = main([
            str(input_path),
            "--output-dir",
            str(output_dir),
        ])

    captured = capsys.readouterr()

    assert result == 1
    assert captured.out == ""
    assert captured.err == (
        "Could not verify input/output dir paths: "
        "Deliberate test failure\n"
    )
    assert not output_dir.exists()
    assert input_path.read_text(encoding="utf-8") == original_input


def test_symlink_in_output_dir_failure(tmp_path, capsys):
    input_path = tmp_path / "input.csv"
    output_dir = tmp_path / "output"
    clean_output_path = output_dir / "clean_transactions.csv"

    original_input = (
        "transaction_id,date,description,amount,category\n"
        "ABC-001,2026-08-27,Office supplies,12.50,expenses\n"
    )

    input_path.write_text(original_input, encoding="utf-8")
    output_dir.mkdir()

    try:
        clean_output_path.symlink_to(input_path)
    except (OSError, NotImplementedError) as error:
        pytest.skip(f"Symbolic links are unavailable: {error}")

    assert clean_output_path.is_symlink()
    assert clean_output_path.resolve() == input_path.resolve()

    assert main([str(input_path), "--output-dir", str(output_dir)]) == 1

    captured = capsys.readouterr()

    assert "Existing file in output dir is unsupported symlink:" in captured.err
    assert str(clean_output_path) in captured.err
    assert captured.out == ""

    assert input_path.read_text(encoding="utf-8") == original_input
    assert not (output_dir / "rejected_rows.csv").exists()
    assert not (output_dir / "summary.json").exists()


def test_file_system_failure(tmp_path, capsys):
    test_input_file_path = tmp_path / "input.csv"
    test_output_dir_path = tmp_path / "blocked.txt"

    test_output_dir_path.write_text("blocking file", encoding="utf-8")

    csv_content = (
        "transaction_id,date,description,amount,category\n"
        "ABC-001,2026-08-27,Office supplies,12.50,expenses\n"
    )

    test_input_file_path.write_text(csv_content, encoding="utf-8")

    assert (
        main([str(test_input_file_path), "--output-dir", str(test_output_dir_path)])
        == 1
    )

    captured = capsys.readouterr()
    assert (
        "Could not write to directory" in captured.err and "blocked.txt" in captured.err
    )
    assert captured.out == ""
