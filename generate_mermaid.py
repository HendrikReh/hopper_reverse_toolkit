
from __future__ import annotations

import argparse
import json
from collections import Counter
from typing import Any

from _hopper_utils import load_json, sanitize_id, sanitize_label, write_text


VERSION = "1.4.0"


def label_for(function: dict[str, Any]) -> str:
    return str(
        function.get("name_demangled")
        or function.get("name_mangled")
        or function.get("address")
        or "unknown",
    )


def render_subsystem_diagram(
    functions: list[dict[str, Any]],
    top_n: int = 12,
) -> str:
    counts = Counter(str(function.get("subsystem", "unknown")) for function in functions)
    lines = ["flowchart TD\n", "    A[Binary] --> B[Function Clusters]\n"]
    for subsystem, count in counts.most_common(top_n):
        lines.append(f"    B --> {sanitize_id(subsystem)}[{subsystem} ({count})]\n")
    return "".join(lines)


def render_hotspot_diagram(
    functions: list[dict[str, Any]],
    top_n: int = 15,
) -> str:
    ranked = sorted(
        functions,
        key=lambda function: function.get("interesting_score", 0),
        reverse=True,
    )[:top_n]
    lines = ["flowchart TD\n", "    Root[Interesting Functions]\n"]
    for function in ranked:
        label = sanitize_label(label_for(function))
        lines.append(
            f'    Root --> {sanitize_id(function.get("address"))}["{label}\\n'
            f'score={function.get("interesting_score", 0)}"]\n',
        )
    return "".join(lines)


def render_callflow_diagram(
    functions: list[dict[str, Any]],
    top_n: int = 10,
) -> str:
    ranked = sorted(
        functions,
        key=lambda function: function.get("in_degree", 0) + function.get("out_degree", 0),
        reverse=True,
    )[:top_n]
    selected = {str(function.get("address")): function for function in ranked if function.get("address")}
    seen_edges: set[tuple[str, str]] = set()

    lines = ["flowchart LR\n"]
    for function in ranked:
        lines.append(
            f'    {sanitize_id(function.get("address"))}["{sanitize_label(label_for(function))}"]\n',
        )

    for function in ranked:
        source = str(function.get("address"))
        for callee in function.get("callees", [])[:8]:
            target = str(callee)
            edge_key = (source, target)
            if target not in selected or edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            lines.append(f"    {sanitize_id(source)} --> {sanitize_id(target)}\n")

    return "".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Mermaid diagrams from enriched Hopper analysis JSON.",
    )
    parser.add_argument("enriched_json", help="Path to enriched_analysis.json")
    parser.add_argument("--subsystems", default="subsystems.mmd")
    parser.add_argument("--hotspots", default="hotspots.mmd")
    parser.add_argument("--callflow", default="callflow.mmd")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        data = load_json(args.enriched_json)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Failed to load enriched Hopper JSON: {error}") from error

    functions = data.get("functions", [])
    write_text(args.subsystems, render_subsystem_diagram(functions))
    write_text(args.hotspots, render_hotspot_diagram(functions))
    write_text(args.callflow, render_callflow_diagram(functions))

    print("Mermaid written:", args.subsystems)
    print("Mermaid written:", args.hotspots)
    print("Mermaid written:", args.callflow)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
