# hopper_export_metadata.py — run inside Hopper's script engine
# Exports full document metadata (segments, symbols, procedures, CFG, pseudocode) to JSON.

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


Document: Any  # provided by Hopper's script engine at runtime

VERSION = "1.5.2"


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
    """Check that background analysis has finished.

    NOTE: waitForBackgroundProcessToEnd() dispatches to the main thread.
    If analysis is still running, log a warning instead of blocking
    (which would deadlock the Python thread against the main thread GIL).
    """
    try:
        if document.backgroundProcessActive():
            document.log(
                "[hopper_export_metadata] Warning: background analysis still active — "
                "export may be incomplete. Wait for analysis to finish, then re-run."
            )
    except AttributeError:
        return


def iter_document_procedures(document: Any) -> list[tuple[Any, Any]]:
    """Yield (segment, procedure) pairs for all procedures in the document."""
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


def safe_name(value: object, fallback: str = "") -> str:
    try:
        return fallback if value is None else str(value)
    except Exception:
        return fallback


# ---------------------------------------------------------------------------
# Metadata collection
# ---------------------------------------------------------------------------

def basic_block_details(procedure: Any) -> list[dict[str, Any]]:
    basic_blocks: list[dict[str, Any]] = []
    try:
        count = int(procedure.getBasicBlockCount())
    except Exception:
        return basic_blocks

    for index in range(count):
        try:
            basic_block = procedure.getBasicBlock(index)
        except Exception:
            continue

        successors: list[str] = []
        try:
            successor_count = int(basic_block.getSuccessorCount())
        except Exception:
            successor_count = 0

        for successor_index in range(successor_count):
            try:
                successor_address = basic_block.getSuccessorAddressAtIndex(successor_index)
            except Exception:
                continue
            successor_text = to_hex(successor_address)
            if successor_text:
                successors.append(successor_text)

        basic_blocks.append(
            {
                "start": to_hex(basic_block.getStartingAddress()),
                "end": to_hex(basic_block.getEndingAddress()),
                "successors": successors,
                "tags": tag_names(basic_block),
            },
        )

    return basic_blocks


def local_variable_details(procedure: Any) -> list[dict[str, Any]]:
    details: list[dict[str, Any]] = []
    try:
        variables = procedure.getLocalVariableList()
    except Exception:
        return details

    for variable in variables:
        try:
            details.append(
                {
                    "name": safe_name(variable.name(), ""),
                    "displacement": int(variable.displacement()),
                },
            )
        except Exception:
            continue
    return details


def collect_metadata(document: Any) -> dict[str, Any]:
    result: dict[str, Any] = {
        "tool": "hopper_export_metadata.py",
        "version": VERSION,
        "document": {},
        "segments": [],
        "symbols": [],
        "procedures": [],
        "entry_points": [],
    }
    warnings: list[str] = []

    try:
        result["document"]["name"] = safe_name(document.getDocumentName(), "")
    except Exception:
        result["document"]["name"] = ""
    try:
        result["document"]["database_path"] = safe_name(document.getDatabaseFilePath(), "")
    except Exception:
        result["document"]["database_path"] = ""
    try:
        result["document"]["file_path"] = safe_name(document.getExecutableFilePath(), "")
    except Exception:
        result["document"]["file_path"] = ""
    try:
        result["document"]["entry_point"] = to_hex(document.getEntryPoint())
    except Exception:
        result["document"]["entry_point"] = None
    try:
        result["document"]["is_64_bit"] = bool(document.is64Bits())
    except Exception:
        result["document"]["is_64_bit"] = None

    try:
        for segment in document.getSegmentsList():
            segment_info = {
                "name": safe_name(segment.getName(), ""),
                "start": to_hex(segment.getStartingAddress()),
                "length": int(segment.getLength()),
                "file_offset": int(segment.getFileOffset()),
                "sections": [],
                "procedure_count": int(segment.getProcedureCount()),
                "string_count": int(segment.getStringCount()),
            }
            try:
                section_count = int(segment.getSectionCount())
            except Exception:
                section_count = 0
            for index in range(section_count):
                try:
                    section = segment.getSection(index)
                except Exception:
                    continue
                segment_info["sections"].append(
                    {
                        "name": safe_name(section.getName(), ""),
                        "start": to_hex(section.getStartingAddress()),
                        "length": int(section.getLength()),
                        "flags": int(section.getFlags()),
                    },
                )
            result["segments"].append(segment_info)
            try:
                for address in segment.getNamedAddresses():
                    result["symbols"].append(
                        {
                            "segment": segment_info["name"],
                            "address": to_hex(address),
                            "name": safe_name(segment.getNameAtAddress(address), ""),
                        },
                    )
            except Exception:
                continue
            try:
                strings = []
                for text, address in segment.getStringsList():
                    strings.append({"address": to_hex(address), "value": safe_name(text, "")})
                if strings:
                    segment_info["strings"] = strings
            except Exception:
                continue
    except Exception as error:
        warnings.append(f"Segment parsing failed: {error}")

    try:
        for seg, proc in iter_document_procedures(document):
            try:
                entry = to_hex(proc.getEntryPoint())
            except Exception:
                entry = None
            try:
                start = to_hex(proc.getStartingAddress())
            except Exception:
                start = entry
            try:
                end = to_hex(proc.getEndingAddress())
            except Exception:
                end = None
            try:
                signature = safe_name(proc.signatureString(), "")
            except Exception:
                signature = ""
            try:
                heap_size = int(proc.getHeapSize())
            except Exception:
                heap_size = 0

            basic_blocks = basic_block_details(proc)
            local_variables = local_variable_details(proc)

            procedure_info: dict[str, Any] = {
                "name": procedure_name(seg, proc),
                "entry_point": entry,
                "start": start,
                "end": end,
                "signature": signature,
                "heap_size": heap_size,
                "local_variables": local_variables,
                "tags": tag_names(proc),
                "basic_block_count": len(basic_blocks),
                "basic_blocks": basic_blocks,
            }
            # NOTE: proc.decompile() is intentionally skipped in batch export.
            # It dispatches to the main thread via _dispatch_sync_f_slow, which
            # deadlocks when the main thread is waiting on the Python GIL.
            # Use the MCP server's decompile_procedure() for individual procedures.
            result["procedures"].append(procedure_info)
    except Exception as error:
        warnings.append(f"Procedure parsing failed: {error}")

    result["entry_points"] = [
        result["document"]["entry_point"],
    ] if result["document"].get("entry_point") else []

    if warnings:
        result["warnings"] = warnings
    return result


# ---------------------------------------------------------------------------
# Script entry — runs immediately inside Hopper
# ---------------------------------------------------------------------------

doc = Document.getCurrentDocument()
if doc is None:
    raise RuntimeError("No active Hopper document.")

ensure_document_ready(doc)
result = collect_metadata(doc)

output_path = default_output_path(
    result["document"].get("file_path"),
    ".hopper_export.json",
    "hopper_export.json",
)
write_json(output_path, result)

doc.log(f"[hopper_export_metadata] Export complete: {output_path}")
if result.get("warnings"):
    for w in result["warnings"]:
        doc.log(f"[hopper_export_metadata] Warning: {w}")
