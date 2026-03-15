
from __future__ import annotations

from pathlib import Path
from typing import Any

from _hopper_utils import (
    call_type_name,
    default_output_path,
    demangle_rust_symbol,
    ensure_document_ready,
    iter_document_procedures,
    tag_names,
    to_hex,
    write_json,
)


try:
    from hopper import Document  # type: ignore[import-not-found]

    HAS_HOPPER = True
except ModuleNotFoundError:
    Document = None
    HAS_HOPPER = False


VERSION = "1.5.0"
CRATE_TOKENS = ("tokio", "axum", "hyper", "serde", "tracing", "rustls", "ring")


def guess_crate(name: str) -> str:
    normalized = name.lower()
    for token in CRATE_TOKENS:
        if token in normalized:
            return token
    if "std::" in normalized:
        return "std"
    return "unknown"


def collect_analysis(document: Any) -> dict[str, Any]:
    functions: list[dict[str, Any]] = []
    calls: list[dict[str, Any]] = []
    seen_edges: set[tuple[str, str, str | None, int]] = set()
    procedures = iter_document_procedures(document)

    for procedure in procedures:
        start = procedure.getStartingAddress()
        end = procedure.getEndingAddress()
        mangled_name = procedure.getName()
        demangled_name = demangle_rust_symbol(mangled_name)
        try:
            local_variable_count = len(procedure.getLocalVariableList())
        except Exception:
            local_variable_count = 0
        functions.append(
            {
                "address": to_hex(start),
                "name_mangled": mangled_name,
                "name_demangled": demangled_name,
                "crate": guess_crate(demangled_name),
                "size": int(end - start),
                "entry_point": to_hex(procedure.getEntryPoint()),
                "signature": str(procedure.signatureString() or ""),
                "basic_block_count": int(procedure.getBasicBlockCount()),
                "local_variable_count": local_variable_count,
                "tags": tag_names(procedure),
            },
        )

    for procedure in procedures:
        source = to_hex(procedure.getEntryPoint())
        if not source:
            continue
        try:
            callees = procedure.getAllCallees()
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
            calls.append(
                {
                    "source": source,
                    "target": target,
                    "call_site": call_site,
                    "call_type": type_value,
                    "call_type_name": call_type_name(type_value),
                },
            )

    return {
        "tool": "hopper_export_rust_analysis.py",
        "version": VERSION,
        "functions": functions,
        "calls": calls,
    }


def export_analysis(document: Any | None = None) -> Path:
    if not HAS_HOPPER and document is None:
        raise RuntimeError("Hopper Python API is unavailable. Run this script inside Hopper.")

    active_document = document or Document.getCurrentDocument()
    if active_document is None:
        raise RuntimeError("No active Hopper document.")

    ensure_document_ready(active_document)
    try:
        executable_path = active_document.getExecutableFilePath()
    except Exception:
        executable_path = None

    result = collect_analysis(active_document)
    output_path = default_output_path(
        executable_path,
        ".analysis.json",
        "hopper_analysis.json",
    )
    write_json(output_path, result)
    return output_path


def main() -> int:
    try:
        output_path = export_analysis()
    except RuntimeError as error:
        print(error)
        return 1

    print("Analysis exported:", output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
