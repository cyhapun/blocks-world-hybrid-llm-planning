import argparse
import json
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple
from pathlib import Path

Atom = Tuple[str, ...]
State = Set[Atom]


ACTION_ARITY = {
    "pick-up": 1,
    "put-down": 1,
    "stack": 2,
    "unstack": 2,
}

PREDICATE_ARITY = {
    "on_table": 1,
    "on": 2,
    "clear": 1,
    "holding": 1,
    "handempty": 0,
}


def atom_to_tuple(atom: Sequence[str]) -> Atom:
    return tuple(atom)


def atom_to_list(atom: Atom) -> List[str]:
    return list(atom)


def serialize_state(state: State) -> List[List[str]]:
    return [atom_to_list(atom) for atom in sorted(state)]


def make_result(
    valid: bool,
    goal_achieved: bool,
    failed_step: Optional[int],
    error_type: Optional[str],
    reason: str,
    final_state: Optional[State] = None,
) -> Dict[str, Any]:
    result = {
        "valid": valid,
        "goal_achieved": goal_achieved,
        "failed_step": failed_step,
        "error_type": error_type,
        "reason": reason,
    }

    if final_state is not None:
        result["final_state"] = serialize_state(final_state)

    return result


def extract_objects_from_atoms(atoms: Iterable[Sequence[str]]) -> Set[str]:
    objects = set()

    for atom in atoms:
        if not atom:
            continue

        for item in atom[1:]:
            objects.add(item)

    return objects


def validate_atom_structure(
    atom: Any,
    objects: Set[str],
    context: str,
) -> Optional[str]:
    if not isinstance(atom, list) or len(atom) == 0:
        return f"Invalid atom in {context}: atom must be a non-empty list."

    predicate = atom[0]

    if not isinstance(predicate, str):
        return f"Invalid atom in {context}: predicate must be a string."

    if predicate not in PREDICATE_ARITY:
        return f"Unknown predicate '{predicate}' in {context}."

    expected_arity = PREDICATE_ARITY[predicate]
    actual_arity = len(atom) - 1

    if actual_arity != expected_arity:
        return (
            f"Predicate '{predicate}' in {context} expects {expected_arity} "
            f"argument(s), got {actual_arity}."
        )

    for obj in atom[1:]:
        if not isinstance(obj, str):
            return f"Invalid object in {context}: object names must be strings."

        if obj not in objects:
            return f"Object '{obj}' in {context} does not exist in problem objects."

    return None


def normalize_action(action: Any) -> Tuple[Optional[str], Optional[List[str]], Optional[str]]:
    """
    Supported action formats:

    1. ["pick-up", "A"]
    2. ["stack", "A", "B"]
    3. {"action": "stack", "args": ["A", "B"]}
    4. "(stack A B)"
    5. "stack A B"
    """
    if isinstance(action, dict):
        name = action.get("action") or action.get("name")
        args = action.get("args") or action.get("parameters") or []

        if not isinstance(name, str):
            return None, None, "Action object must contain string field 'action' or 'name'."

        if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
            return None, None, "Action args must be a list of strings."

        return name, args, None

    if isinstance(action, str):
        text = action.strip()

        if "(" in text and text.endswith(")") and not text.startswith("("):
            name = text[:text.index("(")].strip()
            inner = text[text.index("(") + 1:-1].strip()
            args = [arg.strip() for arg in inner.replace(",", " ").split() if arg.strip()]
            return name, args, None

        if text.startswith("(") and text.endswith(")"):
            text = text[1:-1].strip()

        text = text.replace(",", " ")
        parts = text.split()

        if not parts:
            return None, None, "Action string must not be empty."

        return parts[0], parts[1:], None

    if isinstance(action, (list, tuple)):
        if len(action) == 0:
            return None, None, "Action list must not be empty."

        name = action[0]
        args = list(action[1:])

        if not isinstance(name, str):
            return None, None, "Action name must be a string."

        if not all(isinstance(arg, str) for arg in args):
            return None, None, "Action arguments must be strings."

        return name, args, None

    return None, None, "Action must be a list, tuple, dict, or string."


