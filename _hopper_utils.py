from __future__ import annotations

import json
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Any


SUBSYSTEM_TOKENS: tuple[tuple[str, str], ...] = (
    ("tokio", "async-runtime"),
    ("axum", "http-routing"),
    ("hyper", "http-core"),
    ("serde", "serialization"),
    ("tracing", "observability"),
    ("rustls", "tls"),
    ("ring", "crypto"),
    ("sqlx", "database"),
    ("reqwest", "http-client"),
    ("tower", "middleware"),
    ("std::", "std"),
)
CALL_TYPE_NAMES: dict[int, str] = {
    0: "none",
    1: "unknown",
    2: "direct",
    3: "objc",
}


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path: str | Path, payload: Any) -> None:
    Path(path).write_text(f"{json.dumps(payload, indent=2)}\n", encoding="utf-8")


def write_text(path: str | Path, content: str) -> None:
    Path(path).write_text(content, encoding="utf-8")


@lru_cache(maxsize=4096)
def demangle_rust_symbol(name: str) -> str:
    if not name:
        return ""

    if shutil.which("rustfilt") is None:
        return name

    try:
        completed = subprocess.run(
            ["rustfilt", name],
            capture_output=True,
            check=False,
            text=True,
        )
    except OSError:
        return name

    if completed.returncode != 0:
        return name

    return completed.stdout.strip() or name


def guess_subsystem(name: str) -> str:
    normalized = name.lower()
    for token, subsystem in SUBSYSTEM_TOKENS:
        if token in normalized:
            return subsystem
    return "application-or-unknown"


def sanitize_id(value: object) -> str:
    text = str(value)
    return "".join(character if character.isalnum() else "_" for character in text)


def sanitize_label(value: object) -> str:
    return str(value or "unknown").replace('"', "'")


def short_label(value: object, limit: int = 36) -> str:
    text = sanitize_label(value)
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3]}..."


def default_output_path(
    executable_path: str | None,
    suffix: str,
    fallback_name: str,
) -> Path:
    if executable_path:
        return Path(f"{executable_path}{suffix}")
    return Path.home() / fallback_name


def to_hex(value: object) -> str | None:
    try:
        return f"0x{int(value):x}"
    except (TypeError, ValueError):
        return None


def parse_address(value: object) -> int:
    if isinstance(value, int):
        return value

    text = str(value).strip().lower()
    if text.startswith("0x"):
        return int(text, 16)
    return int(text, 10)


def parse_color(value: object) -> int:
    if isinstance(value, int):
        return value

    text = str(value).strip().lower()
    if text.startswith("#"):
        text = text[1:]
    if text.startswith("0x"):
        text = text[2:]
    return int(text, 16)


def call_type_name(value: object) -> str:
    try:
        return CALL_TYPE_NAMES.get(int(value), f"unknown-{value}")
    except (TypeError, ValueError):
        return "unknown"


def ensure_document_ready(document: Any) -> None:
    try:
        if document.backgroundProcessActive():
            document.waitForBackgroundProcessToEnd()
    except AttributeError:
        return


def iter_document_procedures(document: Any) -> list[Any]:
    procedures: list[Any] = []
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
                procedures.append(procedure)

    return procedures


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
