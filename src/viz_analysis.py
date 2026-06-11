from pathlib import Path
import warnings

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.ticker import PercentFormatter
import numpy as np
import pandas as pd


MODEL_ORDER = ["qwen2.5-3b", "qwen2.5-7b", "llama3.1-8b"]
PROMPT_ORDER = ["basic", "detailed"]
DIFFICULTY_ORDER = ["easy", "medium", "hard"]
METHOD_ORDER = ["llm_only", "llm_planner"]

MODEL_LABELS = {
    "qwen2.5-3b": "Qwen 2.5 3B",
    "qwen2.5-7b": "Qwen 2.5 7B",
    "llama3.1-8b": "Llama 3.1 8B",
}
METHOD_LABELS = {
    "llm_only": "LLM-only",
    "llm_planner": "LLM + planner",
}
PROMPT_LABELS = {
    "basic": "Basic",
    "detailed": "Detailed",
}

METHOD_COLORS = {
    "llm_only": "#4C78A8",
    "llm_planner": "#F58518",
}
CONFIG_COLORS = {
    ("basic", "llm_only"): "#9ECAE1",
    ("detailed", "llm_only"): "#3182BD",
    ("basic", "llm_planner"): "#FDAE6B",
    ("detailed", "llm_planner"): "#E6550D",
}

RESULT_SPECS = [
    (
        "qwen2.5-3b",
        "basic",
        Path("results/qwen2.5-3b-instruct/basic/metrics.csv"),
    ),
    (
        "qwen2.5-3b",
        "detailed",
        Path("results/qwen2.5-3b-instruct/detailed/metrics.csv"),
    ),
    (
        "qwen2.5-7b",
        "basic",
        Path("results/qwen2.5-7b-instruct/basic/metrics.csv"),
    ),
    (
        "qwen2.5-7b",
        "detailed",
        Path("results/qwen2.5-7b-instruct/detailed/metrics.csv"),
    ),
    (
        "llama3.1-8b",
        "basic",
        Path("results/llama3.1-8b/basic/metrics.csv"),
    ),
    (
        "llama3.1-8b",
        "detailed",
        Path("results/llama3.1-8b/detailed/metrics.csv"),
    ),
]

BOOL_COLUMNS = [
    "success",
    "parse_success",
    "plan_valid",
    "goal_achieved",
    "planner_success",
]
REQUIRED_COLUMNS = {
    "id",
    "difficulty",
    "method",
    "parse_success",
    "planner_success",
    "plan_valid",
    "goal_achieved",
    "success",
    "plan_length",
    "runtime",
    "error_type",
}


pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 160)
plt.rcParams.update(
    {
        "figure.figsize": (10, 5),
        "axes.titlesize": 13,
        "axes.labelsize": 11,
        "legend.fontsize": 9,
        "figure.dpi": 110,
    }
)


def annotate_percent_bars(ax, signed=False, fontsize=8):
    for patch in ax.patches:
        height = patch.get_height()
        if not np.isfinite(height):
            continue
        label = f"{height:+.1%}" if signed else f"{height:.1%}"
        offset = 3 if height >= 0 else -12
        va = "bottom" if height >= 0 else "top"
        ax.annotate(
            label,
            (patch.get_x() + patch.get_width() / 2, height),
            xytext=(0, offset),
            textcoords="offset points",
            ha="center",
            va=va,
            fontsize=fontsize,
        )


def percent_style(table):
    return table.style.format(
        lambda value: "—" if pd.isna(value) else f"{value:.1%}"
    )


def style_percent_table(table, caption):
    return percent_style(table).set_caption(caption)


def style_design_counts(count_pivot, imbalance_mask):
    def highlight_imbalance(data):
        return pd.DataFrame(
            np.where(
                imbalance_mask,
                "background-color: #ffd6d6",
                "",
            ),
            index=data.index,
            columns=data.columns,
        )

    return (
        count_pivot.style
        .apply(highlight_imbalance, axis=None)
        .set_caption("Số bài theo toàn bộ factorial cells")
    )


def style_method_effect(method_effect):
    return (
        method_effect.style
        .format({"success_rate": "{:.1%}", "n": "{:,.0f}"})
        .set_caption("Main effect của method")
    )


def style_sensitivity(sensitivity_table):
    return (
        sensitivity_table.style
        .format({"sensitivity": "{:.1%}"})
        .set_caption("So sánh độ nhạy trung bình")
    )


