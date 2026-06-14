"""
HTML / CSS block visualizer for the Blocks World demo.

Generates inline-styled HTML that renders block stacks as coloured
rectangles on a dark table surface instead of ASCII art.
"""

from typing import Any, Dict, List, Set, Tuple

Atom = Tuple[str, ...]
State = Set[Atom]

# Consistent colour palette for blocks A–Z.
BLOCK_COLORS = {
    "A": "#6C63FF",
    "B": "#00D4AA",
    "C": "#FF6B6B",
    "D": "#FFD93D",
    "E": "#45B7D1",
    "F": "#F093FB",
    "G": "#4ECDC4",
    "H": "#FF8A5C",
    "I": "#A29BFE",
    "J": "#FD79A8",
}

DEFAULT_COLOR = "#8B92A5"


def _color_for(block: str) -> str:
    return BLOCK_COLORS.get(block.upper(), DEFAULT_COLOR)


def _text_color_for(bg: str) -> str:
    """Return white or dark text depending on the brightness of *bg*."""
    hex_color = bg.lstrip("#")

    if len(hex_color) != 6:
        return "#FFFFFF"

    r, g, b = (int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    luminance = 0.299 * r + 0.587 * g + 0.114 * b

    return "#1A1D29" if luminance > 160 else "#FFFFFF"


# ── State helpers ─────────────────────────────────────────────

def state_from_atoms(atoms) -> State:
    return {tuple(a) for a in atoms}


def _build_stacks(state: State) -> Tuple[List[List[str]], str | None]:
    """Return (list-of-stacks, held_block_or_None)."""
    table_blocks = sorted(a[1] for a in state if a[0] == "on_table")

    above: Dict[str, str] = {}

    for a in state:
        if a[0] == "on":
            above[a[2]] = a[1]

    stacks: List[List[str]] = []

    for bottom in table_blocks:
        stack = [bottom]
        cur = bottom

        while cur in above:
            cur = above[cur]
            stack.append(cur)

        stacks.append(stack)

    held = None

    for a in state:
        if a[0] == "holding":
            held = a[1]

    return stacks, held


# ── HTML renderers ────────────────────────────────────────────

def _render_block_html(name: str) -> str:
    bg = _color_for(name)
    fg = _text_color_for(bg)

    return (
        f'<div style="'
        f"width:56px;height:40px;border-radius:6px;"
        f"display:flex;align-items:center;justify-content:center;"
        f"font-family:'Inter',sans-serif;font-weight:700;font-size:0.95rem;"
        f"color:{fg};background:{bg};"
        f"text-shadow:0 1px 2px rgba(0,0,0,0.25);"
        f"box-shadow:0 2px 8px rgba(0,0,0,0.25),inset 0 1px 0 rgba(255,255,255,0.15);"
        f'">{name}</div>'
    )


def _render_stack_html(stack: List[str]) -> str:
    blocks = "".join(_render_block_html(b) for b in reversed(stack))

    return (
        '<div style="display:flex;flex-direction:column;align-items:center;gap:2px;">'
        f"{blocks}"
        '<div style="'
        "width:68px;height:6px;margin-top:2px;"
        "background:linear-gradient(180deg,#3A3F4D,#2A2F3D);"
        "border-radius:3px;box-shadow:0 1px 4px rgba(0,0,0,0.3);"
        '"></div>'
        "</div>"
    )


def _render_hand_html(held: str | None) -> str:
    if held is None:
        return (
            '<div style="'
            "display:flex;align-items:center;justify-content:center;"
            "gap:0.5rem;padding:0.4rem 1rem;"
            "background:rgba(108,99,255,0.06);"
            "border:1px dashed rgba(108,99,255,0.2);"
            "border-radius:8px;margin-top:0.6rem;"
            "font-size:0.78rem;color:#8B92A5;"
            "font-family:'Inter',sans-serif;"
            '">Hand empty</div>'
        )

    bg = _color_for(held)
    fg = _text_color_for(bg)

    return (
        '<div style="'
        "display:flex;align-items:center;justify-content:center;"
        "gap:0.5rem;padding:0.4rem 1rem;"
        "background:rgba(108,99,255,0.1);"
        "border:1px dashed rgba(108,99,255,0.35);"
        "border-radius:8px;margin-top:0.6rem;"
        "font-size:0.78rem;color:#A29BFE;"
        "font-family:'Inter',sans-serif;"
        f'">Holding '
        f'<span style="'
        f"display:inline-flex;align-items:center;justify-content:center;"
        f"width:28px;height:22px;border-radius:4px;"
        f"background:{bg};color:{fg};"
        f"font-weight:700;font-size:0.75rem;"
        f'">{held}</span></div>'
    )


def render_state_html(state: State, label: str = "") -> str:
    """Render a single state as an HTML snippet."""
    stacks, held = _build_stacks(state)

    label_html = ""

    if label:
        label_html = (
            '<div style="'
            "font-family:'JetBrains Mono',monospace;font-size:0.7rem;"
            "color:#8B92A5;text-align:center;margin-bottom:0.35rem;"
            "font-weight:500;"
            f'">{label}</div>'
        )

    if not stacks and held is None:
        scene = (
            '<div style="text-align:center;padding:1rem;'
            "color:#5A6178;font-size:0.8rem;"
            "font-family:'Inter',sans-serif;"
            '">⸻ empty table ⸻</div>'
        )
    else:
        stack_divs = "".join(_render_stack_html(s) for s in stacks)
        scene = (
            '<div style="display:flex;align-items:flex-end;'
            'justify-content:center;gap:2rem;padding:1rem 0.5rem 0;">'
            f"{stack_divs}"
            "</div>"
        )

    hand_html = _render_hand_html(held)

    return (
        '<div style="'
        "background:#1A1D29;border:1px solid rgba(255,255,255,0.06);"
        "border-radius:12px;padding:1rem;margin-bottom:0.5rem;"
        f'">{label_html}{scene}{hand_html}</div>'
    )


# ── Full plan renderer ────────────────────────────────────────

def render_plan_visual(
    problem: Dict[str, Any],
    actions: List[List[str]],
) -> str:
    """
    Render the full plan as a sequence of HTML state snapshots.

    Uses ``check_preconditions`` and ``apply_effects`` from
    ``validate_plan`` to advance the state, just like the ASCII
    renderer does.
    """
    from validate_plan import apply_effects, check_preconditions

    state = state_from_atoms(problem["initial_state"])
    parts: List[str] = []

    parts.append(render_state_html(state, label="Step 0 — Initial State"))

    for idx, action in enumerate(actions, start=1):
        name = action[0]
        args = action[1:]

        action_str = f"{name}({', '.join(args)})"
        error = check_preconditions(name, args, state)

        if error:
            parts.append(
                '<div style="'
                "text-align:center;padding:0.4rem;margin:0.25rem 0;"
                "font-family:'Inter',sans-serif;font-size:0.78rem;"
                "color:#FF6B6B;"
                f'">Step {idx}: {action_str} — {error}</div>'
            )
            parts.append(render_state_html(state, label=f"Step {idx} — ERROR"))
            break

        state = apply_effects(name, args, state)

        parts.append(
            '<div style="'
            "text-align:center;padding:0.3rem;margin:0.15rem 0;"
            "font-family:'JetBrains Mono',monospace;font-size:0.72rem;"
            "color:#A29BFE;font-weight:500;"
            f'">▼ {action_str}</div>'
        )
        parts.append(render_state_html(state, label=f"Step {idx}"))

    return "\n".join(parts)
