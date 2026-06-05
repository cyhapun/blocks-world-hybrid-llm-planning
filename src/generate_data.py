import json
from pathlib import Path


Path("data").mkdir(exist_ok=True)


def build_state(objects, stacks):
    state = []

    for stack in stacks:
        if not stack:
            continue

        state.append(["on_table", stack[0]])

        for lower, upper in zip(stack, stack[1:]):
            state.append(["on", upper, lower])

        state.append(["clear", stack[-1]])

    state.append(["handempty"])
    return state


def describe(objects, stacks, goal):
    parts = []

    table_blocks = [stack[0] for stack in stacks if stack]
    parts.append(f"Initially, {', '.join(table_blocks)} are on the table.")

    on_relations = []
    for stack in stacks:
        for lower, upper in zip(stack, stack[1:]):
            on_relations.append(f"{upper} is on {lower}")

    if on_relations:
        parts.append(", ".join(on_relations) + ".")

    clear_blocks = [stack[-1] for stack in stacks if stack]
    parts.append(f"{', '.join(clear_blocks)} are clear.")
    parts.append("The hand is empty.")

    goal_parts = []
    for atom in goal:
        if atom[0] == "on":
            goal_parts.append(f"put {atom[1]} on {atom[2]}")
        elif atom[0] == "on_table":
            goal_parts.append(f"put {atom[1]} on the table")
        elif atom[0] == "clear":
            goal_parts.append(f"make {atom[1]} clear")

    parts.append("The goal is to " + " and ".join(goal_parts) + ".")
    return " ".join(parts)


def make_record(record_id, difficulty, objects, stacks, goal):
    return {
        "id": record_id,
        "difficulty": difficulty,
        "objects": objects,
        "initial_state": build_state(objects, stacks),
        "goal": goal,
        "natural_language": describe(objects, stacks, goal),
    }


easy_specs = [
    ([["A"], ["B"], ["C"]], [["on", "A", "B"]]),
    ([["A", "C"], ["B"]], [["on", "B", "C"]]),
    ([["A"], ["B", "C"]], [["on", "C", "A"]]),
    ([["A", "B"], ["C"]], [["on", "C", "B"]]),
    ([["A"], ["B"], ["C"]], [["on", "C", "B"]]),
    ([["A", "B", "C"]], [["on_table", "C"]]),
    ([["A", "C"], ["B"]], [["on", "A", "B"]]),
    ([["A"], ["B", "A"], ["C"]], [["on", "C", "A"]]),
    ([["C", "A"], ["B"]], [["on", "B", "A"]]),
    ([["B"], ["A", "C"]], [["on", "A", "B"]]),
]

medium_specs = [
    ([["A"], ["B"], ["C"], ["D"]], [["on", "A", "B"], ["on", "C", "D"]]),
    ([["A", "B"], ["C"], ["D"]], [["on", "D", "B"]]),
    ([["A", "C"], ["B", "D"]], [["on", "C", "D"]]),
    ([["A", "B", "C"], ["D"]], [["on", "D", "C"]]),
    ([["A"], ["B", "C", "D"]], [["on", "A", "D"]]),
    ([["A", "D"], ["B"], ["C"]], [["on", "C", "D"], ["on", "B", "A"]]),
    ([["A", "B"], ["C", "D"]], [["on", "D", "B"]]),
    ([["A"], ["B", "A"], ["C"], ["D"]], [["on", "D", "A"]]),
    ([["D", "C"], ["A", "B"]], [["on", "B", "C"]]),
    ([["A", "B", "D"], ["C"]], [["on", "C", "D"]]),
    ([["B"], ["C", "A"], ["D"]], [["on", "B", "A"]]),
    ([["A", "C"], ["D", "B"]], [["on", "A", "B"]]),
    ([["C"], ["A", "D"], ["B"]], [["on", "C", "D"]]),
    ([["D", "A", "B"], ["C"]], [["on", "C", "B"]]),
    ([["A"], ["B"], ["C", "D"]], [["on", "A", "D"], ["on", "B", "A"]]),
]

