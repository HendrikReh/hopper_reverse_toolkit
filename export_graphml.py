
from __future__ import annotations

import argparse
import json
from typing import Any
from xml.sax.saxutils import escape

from _hopper_utils import load_json, write_text


VERSION = "1.4.0"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a Hopper callgraph JSON export into GraphML.",
    )
    parser.add_argument("input_json", help="Path to *.callgraph.json")
    parser.add_argument("output_graphml", help="Destination GraphML file")
    return parser.parse_args()


def render_graphml(data: dict[str, Any]) -> str:
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    seen_nodes: set[str] = set()
    seen_edges: set[tuple[str, str]] = set()

    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">\n',
        '  <key id="name" for="node" attr.name="name" attr.type="string"/>\n',
        '  <graph id="G" edgedefault="directed">\n',
    ]

    for node in nodes:
        node_id = node.get("id") or node.get("start")
        if not node_id:
            continue
        node_text = str(node_id)
        seen_nodes.add(node_text)
        name = escape(str(node.get("name", "")))
        lines.append(
            f'    <node id="{escape(node_text)}"><data key="name">{name}</data></node>\n',
        )

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue

        source_id = str(source)
        target_id = str(target)

        if source_id not in seen_nodes:
            lines.append(f'    <node id="{escape(source_id)}"/>\n')
            seen_nodes.add(source_id)
        if target_id not in seen_nodes:
            lines.append(f'    <node id="{escape(target_id)}"/>\n')
            seen_nodes.add(target_id)

        edge_key = (source_id, target_id)
        if edge_key in seen_edges:
            continue
        seen_edges.add(edge_key)
        lines.append(
            f'    <edge source="{escape(source_id)}" target="{escape(target_id)}"/>\n',
        )

    lines.append("  </graph>\n")
    lines.append("</graphml>\n")
    return "".join(lines)


def main() -> int:
    args = parse_args()

    try:
        data = load_json(args.input_json)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Failed to load callgraph JSON: {error}") from error

    write_text(args.output_graphml, render_graphml(data))
    print("GraphML written:", args.output_graphml)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
