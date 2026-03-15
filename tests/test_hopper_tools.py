from __future__ import annotations

import importlib
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parents[1]
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))


def sample_functions() -> list[dict[str, object]]:
    return [
        {
            "address": "0x10",
            "name_demangled": "app::main",
            "name_mangled": "_RNvmain",
            "subsystem": "application-or-unknown",
            "interesting_score": 7.5,
            "in_degree": 1,
            "out_degree": 2,
            "callees": ["0x20", "0x30"],
        },
        {
            "address": "0x20",
            "name_demangled": "axum::routing::Router",
            "name_mangled": "_RNvrouter",
            "subsystem": "http-routing",
            "interesting_score": 9.0,
            "in_degree": 2,
            "out_degree": 1,
            "callees": ["0x30"],
        },
        {
            "address": "0x30",
            "name_demangled": "serde_json::from_slice",
            "name_mangled": "_RNvserde",
            "subsystem": "serialization",
            "interesting_score": 6.5,
            "in_degree": 3,
            "out_degree": 0,
            "callees": [],
        },
    ]


class FakeTag:
    def __init__(self, name: str) -> None:
        self._name = name

    def getName(self) -> str:
        return self._name


class FakeLocalVariable:
    def __init__(self, name: str, displacement: int) -> None:
        self._name = name
        self._displacement = displacement

    def name(self) -> str:
        return self._name

    def displacement(self) -> int:
        return self._displacement


class FakeBasicBlock:
    def __init__(
        self,
        start: int,
        end: int,
        successors: list[int] | None = None,
        tags: list[FakeTag] | None = None,
    ) -> None:
        self._start = start
        self._end = end
        self._successors = successors or []
        self._tags = tags or []

    def getStartingAddress(self) -> int:
        return self._start

    def getEndingAddress(self) -> int:
        return self._end

    def getSuccessorCount(self) -> int:
        return len(self._successors)

    def getSuccessorAddressAtIndex(self, index: int) -> int:
        return self._successors[index]

    def getTagList(self) -> list[FakeTag]:
        return list(self._tags)


class FakeCallReference:
    def __init__(self, type_value: int, from_address: int, to_address: int) -> None:
        self._type_value = type_value
        self._from_address = from_address
        self._to_address = to_address

    def type(self) -> int:
        return self._type_value

    def fromAddress(self) -> int:
        return self._from_address

    def toAddress(self) -> int:
        return self._to_address


class FakeProcedure:
    def __init__(
        self,
        name: str,
        entry: int,
        end: int,
        *,
        signature: str = "",
        heap_size: int = 0,
        locals_: list[FakeLocalVariable] | None = None,
        tags: list[FakeTag] | None = None,
        basic_blocks: list[FakeBasicBlock] | None = None,
        callees: list[FakeCallReference] | None = None,
        callers: list[FakeCallReference] | None = None,
        pseudocode: str | None = None,
    ) -> None:
        self._name = name
        self._entry = entry
        self._end = end
        self._signature = signature
        self._heap_size = heap_size
        self._locals = locals_ or []
        self._tags = tags or []
        self._basic_blocks = basic_blocks or []
        self._callees = callees or []
        self._callers = callers or []
        self._pseudocode = pseudocode

    def getName(self) -> str:
        return self._name

    def getEntryPoint(self) -> int:
        return self._entry

    def getStartingAddress(self) -> int:
        return self._entry

    def getEndingAddress(self) -> int:
        return self._end

    def signatureString(self) -> str:
        return self._signature

    def getHeapSize(self) -> int:
        return self._heap_size

    def getLocalVariableList(self) -> list[FakeLocalVariable]:
        return list(self._locals)

    def getTagList(self) -> list[FakeTag]:
        return list(self._tags)

    def getBasicBlockCount(self) -> int:
        return len(self._basic_blocks)

    def getBasicBlock(self, index: int) -> FakeBasicBlock:
        return self._basic_blocks[index]

    def getAllCallees(self) -> list[FakeCallReference]:
        return list(self._callees)

    def getAllCallers(self) -> list[FakeCallReference]:
        return list(self._callers)

    def decompile(self) -> str | None:
        return self._pseudocode


class FakeSection:
    def __init__(self, name: str, start: int, length: int, flags: int) -> None:
        self._name = name
        self._start = start
        self._length = length
        self._flags = flags

    def getName(self) -> str:
        return self._name

    def getStartingAddress(self) -> int:
        return self._start

    def getLength(self) -> int:
        return self._length

    def getFlags(self) -> int:
        return self._flags


