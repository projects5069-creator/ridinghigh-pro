"""M1 — queue reader for The Auto Dancer.

Parses a human-written QUEUE file (task SOURCE for a MANUAL run) into ordered
(task_id, budget, note) rows. budget/note optional (default budget 150000);
blank/#-comment lines skipped; a malformed task id is logged to stderr and
skipped — never crashes the whole file. Missing file → main() exit 1.
"""
import os
import sys

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "scripts",
        "overnight",
    ),
)

import read_queue  # noqa: E402


def _write(tmp_path, text):
    p = tmp_path / "QUEUE_test.md"
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_full_line(tmp_path):
    path = _write(tmp_path, "- TASK-159 | budget: 120k | note: x\n")
    assert list(read_queue.read_queue(path)) == [("TASK-159", 120000, "x")]


def test_minimal_line(tmp_path):
    path = _write(tmp_path, "- TASK-228\n")
    assert list(read_queue.read_queue(path)) == [("TASK-228", 150000, "")]


def test_raw_numeric_budget(tmp_path):
    path = _write(tmp_path, "- TASK-1 | budget: 80000\n")
    assert list(read_queue.read_queue(path)) == [("TASK-1", 80000, "")]


def test_empty_or_bad_budget_defaults(tmp_path):
    path = _write(tmp_path, "- TASK-1 | budget: \n- TASK-2 | budget: abc\n")
    rows = list(read_queue.read_queue(path))
    assert rows == [("TASK-1", 150000, ""), ("TASK-2", 150000, "")]


def test_blank_and_comment_skipped(tmp_path):
    path = _write(tmp_path, "# header comment\n\n- TASK-7\n\n#- TASK-8 (disabled)\n")
    assert list(read_queue.read_queue(path)) == [("TASK-7", 150000, "")]


def test_bad_id_skipped_with_stderr(tmp_path, capsys):
    path = _write(tmp_path, "- TASK-5\n- BADID-9 | note: nope\n- TASK-6\n")
    rows = list(read_queue.read_queue(path))
    assert rows == [("TASK-5", 150000, ""), ("TASK-6", 150000, "")]
    err = capsys.readouterr().err
    assert "BADID-9" in err and "skipped" in err


def test_missing_file_exit_1(capsys):
    rc = read_queue.main(["read_queue.py", "/tmp/does_not_exist_rh_QUEUE.md"])
    assert rc == 1
    assert "not found" in capsys.readouterr().err


def test_order_preserved(tmp_path):
    path = _write(tmp_path, "- TASK-30\n- TASK-2\n- TASK-19\n")
    ids = [r[0] for r in read_queue.read_queue(path)]
    assert ids == ["TASK-30", "TASK-2", "TASK-19"]
