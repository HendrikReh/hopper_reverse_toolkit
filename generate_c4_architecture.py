
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from typing import Any

from _hopper_utils import load_json, sanitize_id, short_label, write_text


VERSION = "1.4.0"


def group_functions(functions: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    groups: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for function in functions:
        groups[str(function.get("subsystem", "application-or-unknown"))].append(function)
    return dict(groups)


def derive_edges(functions: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
    subsystem_by_address: dict[str, str] = {}
    for function in functions:
        address = function.get("address")
        if address:
            subsystem_by_address[str(address)] = str(
                function.get("subsystem", "application-or-unknown"),
            )

    edge_weights: Counter[tuple[str, str]] = Counter()
    for function in functions:
        source = str(function.get("subsystem", "application-or-unknown"))
        for callee in function.get("callees", []):
            target = subsystem_by_address.get(str(callee))
            if not target or target == source:
                continue
            edge_weights[(source, target)] += 1
    return edge_weights


def select_groups(
    groups: dict[str, list[dict[str, Any]]],
    max_groups: int = 8,
) -> list[tuple[str, list[dict[str, Any]]]]:
    return sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)[:max_groups]


def representative_functions(
    members: list[dict[str, Any]],
    count: int = 3,
) -> list[dict[str, Any]]:
    ranked = sorted(
        members,
        key=lambda function: (
            function.get("interesting_score", 0),
            function.get("in_degree", 0) + function.get("out_degree", 0),
        ),
        reverse=True,
    )
    return ranked[:count]


def selected_edges(
    functions: list[dict[str, Any]],
    max_groups: int,
    max_edges: int,
) -> list[tuple[str, str, int]]:
    groups = group_functions(functions)
    selected = select_groups(groups, max_groups=max_groups)
    selected_names = {name for name, _ in selected}
    return [
        (source, target, weight)
        for (source, target), weight in derive_edges(functions).most_common()
        if source in selected_names and target in selected_names
    ][:max_edges]


def render_mermaid(
    functions: list[dict[str, Any]],
    max_groups: int = 8,
    max_edges: int = 14,
) -> str:
    selected = select_groups(group_functions(functions), max_groups=max_groups)
    edges = selected_edges(functions, max_groups=max_groups, max_edges=max_edges)
    lines = [
        "flowchart TB\n",
        "    User[Analyst / Reverse Engineer] --> Binary[Compiled Binary]\n",
        "    Binary --> System[Recovered Runtime System]\n\n",
    ]

    for name, members in selected:
        subsystem_id = sanitize_id(name)
        lines.append(f"    System --> {subsystem_id}[{name}\\nfunctions={len(members)}]\n")

    lines.append("\n")
    for name, members in selected:
        subsystem_id = sanitize_id(name)
        lines.append(f"    subgraph {subsystem_id}_container [{name}]\n")
        for function in representative_functions(members, count=3):
            function_id = sanitize_id(f"{subsystem_id}_{function.get('address')}")
            label = short_label(
                function.get("name_demangled")
                or function.get("name_mangled")
                or function.get("address"),
            )
            lines.append(f'        {function_id}["{label}"]\n')
        lines.append("    end\n")

    lines.append("\n")
    for source, target, weight in edges:
        lines.append(f"    {sanitize_id(source)} -->|calls={weight}| {sanitize_id(target)}\n")

    return "".join(lines)


def render_plantuml(
    functions: list[dict[str, Any]],
    max_groups: int = 8,
    max_edges: int = 14,
) -> str:
    selected = select_groups(group_functions(functions), max_groups=max_groups)
    edges = selected_edges(functions, max_groups=max_groups, max_edges=max_edges)
    lines = [
        "@startuml\n",
        "title Recovered C4-Style Architecture from Binary\n",
        "skinparam componentStyle rectangle\n\n",
        'actor "Analyst / Reverse Engineer" as Analyst\n',
        'rectangle "Compiled Binary" as Binary\n',
        'rectangle "Recovered Runtime System" as System\n\n',
        "Analyst --> Binary\n",
        "Binary --> System\n\n",
    ]

    for name, members in selected:
        subsystem_id = sanitize_id(name)
        lines.append(f'package "{name}" as {subsystem_id} {{\n')
        for index, function in enumerate(representative_functions(members, count=3), start=1):
            component_id = sanitize_id(f"{subsystem_id}_{index}")
            label = short_label(
                function.get("name_demangled")
                or function.get("name_mangled")
                or function.get("address"),
            )
            lines.append(f'  component "{label}" as {component_id}\n')
        lines.append("}\n\n")

    for source, target, weight in edges:
        lines.append(f"{sanitize_id(source)} --> {sanitize_id(target)} : calls={weight}\n")

    lines.append("\n@enduml\n")
    return "".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate C4-style Mermaid and PlantUML diagrams from enriched Hopper JSON.",
    )
    parser.add_argument("enriched_json", help="Path to enriched_analysis.json")
    parser.add_argument("--mermaid-out", default="c4_architecture.mmd")
    parser.add_argument("--plantuml-out", default="c4_architecture.puml")
    parser.add_argument("--max-groups", type=int, default=8)
    parser.add_argument("--max-edges", type=int, default=14)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        data = load_json(args.enriched_json)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Failed to load enriched Hopper JSON: {error}") from error

    functions = data.get("functions", [])
    if not functions:
        raise SystemExit("No functions found in enriched JSON.")

    write_text(
        args.mermaid_out,
        render_mermaid(functions, max_groups=args.max_groups, max_edges=args.max_edges),
    )
    write_text(
        args.plantuml_out,
        render_plantuml(functions, max_groups=args.max_groups, max_edges=args.max_edges),
    )

    print("Mermaid C4 written:", args.mermaid_out)
    print("PlantUML C4 written:", args.plantuml_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