hard_specs = [
    (["A", "B", "C", "D", "E"], [["A"], ["B"], ["C"], ["D"], ["E"]], [["on", "A", "B"], ["on", "B", "C"], ["on", "C", "D"]]),
    (["A", "B", "C", "D", "E"], [["A", "B"], ["C", "D"], ["E"]], [["on", "E", "B"], ["on", "D", "A"]]),
    (["A", "B", "C", "D", "E"], [["A", "C", "E"], ["B"], ["D"]], [["on", "B", "E"], ["on", "D", "B"]]),
    (["A", "B", "C", "D", "E"], [["D", "A"], ["B", "C"], ["E"]], [["on", "E", "A"], ["on", "C", "D"]]),
    (["A", "B", "C", "D", "E"], [["A", "B", "C"], ["D", "E"]], [["on", "E", "C"], ["on_table", "B"]]),
    (["A", "B", "C", "D", "E"], [["E", "D", "C"], ["A"], ["B"]], [["on", "A", "C"], ["on", "B", "A"]]),
    (["A", "B", "C", "D", "E"], [["B", "A"], ["C"], ["D", "E"]], [["on", "C", "A"], ["on", "E", "C"]]),
    (["A", "B", "C", "D", "E"], [["C", "B"], ["A", "D"], ["E"]], [["on", "E", "D"], ["on", "B", "A"]]),
    (["A", "B", "C", "D", "E", "F"], [["A"], ["B"], ["C"], ["D"], ["E"], ["F"]], [["on", "A", "B"], ["on", "B", "C"], ["on", "D", "E"]]),
    (["A", "B", "C", "D", "E", "F"], [["A", "B"], ["C", "D"], ["E", "F"]], [["on", "F", "B"], ["on", "D", "A"]]),
    (["A", "B", "C", "D", "E", "F"], [["A", "C", "E"], ["B", "D"], ["F"]], [["on", "F", "E"], ["on", "D", "C"]]),
    (["A", "B", "C", "D", "E", "F"], [["F", "E", "D"], ["A", "B"], ["C"]], [["on", "C", "D"], ["on", "B", "E"]]),
    (["A", "B", "C", "D", "E", "F"], [["A", "D"], ["B", "E"], ["C", "F"]], [["on", "F", "D"], ["on", "E", "A"]]),
    (["A", "B", "C", "D", "E", "F"], [["C", "A", "B"], ["D"], ["E", "F"]], [["on", "D", "B"], ["on", "F", "A"]]),
    (["A", "B", "C", "D", "E", "F"], [["B", "C"], ["D", "A"], ["E"], ["F"]], [["on", "E", "C"], ["on", "F", "E"], ["on", "A", "B"]]),
]


def write_jsonl(path, records):
    with Path(path).open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


easy_records = [
    make_record(f"bw_easy_{i:03d}", "easy", ["A", "B", "C"], stacks, goal)
    for i, (stacks, goal) in enumerate(easy_specs, start=1)
]

medium_records = [
    make_record(f"bw_medium_{i:03d}", "medium", ["A", "B", "C", "D"], stacks, goal)
    for i, (stacks, goal) in enumerate(medium_specs, start=1)
]

hard_records = [
    make_record(f"bw_hard_{i:03d}", "hard", objects, stacks, goal)
    for i, (objects, stacks, goal) in enumerate(hard_specs, start=1)
]

write_jsonl("data/blocks_world_easy.jsonl", easy_records)
write_jsonl("data/blocks_world_medium.jsonl", medium_records)
write_jsonl("data/blocks_world_hard.jsonl", hard_records)

print("Generated:")
print("data/blocks_world_easy.jsonl")
print("data/blocks_world_medium.jsonl")
print("data/blocks_world_hard.jsonl")