def check_action_schema(
    name: str,
    args: List[str],
    objects: Set[str],
) -> Optional[str]:
    if name not in ACTION_ARITY:
        supported = ", ".join(sorted(ACTION_ARITY))
        return f"Unknown action '{name}'. Supported actions are: {supported}."

    expected_arity = ACTION_ARITY[name]
    actual_arity = len(args)

    if actual_arity != expected_arity:
        return (
            f"Action '{name}' expects {expected_arity} argument(s), "
            f"got {actual_arity}."
        )

    for obj in args:
        if obj not in objects:
            return f"Object '{obj}' does not exist in problem objects."

    return None


def check_preconditions(name: str, args: List[str], state: State) -> Optional[str]:
    if name == "pick-up":
        x = args[0]

        if ("clear", x) not in state:
            return f"Cannot pick up {x} because {x} is not clear."

        if ("on_table", x) not in state:
            return f"Cannot pick up {x} because {x} is not on the table."

        if ("handempty",) not in state:
            return f"Cannot pick up {x} because the hand is not empty."

        return None

    if name == "put-down":
        x = args[0]

        if ("holding", x) not in state:
            return f"Cannot put down {x} because {x} is not being held."

        return None

    if name == "stack":
        x, y = args

        if ("holding", x) not in state:
            return f"Cannot stack {x} on {y} because {x} is not being held."

        if ("clear", y) not in state:
            return f"Cannot stack {x} on {y} because {y} is not clear."

        return None

    if name == "unstack":
        x, y = args

        if ("on", x, y) not in state:
            return f"Cannot unstack {x} from {y} because {x} is not on {y}."

        if ("clear", x) not in state:
            return f"Cannot unstack {x} from {y} because {x} is not clear."

        if ("handempty",) not in state:
            return f"Cannot unstack {x} from {y} because the hand is not empty."

        return None

    return f"Unknown action '{name}'."


def apply_effects(name: str, args: List[str], state: State) -> State:
    new_state = set(state)

    if name == "pick-up":
        x = args[0]

        new_state.add(("holding", x))
        new_state.discard(("clear", x))
        new_state.discard(("on_table", x))
        new_state.discard(("handempty",))

    elif name == "put-down":
        x = args[0]

        new_state.add(("on_table", x))
        new_state.add(("clear", x))
        new_state.add(("handempty",))
        new_state.discard(("holding", x))

    elif name == "stack":
        x, y = args

        new_state.add(("on", x, y))
        new_state.add(("clear", x))
        new_state.add(("handempty",))
        new_state.discard(("holding", x))
        new_state.discard(("clear", y))

    elif name == "unstack":
        x, y = args

        new_state.add(("holding", x))
        new_state.add(("clear", y))
        new_state.discard(("on", x, y))
        new_state.discard(("clear", x))
        new_state.discard(("handempty",))

    return new_state


