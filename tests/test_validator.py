import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from src.validate_plan import validate_plan


def base_problem():
    return {
        "objects": ["A", "B"],
        "initial_state": [
            ["on_table", "A"],
            ["on_table", "B"],
            ["clear", "A"],
            ["clear", "B"],
            ["handempty"],
        ],
        "goal": [
            ["on", "A", "B"],
        ],
    }


def test_valid_plan():
    problem = base_problem()

    actions = [
        ["pick-up", "A"],
        ["stack", "A", "B"],
    ]

    result = validate_plan(
        initial_state=problem["initial_state"],
        goal=problem["goal"],
        actions=actions,
        objects=problem["objects"],
    )

    assert result["valid"] is True
    assert result["goal_achieved"] is True
    assert result["failed_step"] is None
    assert result["error_type"] is None


def test_unknown_action():
    problem = base_problem()

    actions = [
        ["fly", "A"],
    ]

    result = validate_plan(
        initial_state=problem["initial_state"],
        goal=problem["goal"],
        actions=actions,
        objects=problem["objects"],
    )

    assert result["valid"] is False
    assert result["goal_achieved"] is False
    assert result["failed_step"] == 1
    assert result["error_type"] == "unknown_action"
    assert "Unknown action" in result["reason"]


def test_precondition_violation():
    objects = ["A", "B"]

    initial_state = [
        ["on_table", "A"],
        ["on", "B", "A"],
        ["clear", "B"],
        ["handempty"],
    ]

    goal = [
        ["on", "A", "B"],
    ]

    actions = [
        ["pick-up", "A"],
    ]

    result = validate_plan(
        initial_state=initial_state,
        goal=goal,
        actions=actions,
        objects=objects,
    )

    assert result["valid"] is False
    assert result["goal_achieved"] is False
    assert result["failed_step"] == 1
    assert result["error_type"] == "precondition_violation"
    assert "not clear" in result["reason"]


def test_plan_executes_but_goal_not_achieved():
    problem = base_problem()

    actions = [
        ["pick-up", "A"],
        ["put-down", "A"],
    ]

    result = validate_plan(
        initial_state=problem["initial_state"],
        goal=problem["goal"],
        actions=actions,
        objects=problem["objects"],
    )

    assert result["valid"] is False
    assert result["goal_achieved"] is False
    assert result["failed_step"] is None
    assert result["error_type"] == "goal_not_achieved"
    assert "goal was not achieved" in result["reason"]


def test_unknown_object():
    problem = base_problem()

    actions = [
        ["pick-up", "C"],
    ]

    result = validate_plan(
        initial_state=problem["initial_state"],
        goal=problem["goal"],
        actions=actions,
        objects=problem["objects"],
    )

    assert result["valid"] is False
    assert result["goal_achieved"] is False
    assert result["failed_step"] == 1
    assert result["error_type"] == "unknown_object"
    assert "does not exist" in result["reason"]