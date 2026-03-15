# hopper_export_callgraph.py — run inside Hopper's script engine
# Exports the call graph (nodes + edges) of the current document to JSON.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


Document: Any  # provided by Hopper's script engine at runtime

VERSION = "1.5.1"

CALL_TYPE_NAMES: dict[int, str] = {
    0: "none",
    1: "unknown",
    2: "direct",
    3: "objc",
}


# ---------------------------------------------------------------------------
# Utility helpers (inlined — no external module dependencies)
# ---------------------------------------------------------------------------

def to_hex(value: object) -> str | None:
    try:
        return f"0x{int(value):x}"
    except (TypeError, ValueError):
        return None


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


def default_output_path(
    executable_path: str | None,
    suffix: str,
    fallback_name: str,
) -> Path:
    if executable_path:
        return Path(f"{executable_path}{suffix}")
    return Path.home() / fallback_name


def ensure_document_ready(document: Any) -> None:
    try:
        if document.backgroundProcessActive():
            document.waitForBackgroundProcessToEnd()
    except AttributeError:
        return


def call_type_name(value: object) -> str:
    try:
        return CALL_TYPE_NAMES.get(int(value), f"unknown-{value}")
    except (TypeError, ValueError):
        return "unknown"


def iter_document_procedures(document: Any) -> list[tuple[Any, Any]]:
    """Return (segment, procedure) pairs for all procedures in the document."""
    results: list[tuple[Any, Any]] = []
    for segment in document.getSegmentsList():
        try:
            count = int(segment.getProcedureCount())
        except Exception:
            continue
        for index in range(count):
            try:
                procedure = segment.getProcedureAtIndex(index)
            except Exception:
                continue
            if procedure is not None:
                results.append((segment, procedure))
    return results


def procedure_name(segment: Any, procedure: Any) -> str:
    """Get the name of a procedure via segment name lookup at its entry point."""
    try:
        entry = procedure.getEntryPoint()
        name = segment.getNameAtAddress(entry)
        if name:
            return str(name)
    except Exception:
        pass
    return ""


def tag_names(owner: Any) -> list[str]:
    try:
        tags = owner.getTagList()
    except Exception:
        return []
    names: list[str] = []
    for tag in tags:
        try:
            names.append(str(tag.getName()))
        except Exception:
            continue
    return names


# ---------------------------------------------------------------------------
# Callgraph collection
# ---------------------------------------------------------------------------

def collect_callgraph(document: Any) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str | None, int]] = set()
    pairs = iter_document_procedures(document)

    for seg, proc in pairs:
        entry_point = to_hex(proc.getEntryPoint())
        try:
            start = to_hex(proc.getStartingAddress())
        except Exception:
            start = entry_point
        try:
            end = to_hex(proc.getEndingAddress())
        except Exception:
            end = None
        try:
            signature = str(proc.signatureString() or "")
        except Exception:
            signature = ""
        try:
            bb_count = int(proc.getBasicBlockCount())
        except Exception:
            bb_count = 0

        nodes.append(
            {
                "id": entry_point,
                "name": procedure_name(seg, proc),
                "start": start,
                "end": end,
                "entry_point": entry_point,
                "signature": signature,
                "basic_block_count": bb_count,
                "tags": tag_names(proc),
            },
        )

    for _seg, proc in pairs:
        source = to_hex(proc.getEntryPoint())
        if not source:
            continue
        try:
            callees = proc.getAllCallees()
        except Exception:
            continue

        for call_reference in callees:
            target = to_hex(call_reference.toAddress())
            if not target:
                continue
            call_site = to_hex(call_reference.fromAddress())
            type_value = int(call_reference.type())
            edge_key = (source, target, call_site, type_value)
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            edges.append(
                {
                    "source": source,
                    "target": target,
                    "call_site": call_site,
                    "call_type": type_value,
                    "call_type_name": call_type_name(type_value),
                },
            )

    return {
        "tool": "hopper_export_callgraph.py",
        "version": VERSION,
        "nodes": nodes,
        "edges": edges,
    }


# ---------------------------------------------------------------------------
# Script entry — runs immediately inside Hopper
# ---------------------------------------------------------------------------

doc = Document.getCurrentDocument()
if doc is None:
    raise RuntimeError("No active Hopper document.")

ensure_document_ready(doc)

try:
    executable_path = doc.getExecutableFilePath()
except Exception:
    executable_path = None

result = collect_callgraph(doc)
output_path = default_output_path(
    executable_path,
    ".callgraph.json",
    "hopper_callgraph.json",
)
write_json(output_path, result)

doc.log(f"[hopper_export_callgraph] Export complete: {output_path}")