class FakeSegment:
    def __init__(
        self,
        name: str,
        start: int,
        length: int,
        file_offset: int,
        *,
        sections: list[FakeSection] | None = None,
        procedures: list[FakeProcedure] | None = None,
        labels: dict[int, str] | None = None,
        strings: list[tuple[int, str]] | None = None,
    ) -> None:
        self._name = name
        self._start = start
        self._length = length
        self._file_offset = file_offset
        self._sections = sections or []
        self._procedures = procedures or []
        self._labels = labels or {}
        self._strings = strings or []

    def getName(self) -> str:
        return self._name

    def getStartingAddress(self) -> int:
        return self._start

    def getLength(self) -> int:
        return self._length

    def getFileOffset(self) -> int:
        return self._file_offset

    def getSectionCount(self) -> int:
        return len(self._sections)

    def getSection(self, index: int) -> FakeSection:
        return self._sections[index]

    def getNamedAddresses(self) -> list[int]:
        return list(self._labels.keys())

    def getNameAtAddress(self, address: int) -> str | None:
        return self._labels.get(address)

    def getProcedureCount(self) -> int:
        return len(self._procedures)

    def getProcedureAtIndex(self, index: int) -> FakeProcedure:
        return self._procedures[index]

    def getStringCount(self) -> int:
        return len(self._strings)

    def getStringsList(self) -> list[tuple[str, int]]:
        return [(text, address) for address, text in self._strings]


class FakeDocument:
    def __init__(
        self,
        executable_path: str,
        *,
        entry_point: int = 0x1000,
        database_path: str = "/tmp/sample.hop",
        segments: list[FakeSegment] | None = None,
        document_name: str = "Sample",
        is_64_bit: bool = True,
        background_active: bool = False,
    ) -> None:
        self._executable_path = executable_path
        self._entry_point = entry_point
        self._database_path = database_path
        self._segments = segments or []
        self._document_name = document_name
        self._is_64_bit = is_64_bit
        self._background_active = background_active
        self.waited = False
        self.names: dict[int, str] = {}
        self.comments: dict[int, str] = {}
        self.inline_comments: dict[int, str] = {}
        self.colors: dict[int, int] = {}
        self.bookmarks: dict[int, str | None] = {}
        self.tags_by_address: dict[int, set[str]] = {}
        self.tags: dict[str, FakeTag] = {}
        self.refreshed = False

    def backgroundProcessActive(self) -> bool:
        return self._background_active

    def waitForBackgroundProcessToEnd(self) -> None:
        self.waited = True
        self._background_active = False

    def getDocumentName(self) -> str:
        return self._document_name

    def getDatabaseFilePath(self) -> str:
        return self._database_path

    def getExecutableFilePath(self) -> str:
        return self._executable_path

    def is64Bits(self) -> bool:
        return self._is_64_bit

    def getEntryPoint(self) -> int:
        return self._entry_point

    def getSegmentsList(self) -> list[FakeSegment]:
        return list(self._segments)

    def setNameAtAddress(self, address: int, name: str) -> None:
        self.names[address] = name

    def setCommentAtAddress(self, address: int, comment: str) -> None:
        self.comments[address] = comment

    def setInlineCommentAtAddress(self, address: int, comment: str) -> None:
        self.inline_comments[address] = comment

    def buildTag(self, name: str) -> FakeTag:
        tag = self.tags.setdefault(name, FakeTag(name))
        return tag

    def addTagAtAddress(self, tag: FakeTag, address: int) -> None:
        self.tags_by_address.setdefault(address, set()).add(tag.getName())

    def setColorAtAddress(self, color: int, address: int) -> None:
        self.colors[address] = color

    def setBookmarkAtAddress(self, address: int, name: str | None = None) -> None:
        self.bookmarks[address] = name

    def refreshView(self) -> None:
        self.refreshed = True


def build_fake_document(tmp_path: Path, *, background_active: bool = False) -> FakeDocument:
    tag_hot = FakeTag("hot")
    block_1 = FakeBasicBlock(0x1000, 0x1010, successors=[0x1010], tags=[tag_hot])
    block_2 = FakeBasicBlock(0x1010, 0x1020, successors=[], tags=[])
    procedure_main = FakeProcedure(
        "main",
        0x1000,
        0x1020,
        signature="fn main()",
        heap_size=32,
        locals_=[FakeLocalVariable("var_8", -8)],
        tags=[tag_hot],
        basic_blocks=[block_1, block_2],
        callees=[FakeCallReference(2, 0x1004, 0x2000)],
        callers=[],
        pseudocode="fn main() { helper(); }",
    )
    procedure_helper = FakeProcedure(
        "helper",
        0x2000,
        0x2010,
        signature="fn helper()",
        basic_blocks=[FakeBasicBlock(0x2000, 0x2010)],
        callees=[],
        callers=[FakeCallReference(2, 0x1004, 0x2000)],
        pseudocode="fn helper() {}",
    )
    text_segment = FakeSegment(
        "TEXT",
        0x1000,
        0x200,
        0,
        sections=[FakeSection("__text", 0x1000, 0x120, 0x80000000)],
        procedures=[procedure_main, procedure_helper],
        labels={0x1000: "main", 0x2000: "helper"},
        strings=[(0x3000, "token"), (0x3010, "router")],
    )
    return FakeDocument(
        str(tmp_path / "sample.bin"),
        segments=[text_segment],
        background_active=background_active,
    )


