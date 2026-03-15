
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


def derive_subsystem_edges(functions: list[dict[str, Any]]) -> Counter[tuple[str, str]]:
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
            if not target or source == target:
                continue
            edge_weights[(source, target)] += 1
    return edge_weights


def top_functions_for_group(
    functions: list[dict[str, Any]],
    count: int = 3,
) -> list[dict[str, Any]]:
    ranked = sorted(
        functions,
        key=lambda function: (
            function.get("interesting_score", 0),
            function.get("in_degree", 0) + function.get("out_degree", 0),
        ),
        reverse=True,
    )
    return ranked[:count]


def render_architecture(
    functions: list[dict[str, Any]],
    max_groups: int = 8,
    max_edges: int = 16,
) -> str:
    groups = group_functions(functions)
    ranked_groups = sorted(groups.items(), key=lambda item: len(item[1]), reverse=True)[:max_groups]
    selected_group_names = {name for name, _ in ranked_groups}
    ranked_edges = [
        (source, target, weight)
        for (source, target), weight in derive_subsystem_edges(functions).most_common()
        if source in selected_group_names and target in selected_group_names
    ][:max_edges]

    lines = [
        "flowchart TD\n",
        "    Binary[Compiled Binary] --> Runtime[Recovered Runtime Architecture]\n",
    ]

    for group_name, members in ranked_groups:
        group_id = sanitize_id(group_name)
        lines.append(f"    Runtime --> {group_id}[{group_name}\\nfunctions={len(members)}]\n")

    lines.append("\n")
    for group_name, members in ranked_groups:
        group_id = sanitize_id(group_name)
        lines.append(f"    subgraph {group_id}_detail [{group_name}]\n")
        for index, function in enumerate(top_functions_for_group(members, count=3), start=1):
            function_id = sanitize_id(f"{group_id}_{index}_{function.get('address')}")
            label = short_label(
                function.get("name_demangled")
                or function.get("name_mangled")
                or function.get("address"),
                limit=42,
            )
            score = function.get("interesting_score", 0)
            lines.append(f'        {function_id}["{label}\\nscore={score}"]\n')
        lines.append("    end\n")

    lines.append("\n")
    for source, target, weight in ranked_edges:
        lines.append(f"    {sanitize_id(source)} -->|calls={weight}| {sanitize_id(target)}\n")

    return "".join(lines)


def synthesize(
    enriched_json_path: str,
    out_path: str,
    max_groups: int = 8,
    max_edges: int = 16,
) -> str:
    data = load_json(enriched_json_path)
    functions = data.get("functions", [])
    rendered = render_architecture(functions, max_groups=max_groups, max_edges=max_edges)
    write_text(out_path, rendered)
    return rendered


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synthesize a high-level Mermaid architecture diagram from enriched Hopper JSON.",
    )
    parser.add_argument("enriched_json")
    parser.add_argument("--out", default="architecture_synthesized.mmd")
    parser.add_argument("--max-groups", type=int, default=8)
    parser.add_argument("--max-edges", type=int, default=16)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        synthesize(
            args.enriched_json,
            args.out,
            max_groups=args.max_groups,
            max_edges=args.max_edges,
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Failed to synthesize architecture Mermaid: {error}") from error

    print("Architecture Mermaid written:", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
