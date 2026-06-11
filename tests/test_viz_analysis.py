import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd


SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

import viz_analysis as viz


def make_metrics_row():
    return {
        "id": "bw_easy_001",
        "difficulty": "easy",
        "method": "llm_only",
        "parse_success": "True",
        "planner_success": "",
        "plan_valid": "False",
        "goal_achieved": "0",
        "success": "1",
        "plan_length": 2,
        "runtime": 0.1,
        "error_type": "",
        "prompt_variant": "wrong-source-label",
    }


def test_parse_bool_handles_supported_values():
    assert viz.parse_bool("True") is True
    assert viz.parse_bool("1") is True
    assert viz.parse_bool("False") is False
    assert viz.parse_bool("0") is False
    assert pd.isna(viz.parse_bool("unknown"))


def test_load_all_metrics_combines_variants_and_overrides_labels(tmp_path):
    row = make_metrics_row()

    for model, prompt_variant, relative_path in viz.RESULT_SPECS:
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame([row]).to_csv(path, index=False)

    df, inventory = viz.load_all_metrics(tmp_path)

    assert len(df) == len(viz.RESULT_SPECS)
    assert inventory["status"].eq("loaded").all()
    assert set(df["prompt_variant"].astype(str)) == set(viz.PROMPT_ORDER)
    assert list(df["model"].cat.categories) == viz.MODEL_ORDER
    assert list(df["method"].cat.categories) == viz.METHOD_ORDER
    assert df["success"].all()
    assert not df["goal_achieved"].any()


def test_plot_helpers_return_expected_figure_layouts():
    config_index = pd.MultiIndex.from_product(
        [viz.MODEL_ORDER, viz.PROMPT_ORDER],
        names=["model", "prompt_variant"],
    )
    central_table = pd.DataFrame(
        {
            "llm_only": [0.1] * len(config_index),
            "llm_planner": [0.8] * len(config_index),
        },
        index=config_index,
    )
    funnel_table = pd.DataFrame(
        {
            "parse_success": [0.9] * len(config_index),
            "plan_valid": [0.7] * len(config_index),
            "goal_achieved": [0.6] * len(config_index),
        },
        index=config_index,
    )

    heatmap = viz.plot_central_heatmap(central_table)
    funnel = viz.plot_funnel(
        funnel_table,
        stages=list(funnel_table.columns),
        stage_labels=["Parse", "Plan valid", "Goal"],
        title="Test funnel",
    )

    assert len(heatmap.axes) == 2
    assert heatmap.axes[0].get_title() == (
        "Heatmap success rate của factorial 3 yếu tố"
    )
    assert len(funnel.axes) == len(viz.MODEL_ORDER)
    assert funnel._suptitle.get_text() == "Test funnel"

    plt.close(heatmap)
    plt.close(funnel)