class ExportGraphMlTests(unittest.TestCase):
    def test_render_graphml_escapes_names_and_backfills_nodes(self) -> None:
        module = importlib.import_module("export_graphml")

        graphml = module.render_graphml(
            {
                "nodes": [{"id": "0x1", "name": 'alpha & "beta"'}],
                "edges": [{"source": "0x1", "target": "0x2"}],
            }
        )

        self.assertIn("alpha &amp; \"beta\"", graphml)
        self.assertIn('<node id="0x2"/>', graphml)
        self.assertIn('<edge source="0x1" target="0x2"/>', graphml)


class MermaidRendererTests(unittest.TestCase):
    def test_generate_mermaid_exposes_render_helpers(self) -> None:
        module = importlib.import_module("generate_mermaid")

        subsystem = module.render_subsystem_diagram(sample_functions(), top_n=2)
        hotspots = module.render_hotspot_diagram(sample_functions(), top_n=2)
        callflow = module.render_callflow_diagram(sample_functions(), top_n=2)

        self.assertIn("flowchart TD", subsystem)
        self.assertIn("http-routing", subsystem)
        self.assertIn("Interesting Functions", hotspots)
        self.assertIn("score=9.0", hotspots)
        self.assertIn("flowchart LR", callflow)
        self.assertIn("0x10", callflow)


class ArchitectureRendererTests(unittest.TestCase):
    def test_json_architecture_module_renders_mermaid(self) -> None:
        module = importlib.import_module("json_to_mermaid_architecture")

        mermaid = module.render_architecture(sample_functions(), max_groups=3, max_edges=4)

        self.assertIn("Recovered Runtime Architecture", mermaid)
        self.assertIn("calls=1", mermaid)
        self.assertIn("http-routing", mermaid)

    def test_c4_module_renders_mermaid_and_plantuml(self) -> None:
        module = importlib.import_module("generate_c4_architecture")

        mermaid = module.render_mermaid(sample_functions(), max_groups=3, max_edges=4)
        plantuml = module.render_plantuml(sample_functions(), max_groups=3, max_edges=4)

        self.assertIn("Recovered Runtime System", mermaid)
        self.assertIn("calls=1", mermaid)
        self.assertIn("@startuml", plantuml)
        self.assertIn("component", plantuml)