def validate_plan(
    initial_state: List[List[str]],
    goal: List[List[str]],
    actions: List[Any],
    objects: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Validate a Blocks World plan.

    Args:
        initial_state: list of atoms, e.g. [["on_table", "A"], ["clear", "A"]]
        goal: list of goal atoms, e.g. [["on", "A", "B"]]
        actions: list of actions, e.g. [["pick-up", "A"], ["stack", "A", "B"]]
        objects: optional list of valid objects. If omitted, objects are inferred
                 from initial_state and goal.

    Returns:
        Dict with fields:
        - valid
        - goal_achieved
        - failed_step
        - error_type
        - reason
        - final_state
    """
    if objects is None:
        object_set = extract_objects_from_atoms(initial_state)
        object_set.update(extract_objects_from_atoms(goal))
    else:
        object_set = set(objects)

    for atom in initial_state:
        error = validate_atom_structure(atom, object_set, "initial_state")
        if error:
            return make_result(
                valid=False,
                goal_achieved=False,
                failed_step=None,
                error_type="invalid_problem",
                reason=error,
            )

    for atom in goal:
        error = validate_atom_structure(atom, object_set, "goal")
        if error:
            return make_result(
                valid=False,
                goal_achieved=False,
                failed_step=None,
                error_type="invalid_problem",
                reason=error,
            )

    state: State = {atom_to_tuple(atom) for atom in initial_state}

    for step_index, raw_action in enumerate(actions, start=1):
        name, args, normalize_error = normalize_action(raw_action)

        if normalize_error:
            return make_result(
                valid=False,
                goal_achieved=False,
                failed_step=step_index,
                error_type="invalid_action_format",
                reason=normalize_error,
                final_state=state,
            )

        assert name is not None
        assert args is not None

        schema_error = check_action_schema(name, args, object_set)

        if schema_error:
            error_type = "unknown_action" if name not in ACTION_ARITY else "invalid_action"

            if "does not exist" in schema_error:
                error_type = "unknown_object"

            return make_result(
                valid=False,
                goal_achieved=False,
                failed_step=step_index,
                error_type=error_type,
                reason=schema_error,
                final_state=state,
            )

        precondition_error = check_preconditions(name, args, state)

        if precondition_error:
            return make_result(
                valid=False,
                goal_achieved=False,
                failed_step=step_index,
                error_type="precondition_violation",
                reason=precondition_error,
                final_state=state,
            )

        state = apply_effects(name, args, state)

    missing_goals = []

    for atom in goal:
        atom_tuple = atom_to_tuple(atom)

        if atom_tuple not in state:
            missing_goals.append(atom)

    if missing_goals:
        return make_result(
            valid=False,
            goal_achieved=False,
            failed_step=None,
            error_type="goal_not_achieved",
            reason=f"Plan executed, but goal was not achieved. Missing goal atoms: {missing_goals}.",
            final_state=state,
        )

    return make_result(
        valid=True,
        goal_achieved=True,
        failed_step=None,
        error_type=None,
        reason="Plan is valid and goal is achieved.",
        final_state=state,
    )


def run_demo() -> None:
    objects = ["A", "B"]

    initial_state = [
        ["on_table", "A"],
        ["on_table", "B"],
        ["clear", "A"],
        ["clear", "B"],
        ["handempty"],
    ]

    goal = [
        ["on", "A", "B"],
    ]

    actions = [
        ["pick-up", "A"],
        ["stack", "A", "B"],
    ]

    result = validate_plan(
        initial_state=initial_state,
        goal=goal,
        actions=actions,
        objects=objects,
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))

def load_problem_by_id(problem_id: str, data_dir: str = "data") -> Dict[str, Any]:
    for path in Path(data_dir).glob("*.jsonl"):
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue

                record = json.loads(line)

                if record.get("id") == problem_id:
                    return record

    raise FileNotFoundError(f"Problem id '{problem_id}' not found in {data_dir}/*.jsonl")


def load_plan_actions(plan_path: str) -> List[List[str]]:
    actions = []

    with Path(plan_path).open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith(";"):
                continue

            name, args, error = normalize_action(line)

            if error:
                raise ValueError(error)

            assert name is not None
            assert args is not None

            actions.append([name] + [arg.upper() for arg in args])

    return actions


def run_problem_plan_validation(problem_id: str, plan_path: str, data_dir: str = "data") -> None:
    problem = load_problem_by_id(problem_id, data_dir=data_dir)
    actions = load_plan_actions(plan_path)

    result = validate_plan(
        initial_state=problem["initial_state"],
        goal=problem["goal"],
        actions=actions,
        objects=problem["objects"],
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--demo", action="store_true", help="Run demo validation")
    parser.add_argument("--problem-id", default=None, help="Problem id from dataset")
    parser.add_argument("--plan", default=None, help="Path to plan text file")
    parser.add_argument("--data-dir", default="data", help="Dataset directory")
    args = parser.parse_args()

    if args.demo:
        run_demo()
    elif args.problem_id and args.plan:
        run_problem_plan_validation(
            problem_id=args.problem_id,
            plan_path=args.plan,
            data_dir=args.data_dir,
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()