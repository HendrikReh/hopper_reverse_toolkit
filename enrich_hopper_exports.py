
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from typing import Any, Callable

from _hopper_utils import demangle_rust_symbol, guess_subsystem, load_json, write_json, write_text


VERSION = "1.5.2"
INTERESTING_TOKENS = (
    "auth",
    "token",
    "login",
    "verify",
    "router",
    "handler",
    "service",
    "query",
    "request",
    "response",
)
MAX_NEIGHBORS = 25
TOP_FUNCTIONS = 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Merge Hopper metadata and callgraph exports into enriched JSON.",
    )
    parser.add_argument("metadata_json", help="Path to *.hopper_export.json")
    parser.add_argument("callgraph_json", help="Path to *.callgraph.json")
    parser.add_argument("--out-json", default="enriched_analysis.json")
    parser.add_argument("--out-md", default="architecture_summary.md")
    return parser.parse_args()


def normalize(
    metadata: dict[str, Any],
    callgraph: dict[str, Any],
    demangle_fn: Callable[[str], str] = demangle_rust_symbol,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    procedures = metadata.get("procedures", [])
    nodes = callgraph.get("nodes", [])
    edges = callgraph.get("edges", [])

    name_by_addr: dict[str, str] = {}
    procedure_by_addr: dict[str, dict[str, Any]] = {}
    for procedure in procedures:
        address = procedure.get("start") or procedure.get("entry_point")
        if address:
            address_text = str(address)
            name_by_addr[address_text] = str(procedure.get("name", ""))
            procedure_by_addr[address_text] = procedure

    graph_nodes: dict[str, str] = {}
    node_by_addr: dict[str, dict[str, Any]] = {}
    for node in nodes:
        address = node.get("id") or node.get("start")
        if address:
            address_text = str(address)
            graph_nodes[address_text] = str(node.get("name", "")) or name_by_addr.get(
                address_text,
                "",
            )
            node_by_addr[address_text] = node

    for address, name in name_by_addr.items():
        graph_nodes.setdefault(address, name)

    out_degree: Counter[str] = Counter()
    in_degree: Counter[str] = Counter()
    neighbors_out: defaultdict[str, list[str]] = defaultdict(list)
    neighbors_in: defaultdict[str, list[str]] = defaultdict(list)
    normalized_edges: list[dict[str, Any]] = []

    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        if not source or not target:
            continue

        source_id = str(source)
        target_id = str(target)
        out_degree[source_id] += 1
        in_degree[target_id] += 1
        neighbors_out[source_id].append(target_id)
        neighbors_in[target_id].append(source_id)
        normalized_edge = {"source": source_id, "target": target_id}
        for key in ("call_site", "call_type", "call_type_name", "target_name"):
            if key in edge:
                normalized_edge[key] = edge[key]
        normalized_edges.append(normalized_edge)

    functions: list[dict[str, Any]] = []
    for address, mangled_name in sorted(graph_nodes.items()):
        demangled_name = demangle_fn(mangled_name)
        function_record = {
            "address": address,
            "name_mangled": mangled_name,
            "name_demangled": demangled_name,
            "subsystem": guess_subsystem(demangled_name),
            "in_degree": in_degree[address],
            "out_degree": out_degree[address],
            "callers": neighbors_in[address][:MAX_NEIGHBORS],
            "callees": neighbors_out[address][:MAX_NEIGHBORS],
        }
        for source in (procedure_by_addr.get(address, {}), node_by_addr.get(address, {})):
            for key in (
                "entry_point",
                "start",
                "end",
                "signature",
                "heap_size",
                "local_variables",
                "basic_block_count",
                "basic_blocks",
                "tags",
                "size",
                "crate",
                "local_variable_count",
            ):
                if key in source and key not in function_record:
                    function_record[key] = source[key]
        functions.append(
            function_record,
        )

    return functions, normalized_edges


def score_function(function: dict[str, Any]) -> float:
    score = min(function.get("in_degree", 0), 20) * 1.2
    score += min(function.get("out_degree", 0), 20) * 1.0

    subsystem = function.get("subsystem", "")
    if subsystem == "application-or-unknown":
        score += 4.0
    if subsystem in {"tls", "crypto", "database", "http-routing", "middleware"}:
        score += 3.0

    name = str(function.get("name_demangled") or "").lower()
    for token in INTERESTING_TOKENS:
        if token in name:
            score += 1.5

    return round(score, 2)


def render_summary(functions: list[dict[str, Any]], edges: list[dict[str, Any]]) -> str:
    subsystem_counts = Counter(str(function["subsystem"]) for function in functions)
    top_functions = sorted(functions, key=score_function, reverse=True)[:TOP_FUNCTIONS]

    lines = [
        "# Architecture Summary\n\n",
        f"- Functions: {len(functions)}\n",
        f"- Calls: {len(edges)}\n\n",
        "## Subsystem distribution\n\n",
    ]

    for subsystem, count in subsystem_counts.most_common():
        lines.append(f"- {subsystem}: {count}\n")

    lines.append("\n## Top interesting functions\n\n")
    for function in top_functions:
        label = function["name_demangled"] or function["name_mangled"]
        lines.append(
            f"- `{function['address']}` — **{label}** "
            f"(subsystem: {function['subsystem']}, in: {function['in_degree']}, "
            f"out: {function['out_degree']}, score: {score_function(function)})\n",
        )

    return "".join(lines)


def main() -> int:
    args = parse_args()

    try:
        metadata = load_json(args.metadata_json)
        callgraph = load_json(args.callgraph_json)
        functions, edges = normalize(metadata, callgraph)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        raise SystemExit(f"Failed to enrich Hopper exports: {error}") from error

    for function in functions:
        function["interesting_score"] = score_function(function)

    payload = {
        "tool": "enrich_hopper_exports.py",
        "version": VERSION,
        "functions": functions,
        "calls": edges,
    }
    write_json(args.out_json, payload)
    write_text(args.out_md, render_summary(functions, edges))

    print("Enriched JSON written:", args.out_json)
    print("Architecture summary written:", args.out_md)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