class HopperExporterTests(unittest.TestCase):
    def test_collect_metadata_exports_sections_cfg_and_locals(self) -> None:
        module = importlib.import_module("hopper_export_metadata")

        with tempfile.TemporaryDirectory() as tmpdir:
            document = build_fake_document(Path(tmpdir))
            result = module.collect_metadata(document)

        self.assertEqual(result["document"]["entry_point"], "0x1000")
        self.assertTrue(result["document"]["is_64_bit"])
        self.assertEqual(result["segments"][0]["sections"][0]["name"], "__text")
        self.assertEqual(result["segments"][0]["string_count"], 2)
        self.assertEqual(result["procedures"][0]["signature"], "fn main()")
        self.assertEqual(result["procedures"][0]["local_variables"][0]["name"], "var_8")
        self.assertEqual(result["procedures"][0]["basic_blocks"][0]["successors"], ["0x1010"])
        self.assertEqual(result["procedures"][0]["tags"], ["hot"])

    def test_export_metadata_waits_for_background_analysis(self) -> None:
        module = importlib.import_module("hopper_export_metadata")

        with tempfile.TemporaryDirectory() as tmpdir:
            document = build_fake_document(Path(tmpdir), background_active=True)
            output_path, _ = module.export_hopper_metadata(document=document)
            exported = json.loads(Path(output_path).read_text(encoding="utf-8"))

        self.assertTrue(document.waited)
        self.assertEqual(exported["document"]["entry_point"], "0x1000")

    def test_collect_callgraph_uses_call_references(self) -> None:
        module = importlib.import_module("hopper_export_callgraph")

        with tempfile.TemporaryDirectory() as tmpdir:
            document = build_fake_document(Path(tmpdir))
            result = module.collect_callgraph(document)

        self.assertEqual(result["nodes"][0]["signature"], "fn main()")
        self.assertEqual(result["edges"][0]["source"], "0x1000")
        self.assertEqual(result["edges"][0]["target"], "0x2000")
        self.assertEqual(result["edges"][0]["call_site"], "0x1004")
        self.assertEqual(result["edges"][0]["call_type"], 2)
        self.assertEqual(result["edges"][0]["call_type_name"], "direct")

    def test_collect_rust_analysis_uses_documented_traversal(self) -> None:
        module = importlib.import_module("hopper_export_rust_analysis")

        with tempfile.TemporaryDirectory() as tmpdir:
            document = build_fake_document(Path(tmpdir))
            result = module.collect_analysis(document)

        self.assertEqual(result["functions"][0]["signature"], "fn main()")
        self.assertEqual(result["functions"][0]["local_variable_count"], 1)
        self.assertEqual(result["calls"][0]["call_site"], "0x1004")
        self.assertEqual(result["calls"][0]["call_type_name"], "direct")

    def test_enrichment_preserves_exported_call_metadata(self) -> None:
        module = importlib.import_module("enrich_hopper_exports")

        functions, edges = module.normalize(
            {
                "procedures": [
                    {
                        "entry_point": "0x1000",
                        "start": "0x1000",
                        "name": "main",
                        "signature": "fn main()",
                        "basic_block_count": 2,
                    }
                ]
            },
            {
                "nodes": [{"id": "0x1000", "name": "main"}],
                "edges": [
                    {
                        "source": "0x1000",
                        "target": "0x2000",
                        "call_site": "0x1004",
                        "call_type": 2,
                        "call_type_name": "direct",
                    }
                ],
            },
            demangle_fn=lambda name: name,
        )

        self.assertEqual(functions[0]["signature"], "fn main()")
        self.assertEqual(functions[0]["basic_block_count"], 2)
        self.assertEqual(edges[0]["call_site"], "0x1004")
        self.assertEqual(edges[0]["call_type_name"], "direct")


class HopperAnnotationTests(unittest.TestCase):
    def test_annotation_import_applies_document_changes(self) -> None:
        module = importlib.import_module("hopper_apply_annotations")

        with tempfile.TemporaryDirectory() as tmpdir:
            document = build_fake_document(Path(tmpdir))
            payload = {
                "labels": [{"address": "0x1000", "name": "entry_main"}],
                "comments": [{"address": "0x1000", "comment": "entry point"}],
                "inline_comments": [{"address": "0x1004", "comment": "calls helper"}],
                "tags": [{"address": "0x1000", "tag": "review"}],
                "colors": [{"address": "0x1000", "color": "#FF112233"}],
                "bookmarks": [{"address": "0x1000", "name": "main entry"}],
            }

            summary = module.apply_annotations(document, payload)

        self.assertEqual(summary["labels"], 1)
        self.assertEqual(summary["tags"], 1)
        self.assertEqual(document.names[0x1000], "entry_main")
        self.assertEqual(document.comments[0x1000], "entry point")
        self.assertEqual(document.inline_comments[0x1004], "calls helper")
        self.assertEqual(document.colors[0x1000], 0xFF112233)
        self.assertEqual(document.bookmarks[0x1000], "main entry")
        self.assertIn("review", document.tags_by_address[0x1000])
        self.assertTrue(document.refreshed)

    def test_parse_color_accepts_hex_notation(self) -> None:
        module = importlib.import_module("hopper_apply_annotations")

        self.assertEqual(module.parse_color("#FF112233"), 0xFF112233)
        self.assertEqual(module.parse_color("0xFF112233"), 0xFF112233)
        self.assertEqual(module.parse_color(0xFF112233), 0xFF112233)


class HopperModuleImportTests(unittest.TestCase):
    def test_hopper_exports_import_without_hopper_runtime(self) -> None:
        metadata = importlib.import_module("hopper_export_metadata")
        callgraph = importlib.import_module("hopper_export_callgraph")
        analysis = importlib.import_module("hopper_export_rust_analysis")
        annotations = importlib.import_module("hopper_apply_annotations")

        self.assertFalse(metadata.HAS_HOPPER)
        self.assertFalse(callgraph.HAS_HOPPER)
        self.assertFalse(analysis.HAS_HOPPER)
        self.assertFalse(annotations.HAS_HOPPER)
        self.assertEqual(metadata.to_hex(16), "0x10")
        self.assertEqual(callgraph.to_hex(32), "0x20")
        self.assertEqual(analysis.to_hex(48), "0x30")


if __name__ == "__main__":
    unittest.main()
