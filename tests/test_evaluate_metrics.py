import csv
import sys
from pathlib import Path


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from evaluate import LEGACY_METRICS_COLUMNS, METRICS_COLUMNS, append_metrics_rows


def sample_row(prompt_variant: str = "detailed"):
    return {
        "id": "bw_easy_001",
        "difficulty": "easy",
        "method": "llm_only",
        "prompt_variant": prompt_variant,
        "parse_success": True,
        "planner_success": "",
        "plan_valid": True,
        "goal_achieved": True,
        "success": True,
        "plan_length": 2,
        "runtime": "0.1000",
        "error_type": "",
    }


def read_metrics(path: Path):
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return reader.fieldnames, list(reader)


def test_append_metrics_rows_writes_prompt_variant(tmp_path):
    output_path = tmp_path / "metrics.csv"

    append_metrics_rows(output_path, [sample_row()])

    columns, rows = read_metrics(output_path)
    assert columns == METRICS_COLUMNS
    assert rows[0]["prompt_variant"] == "detailed"


def test_append_metrics_rows_migrates_legacy_rows_as_basic(tmp_path):
    output_path = tmp_path / "metrics.csv"
    legacy_row = sample_row()
    legacy_row.pop("prompt_variant")

    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=LEGACY_METRICS_COLUMNS)
        writer.writeheader()
        writer.writerow(legacy_row)

    append_metrics_rows(output_path, [sample_row()])

    columns, rows = read_metrics(output_path)
    assert columns == METRICS_COLUMNS
    assert rows[0]["prompt_variant"] == "basic"
    assert rows[1]["prompt_variant"] == "detailed"