def style_error_counts(error_counts):
    return (
        error_counts.style
        .background_gradient(cmap="Reds", axis=None)
        .set_caption("Số lỗi theo model × prompt × method")
    )


def pp(value):
    return f"{value * 100:+.1f} điểm %"


def parse_bool(value):
    if pd.isna(value):
        return pd.NA
    if isinstance(value, (bool, np.bool_)):
        return bool(value)
    if isinstance(value, (int, float, np.integer, np.floating)):
        if value == 1:
            return True
        if value == 0:
            return False
    text = str(value).strip().lower()
    if text in {"true", "1"}:
        return True
    if text in {"false", "0"}:
        return False
    return pd.NA


def load_all_metrics(root_dir) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return the combined metrics dataframe and load inventory."""
    root_dir = Path(root_dir)
    frames = []
    load_rows = []

    for model, prompt_variant, relative_path in RESULT_SPECS:
        path = root_dir / relative_path

        if not path.exists():
            warnings.warn(f"Thiếu file: {path}")
            load_rows.append(
                {
                    "model": model,
                    "prompt_variant": prompt_variant,
                    "path": str(path),
                    "status": "missing",
                    "rows": 0,
                }
            )
            continue

        frame = pd.read_csv(path)
        missing_columns = sorted(REQUIRED_COLUMNS - set(frame.columns))

        if missing_columns:
            warnings.warn(f"Bỏ qua {path}: thiếu cột {missing_columns}")
            load_rows.append(
                {
                    "model": model,
                    "prompt_variant": prompt_variant,
                    "path": str(path),
                    "status": f"schema thiếu: {', '.join(missing_columns)}",
                    "rows": len(frame),
                }
            )
            continue

        frame["model"] = model
        frame["prompt_variant"] = prompt_variant

        for column in BOOL_COLUMNS:
            frame[column] = frame[column].map(parse_bool).astype("boolean")

        frames.append(frame)
        load_rows.append(
            {
                "model": model,
                "prompt_variant": prompt_variant,
                "path": str(path),
                "status": "loaded",
                "rows": len(frame),
            }
        )

    inventory = pd.DataFrame(load_rows)

    if frames:
        df = pd.concat(frames, ignore_index=True)
    else:
        df = pd.DataFrame(
            columns=sorted(REQUIRED_COLUMNS | {"model", "prompt_variant"})
        )

    df["model"] = pd.Categorical(
        df["model"],
        categories=MODEL_ORDER,
        ordered=True,
    )
    df["prompt_variant"] = pd.Categorical(
        df["prompt_variant"],
        categories=PROMPT_ORDER,
        ordered=True,
    )
    df["difficulty"] = pd.Categorical(
        df["difficulty"],
        categories=DIFFICULTY_ORDER,
        ordered=True,
    )
    df["method"] = pd.Categorical(
        df["method"],
        categories=METHOD_ORDER,
        ordered=True,
    )

    return df, inventory


def plot_central_heatmap(central_table) -> Figure:
    fig, ax = plt.subplots(figsize=(8.5, 6))
    heat_values = central_table.to_numpy(dtype=float)
    image = ax.imshow(
        heat_values,
        cmap="YlGnBu",
        vmin=0,
        vmax=1,
        aspect="auto",
    )

    ax.set_xticks(range(len(METHOD_ORDER)))
    ax.set_xticklabels([METHOD_LABELS[method] for method in METHOD_ORDER])
    ax.set_yticks(range(len(central_table.index)))
    ax.set_yticklabels(
        [
            f"{MODEL_LABELS[model]} | {PROMPT_LABELS[prompt]}"
            for model, prompt in central_table.index
        ]
    )
    ax.set_xlabel("Method")
    ax.set_ylabel("Model × prompt variant")
    ax.set_title("Heatmap success rate của factorial 3 yếu tố")

    for row in range(heat_values.shape[0]):
        for column in range(heat_values.shape[1]):
            value = heat_values[row, column]
            label = "—" if np.isnan(value) else f"{value:.1%}"
            color = (
                "white"
                if np.isfinite(value) and value >= 0.55
                else "black"
            )
            ax.text(
                column,
                row,
                label,
                ha="center",
                va="center",
                color=color,
                fontweight="bold",
            )

    colorbar = fig.colorbar(image, ax=ax, pad=0.02)
    colorbar.ax.yaxis.set_major_formatter(PercentFormatter(1))
    fig.tight_layout()
    return fig


def plot_method_effect(method_effect) -> Figure:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.bar(
        [METHOD_LABELS[method] for method in METHOD_ORDER],
        method_effect["success_rate"],
        color=[METHOD_COLORS[method] for method in METHOD_ORDER],
    )
    ax.set_ylim(
        0,
        max(1.0, method_effect["success_rate"].max() + 0.12),
    )
    ax.set_ylabel("Success rate")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Success rate trung bình theo method")
    annotate_percent_bars(ax)
    fig.tight_layout()
    return fig


def plot_model_effect(model_effect) -> Figure:
    model_columns = pd.MultiIndex.from_product(
        [PROMPT_ORDER, METHOD_ORDER],
        names=["prompt_variant", "method"],
    )
    x = np.arange(len(MODEL_ORDER))
    width = 0.19
    fig, ax = plt.subplots(figsize=(11, 5.5))

    for offset_index, (prompt, method) in enumerate(model_columns):
        offset = (offset_index - 1.5) * width
        ax.bar(
            x + offset,
            model_effect[(prompt, method)],
            width,
            label=f"{PROMPT_LABELS[prompt]} | {METHOD_LABELS[method]}",
            color=CONFIG_COLORS[(prompt, method)],
        )

    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS[model] for model in MODEL_ORDER])
    ax.set_xlabel("Model")
    ax.set_ylabel("Success rate")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylim(0, 1.12)
    ax.set_title("Main effect của model trong từng prompt × method")
    ax.legend(ncol=2, loc="upper left")
    annotate_percent_bars(ax, fontsize=7)
    fig.tight_layout()
    return fig


def plot_prompt_effect(prompt_effect) -> Figure:
    prompt_columns = pd.MultiIndex.from_product(
        [MODEL_ORDER, METHOD_ORDER],
        names=["model", "method"],
    )
    x = np.arange(len(PROMPT_ORDER))
    width = 0.12
    palette = plt.cm.tab10(np.linspace(0, 1, len(prompt_columns)))
    fig, ax = plt.subplots(figsize=(12, 5.5))

    for offset_index, ((model, method), color) in enumerate(
        zip(prompt_columns, palette)
    ):
        offset = (
            offset_index - (len(prompt_columns) - 1) / 2
        ) * width
        ax.bar(
            x + offset,
            prompt_effect[(model, method)],
            width,
            label=f"{MODEL_LABELS[model]} | {METHOD_LABELS[method]}",
            color=color,
        )

    ax.set_xticks(x)
    ax.set_xticklabels([PROMPT_LABELS[prompt] for prompt in PROMPT_ORDER])
    ax.set_xlabel("Prompt variant")
    ax.set_ylabel("Success rate")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_ylim(0, 1.12)
    ax.set_title("Main effect của prompt trong từng model × method")
    ax.legend(ncol=2, loc="upper left")
    annotate_percent_bars(ax, fontsize=7)
    fig.tight_layout()
    return fig


def plot_prompt_delta_by_method(delta_method) -> Figure:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(
        [METHOD_LABELS[method] for method in METHOD_ORDER],
        delta_method,
        color=[METHOD_COLORS[method] for method in METHOD_ORDER],
    )
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Detailed − Basic")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Prompt delta theo method")
    annotate_percent_bars(ax, signed=True)
    fig.tight_layout()
    return fig


def plot_prompt_delta_by_model(delta_model_method) -> Figure:
    x = np.arange(len(MODEL_ORDER))
    width = 0.34
    fig, ax = plt.subplots(figsize=(10, 5))

    for index, method in enumerate(METHOD_ORDER):
        ax.bar(
            x + (index - 0.5) * width,
            delta_model_method[method],
            width,
            label=METHOD_LABELS[method],
            color=METHOD_COLORS[method],
        )

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels([MODEL_LABELS[model] for model in MODEL_ORDER])
    ax.set_xlabel("Model")
    ax.set_ylabel("Detailed − Basic")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Prompt delta theo model, giữ riêng method")
    ax.legend()
    annotate_percent_bars(ax, signed=True, fontsize=8)
    fig.tight_layout()
    return fig


def plot_sensitivity(sensitivity_table) -> Figure:
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.bar(
        sensitivity_table.index,
        sensitivity_table["sensitivity"],
        color=["#72B7B2", "#B279A2"],
    )
    ax.set_ylabel("Độ nhạy trung bình")
    ax.yaxis.set_major_formatter(PercentFormatter(1))
    ax.set_title("Prompt sensitivity so với model sensitivity")
    ax.set_ylim(
        0,
        sensitivity_table["sensitivity"].max() + 0.12,
    )
    annotate_percent_bars(ax)
    fig.tight_layout()
    return fig


def plot_difficulty_scaling(difficulty_rates) -> Figure:
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(16, 4.8),
        sharey=True,
    )
    x = np.arange(len(DIFFICULTY_ORDER))

    for ax, model in zip(axes, MODEL_ORDER):
        for prompt in PROMPT_ORDER:
            for method in METHOD_ORDER:
                values = difficulty_rates.loc[
                    (model, prompt, method)
                ].reindex(DIFFICULTY_ORDER)
                ax.plot(
                    x,
                    values,
                    marker="o",
                    linewidth=2,
                    linestyle="-" if prompt == "basic" else "--",
                    color=METHOD_COLORS[method],
                    label=(
                        f"{PROMPT_LABELS[prompt]} | "
                        f"{METHOD_LABELS[method]}"
                    ),
                )

                for x_pos, value in zip(x, values):
                    if pd.notna(value):
                        ax.annotate(
                            f"{value:.0%}",
                            (x_pos, value),
                            xytext=(0, 5),
                            textcoords="offset points",
                            ha="center",
                            fontsize=7,
                        )

        ax.set_title(MODEL_LABELS[model])
        ax.set_xticks(x)
        ax.set_xticklabels(
            [level.title() for level in DIFFICULTY_ORDER]
        )
        ax.set_xlabel("Difficulty")
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", alpha=0.25)

    axes[0].set_ylabel("Success rate")
    axes[0].set_ylim(-0.03, 1.08)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, 1.04),
    )
    fig.suptitle(
        "Difficulty scaling theo model, prompt và method",
        y=1.12,
        fontsize=14,
    )
    fig.tight_layout()
    return fig


def plot_funnel(
    funnel_table,
    stages,
    stage_labels,
    title,
    label_rotation=0,
) -> Figure:
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(16, 4.8),
        sharey=True,
    )
    x = np.arange(len(stages))

    for ax, model in zip(axes, MODEL_ORDER):
        for prompt in PROMPT_ORDER:
            values = funnel_table.loc[(model, prompt)].astype(float)
            ax.plot(
                x,
                values,
                marker="o",
                linewidth=2.3,
                label=PROMPT_LABELS[prompt],
                color="#4C78A8" if prompt == "basic" else "#E45756",
            )

            for x_pos, value in zip(x, values):
                if np.isfinite(value):
                    ax.annotate(
                        f"{value:.0%}",
                        (x_pos, value),
                        xytext=(0, 5),
                        textcoords="offset points",
                        ha="center",
                        fontsize=8,
                    )

        ax.set_title(MODEL_LABELS[model])
        ax.set_xticks(x)
        ax.set_xticklabels(
            stage_labels,
            rotation=label_rotation,
        )
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", alpha=0.25)

    axes[0].set_ylabel("Tỷ lệ vượt stage")
    axes[0].set_ylim(-0.03, 1.08)
    axes[-1].legend(title="Prompt", loc="lower left")
    fig.suptitle(title, y=1.02, fontsize=14)
    fig.tight_layout()
    return fig


def plot_error_stacked(
    error_share,
    title="Phân bố lỗi faceted theo model",
) -> Figure:
    error_colors = plt.cm.tab20(
        np.linspace(0, 1, max(1, len(error_share.columns)))
    )
    fig, axes = plt.subplots(
        1,
        3,
        figsize=(18, 6),
        sharex=True,
    )
    row_order = pd.MultiIndex.from_product(
        [PROMPT_ORDER, METHOD_ORDER],
        names=["prompt_variant", "method"],
    )

    for ax, model in zip(axes, MODEL_ORDER):
        panel = error_share.xs(model, level="model").reindex(row_order)
        labels = [
            f"{PROMPT_LABELS[prompt]} | {METHOD_LABELS[method]}"
            for prompt, method in panel.index
        ]
        left = np.zeros(len(panel))

        for error_name, color in zip(panel.columns, error_colors):
            values = panel[error_name].to_numpy(dtype=float)
            ax.barh(
                labels,
                values,
                left=left,
                label=error_name,
                color=color,
            )
            left += values

        ax.set_title(MODEL_LABELS[model])
        ax.set_xlabel("Tỷ lệ trên toàn bộ bài của cấu hình")
        ax.xaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="x", alpha=0.2)

    handles, labels = axes[-1].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        ncol=4,
        bbox_to_anchor=(0.5, 1.04),
    )
    fig.suptitle(title, y=1.10, fontsize=14)
    fig.tight_layout()
    return fig
