import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path
from typing import Callable, Dict, List, Tuple

import matplotlib.pyplot as plt


DIFFICULTY_ORDER = {
    "easy": 0,
    "medium": 1,
    "hard": 2,
}


def parse_bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def load_metrics(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def ensure_output_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def save_bar_chart(
    labels: List[str],
    values: List[float],
    title: str,
    ylabel: str,
    output_path: Path,
    ylim: Tuple[float, float] | None = None,
) -> None:
    plt.figure(figsize=(10, 6))
    plt.bar(labels, values)

    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=30, ha="right")

    if ylim is not None:
        plt.ylim(*ylim)

    for index, value in enumerate(values):
        label = f"{value:.2f}" if value <= 1 else f"{value:.1f}"
        plt.text(index, value, label, ha="center", va="bottom")

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()

    print(f"Wrote {output_path}")


def success_rate_by_group(
    rows: List[Dict[str, str]],
    key_fn: Callable[[Dict[str, str]], str],
) -> Tuple[List[str], List[float]]:
    total = Counter()
    success = Counter()

    for row in rows:
        key = key_fn(row)
        total[key] += 1

        if parse_bool(row.get("success", "")):
            success[key] += 1

    labels = sorted(total.keys())
    values = [success[label] / total[label] for label in labels]

    return labels, values


def plot_success_rate_by_method(rows: List[Dict[str, str]], output_dir: Path) -> None:
    labels, values = success_rate_by_group(rows, lambda row: row["method"])

    save_bar_chart(
        labels=labels,
        values=values,
        title="Success Rate by Method",
        ylabel="Success Rate",
        output_path=output_dir / "success_rate_by_method.png",
        ylim=(0, 1.05),
    )


def difficulty_method_key(row: Dict[str, str]) -> str:
    return f"{row['difficulty']}\n{row['method']}"


def sort_difficulty_method_labels(labels: List[str]) -> List[str]:
    def sort_key(label: str) -> Tuple[int, str]:
        difficulty, method = label.split("\n", 1)
        return DIFFICULTY_ORDER.get(difficulty, 99), method

    return sorted(labels, key=sort_key)


def plot_success_rate_by_difficulty(rows: List[Dict[str, str]], output_dir: Path) -> None:
    labels, values = success_rate_by_group(rows, difficulty_method_key)

    label_to_value = dict(zip(labels, values))
    sorted_labels = sort_difficulty_method_labels(labels)
    sorted_values = [label_to_value[label] for label in sorted_labels]

    save_bar_chart(
        labels=sorted_labels,
        values=sorted_values,
        title="Success Rate by Difficulty and Method",
        ylabel="Success Rate",
        output_path=output_dir / "success_rate_by_difficulty.png",
        ylim=(0, 1.05),
    )


def normalize_error_type(error_type: str) -> str:
    error_type = str(error_type).strip()

    if not error_type:
        return "none"

    return error_type.split(":", 1)[0].strip()


def plot_error_distribution(rows: List[Dict[str, str]], output_dir: Path) -> None:
    errors = Counter()

    for row in rows:
        if parse_bool(row.get("success", "")):
            continue

        errors[normalize_error_type(row.get("error_type", ""))] += 1

    if not errors:
        labels = ["no_errors"]
        values = [0]
    else:
        labels = list(errors.keys())
        values = list(errors.values())

    save_bar_chart(
        labels=labels,
        values=values,
        title="Error Distribution",
        ylabel="Count",
        output_path=output_dir / "error_distribution.png",
    )


def plot_avg_plan_length(rows: List[Dict[str, str]], output_dir: Path) -> None:
    lengths_by_method: Dict[str, List[int]] = defaultdict(list)

    for row in rows:
        if not parse_bool(row.get("success", "")):
            continue

        method = row["method"]

        try:
            plan_length = int(row.get("plan_length", "0"))
        except ValueError:
            plan_length = 0

        lengths_by_method[method].append(plan_length)

    labels = sorted(lengths_by_method.keys())

    if not labels:
        labels = ["no_successful_plans"]
        values = [0.0]
    else:
        values = [
            sum(lengths_by_method[label]) / len(lengths_by_method[label])
            for label in labels
        ]

    save_bar_chart(
        labels=labels,
        values=values,
        title="Average Plan Length by Method",
        ylabel="Average Plan Length",
        output_path=output_dir / "avg_plan_length.png",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--metrics",
        default="results/metrics.csv",
        help="Path to unified metrics CSV",
    )
    parser.add_argument(
        "--output-dir",
        default="results/figures",
        help="Directory to save generated figures",
    )
    args = parser.parse_args()

    metrics_path = Path(args.metrics)
    output_dir = Path(args.output_dir)

    if not metrics_path.exists():
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")

    rows = load_metrics(metrics_path)

    if not rows:
        raise ValueError(f"Metrics file is empty: {metrics_path}")

    ensure_output_dir(output_dir)

    plot_success_rate_by_method(rows, output_dir)
    plot_success_rate_by_difficulty(rows, output_dir)
    plot_error_distribution(rows, output_dir)
    plot_avg_plan_length(rows, output_dir)


if __name__ == "__main__":
    main()