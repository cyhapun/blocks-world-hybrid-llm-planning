"""
Pipeline progress visualization for the Blocks World demo.

Renders a horizontal step indicator showing which stage of the
pipeline succeeded, failed, or was not reached.
"""

from typing import Any, Dict, List

# ── Step definitions ──────────────────────────────────────────

LLM_ONLY_STEPS = [
    {"key": "input", "label": "NL Input", "icon": "1"},
    {"key": "llm", "label": "LLM", "icon": "2"},
    {"key": "parse", "label": "Parse", "icon": "3"},
    {"key": "validate", "label": "Validate", "icon": "4"},
]

LLM_PLANNER_STEPS = [
    {"key": "input", "label": "NL Input", "icon": "1"},
    {"key": "llm", "label": "LLM", "icon": "2"},
    {"key": "json", "label": "JSON", "icon": "3"},
    {"key": "pddl", "label": "PDDL", "icon": "4"},
    {"key": "planner", "label": "Planner", "icon": "5"},
    {"key": "validate", "label": "Validate", "icon": "6"},
]


# ── Status inference ──────────────────────────────────────────

def _infer_llm_only_statuses(result: Dict[str, Any]) -> List[str]:
    """Return a list of statuses (completed | failed | pending) for each step."""
    validator = result.get("validator_result", {})
    error_type = validator.get("error_type")

    # Step 0 is always completed (we have input).
    statuses = ["completed"]

    # LLM call
    if error_type == "llm_error":
        return statuses + ["failed", "pending", "pending"]

    statuses.append("completed")

    # Parse
    if not result.get("parse_success", False):
        return statuses + ["failed", "pending"]

    statuses.append("completed")

    # Validate
    is_valid = bool(validator.get("valid") and validator.get("goal_achieved"))
    statuses.append("completed" if is_valid else "failed")

    return statuses


def _infer_llm_planner_statuses(result: Dict[str, Any]) -> List[str]:
    """Return statuses for each LLM + planner pipeline step."""
    validator = result.get("validator_result", {})
    error_type = validator.get("error_type")

    statuses = ["completed"]

    # LLM
    if error_type == "llm_error":
        return statuses + ["failed", "pending", "pending", "pending", "pending"]

    statuses.append("completed")

    # JSON parse
    if error_type == "json_parse_error":
        return statuses + ["failed", "pending", "pending", "pending"]

    statuses.append("completed")

    # PDDL generation
    if error_type == "pddl_generation_error":
        return statuses + ["failed", "pending", "pending"]

    statuses.append("completed")

    # Planner
    if error_type in ("planner_error", "planner_no_solution_file", "plan_parse_error"):
        return statuses + ["failed", "pending"]

    statuses.append("completed")

    # Validate
    is_valid = bool(validator.get("valid") and validator.get("goal_achieved"))
    statuses.append("completed" if is_valid else "failed")

    return statuses


# ── HTML rendering ────────────────────────────────────────────

_STATUS_STYLES = {
    "completed": {
        "bg": "rgba(0,212,170,0.12)",
        "border": "#00D4AA",
        "color": "#00D4AA",
        "label_color": "#00D4AA",
    },
    "failed": {
        "bg": "rgba(255,107,107,0.12)",
        "border": "#FF6B6B",
        "color": "#FF6B6B",
        "label_color": "#FF6B6B",
    },
    "active": {
        "bg": "rgba(108,99,255,0.15)",
        "border": "#6C63FF",
        "color": "#6C63FF",
        "label_color": "#6C63FF",
    },
    "pending": {
        "bg": "#262B3D",
        "border": "rgba(255,255,255,0.06)",
        "color": "#5A6178",
        "label_color": "#5A6178",
    },
}


def _step_html(step: Dict, status: str) -> str:
    s = _STATUS_STYLES.get(status, _STATUS_STYLES["pending"])

    return (
        '<div style="display:flex;flex-direction:column;align-items:center;'
        'gap:0.35rem;min-width:60px;">'
        # Icon circle
        f'<div style="'
        f"width:34px;height:34px;border-radius:50%;"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-size:0.85rem;"
        f"background:{s['bg']};"
        f"border:2px solid {s['border']};"
        f"color:{s['color']};"
        f'">{step["icon"]}</div>'
        # Label
        f'<div style="'
        f"font-family:'Inter',sans-serif;font-size:0.6rem;"
        f"font-weight:500;color:{s['label_color']};"
        f"text-align:center;line-height:1.2;"
        f'">{step["label"]}</div>'
        "</div>"
    )


def _arrow_html(left_status: str, right_status: str) -> str:
    if left_status == "completed" and right_status in ("completed", "failed"):
        bg = "linear-gradient(90deg,#00D4AA,#00D4AA)"
    elif left_status == "completed" and right_status == "active":
        bg = "linear-gradient(90deg,#00D4AA,#6C63FF)"
    else:
        bg = "rgba(255,255,255,0.06)"

    return (
        f'<div style="'
        f"width:28px;height:2px;"
        f"background:{bg};"
        f"margin:0 2px;"
        f"margin-bottom:18px;"
        f"flex-shrink:0;"
        f'"></div>'
    )


def render_pipeline_html(
    steps: List[Dict],
    statuses: List[str],
) -> str:
    """Render a horizontal pipeline progress bar as HTML."""
    parts: List[str] = []

    for i, (step, status) in enumerate(zip(steps, statuses)):
        parts.append(_step_html(step, status))

        if i < len(steps) - 1:
            next_status = statuses[i + 1] if i + 1 < len(statuses) else "pending"
            parts.append(_arrow_html(status, next_status))

    inner = "\n".join(parts)

    return (
        '<div style="'
        "display:flex;align-items:center;justify-content:center;"
        "gap:0;padding:1rem 0.75rem;"
        "margin:0.75rem 0;"
        "background:#1A1D29;"
        "border:1px solid rgba(255,255,255,0.06);"
        "border-radius:12px;"
        "overflow-x:auto;"
        f'">{inner}</div>'
    )


# ── Public API ────────────────────────────────────────────────

def pipeline_html_for_result(result: Dict[str, Any]) -> str:
    """Return pipeline progress HTML for a finished result dict."""
    method = result.get("method", "")

    if method == "llm_only":
        steps = LLM_ONLY_STEPS
        statuses = _infer_llm_only_statuses(result)
    else:
        steps = LLM_PLANNER_STEPS
        statuses = _infer_llm_planner_statuses(result)

    return render_pipeline_html(steps, statuses)
