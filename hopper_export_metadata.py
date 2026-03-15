
from __future__ import annotations

from pathlib import Path
from typing import Any

from _hopper_utils import (
    default_output_path,
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


def safe_name(value: object, fallback: str = "") -> str:
    try:
        return fallback if value is None else str(value)
    except Exception:
        return fallback

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
        for procedure in iter_document_procedures(document):
            basic_blocks = basic_block_details(procedure)
            local_variables = local_variable_details(procedure)
            procedure_info = {
                "name": safe_name(procedure.getName(), ""),
                "entry_point": to_hex(procedure.getEntryPoint()),
                "start": to_hex(procedure.getStartingAddress()),
                "end": to_hex(procedure.getEndingAddress()),
                "signature": safe_name(procedure.signatureString(), ""),
                "heap_size": int(procedure.getHeapSize()),
                "local_variables": local_variables,
                "tags": tag_names(procedure),
                "basic_block_count": len(basic_blocks),
                "basic_blocks": basic_blocks,
            }
            try:
                pseudocode = procedure.decompile()
            except Exception:
                pseudocode = None
            if pseudocode:
                procedure_info["pseudocode"] = safe_name(pseudocode, "")
            result["procedures"].append(procedure_info)
    except Exception as error:
        warnings.append(f"Procedure parsing failed: {error}")

    result["entry_points"] = [
        result["document"]["entry_point"],
    ] if result["document"].get("entry_point") else []

    if warnings:
        result["warnings"] = warnings
    return result


def export_hopper_metadata(document: Any | None = None) -> tuple[Path, dict[str, Any]]:
    if not HAS_HOPPER and document is None:
        raise RuntimeError("Hopper Python API is unavailable. Run this script inside Hopper.")

    active_document = document or Document.getCurrentDocument()
    if active_document is None:
        raise RuntimeError("No active Hopper document.")

    ensure_document_ready(active_document)
    result = collect_metadata(active_document)
    output_path = default_output_path(
        result["document"].get("file_path"),
        ".hopper_export.json",
        "hopper_export.json",
    )
    write_json(output_path, result)
    return output_path, result


def main() -> int:
    try:
        output_path, result = export_hopper_metadata()
    except RuntimeError as error:
        print(error)
        return 1

    print("Export complete:", output_path)
    if result.get("warnings"):
        print(f"Warnings: {len(result['warnings'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
