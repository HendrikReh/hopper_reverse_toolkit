# Hopper 6.2.1 Python API Guide

**Version target:** Hopper 6.2.1
**Scope:** Public Python scripting API
**Audience:** Reverse engineers who know binary analysis but are new to Hopper scripting

This guide explains how to script Hopper 6.2.1 with Python, using the public API surface reflected in this repository. It is intentionally practical first and reference-oriented second.

If you only need working examples, start with these repository scripts:
- `hopper_export_metadata.py`
- `hopper_export_callgraph.py`
- `hopper_export_rust_analysis.py`
- `hopper_apply_annotations.py`
- `_hopper_utils.py`

## 1. Hopper's scripting model

Hopper organizes analysis around a `Document`. A document contains `Segment` objects, and each segment contains `Section` objects and typed bytes. Procedures live inside segments and are made of `BasicBlock` objects. Instructions, strings, labels, tags, comments, colors, and bookmarks are all attached to addresses inside the document.

The most important consequence is this:
- start from `Document.getCurrentDocument()`
- use document methods when you want a global view
- use segment methods when you want address-local reads, writes, types, strings, or xrefs
- use procedure and basic-block methods when you want control-flow structure

## 2. Safe script bootstrap

Inside Hopper, scripts normally import directly from `hopper`:

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

print("Loaded:", document.getDocumentName())
```

If you want the same script to fail cleanly outside Hopper, guard the import:

```python
try:
    from hopper import Document
except ModuleNotFoundError:
    Document = None


def main() -> int:
    if Document is None:
        print("Hopper Python API is unavailable. Run this script inside Hopper.")
        return 1
    ...
```

## 3. Working with the current document

The `Document` class is your entrypoint for almost everything:
- retrieve the current file and database paths
- inspect segments and procedures
- read and write bytes across mapped segments
- navigate the current cursor and selection
- create tags, colors, comments, and bookmarks

Useful starting calls:
- `Document.getCurrentDocument()`
- `document.getDocumentName()`
- `document.getExecutableFilePath()`
- `document.getDatabaseFilePath()`
- `document.getEntryPoint()`
- `document.is64Bits()`

Before exporting or mining analysis, wait for background analysis to finish:

```python
document = Document.getCurrentDocument()
if document and document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()
```

That pattern matters. Exporting too early can silently miss procedures, labels, strings, or cross-references.

## 4. Practical scripting patterns

### 4.1 Enumerate segments and sections

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

for segment in document.getSegmentsList():
    print(
        segment.getName(),
        hex(segment.getStartingAddress()),
        segment.getLength(),
    )
    for section in segment.getSectionsList():
        print(
            "  ",
            section.getName(),
            hex(section.getStartingAddress()),
            section.getLength(),
        )
```

Use this when you want:
- memory layout
- file offset mapping
- section-by-section export logic

Important segment helpers:
- `getFileOffset()`
- `getFileOffsetForAddress(addr)`
- `getSectionAtAddress(addr)`
- `getSectionIndexAtAddress(addr)`

### 4.2 Enumerate procedures safely

Prefer segment-based procedure enumeration. It stays on the documented public API:

```python
def iter_procedures(document):
    for segment in document.getSegmentsList():
        count = segment.getProcedureCount()
        for index in range(count):
            procedure = segment.getProcedureAtIndex(index)
            if procedure is not None:
                yield procedure


document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

for procedure in iter_procedures(document):
    entry = procedure.getEntryPoint()
    name = document.getNameAtAddress(entry) or hex(entry)
    print(name, procedure.signatureString())
```

This is better than relying on undocumented shortcuts from old scripts.

### 4.3 Walk basic blocks and control flow

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

entry = document.getEntryPoint()
segment = document.getSegmentAtAddress(entry)
procedure = segment.getProcedureAtAddress(entry)

for index in range(procedure.getBasicBlockCount()):
    block = procedure.getBasicBlock(index)
    print("block", hex(block.getStartingAddress()), "->", hex(block.getEndingAddress()))
    for succ_index in range(block.getSuccessorCount()):
        succ = block.getSuccessorAddressAtIndex(succ_index)
        print("  successor", hex(succ))
```

Use this when you need:
- local control-flow graphs
- branch fan-out
- basic-block tagging

### 4.4 Build a call graph

`Procedure.getAllCallees()` and `Procedure.getAllCallers()` return `CallReference` objects. Those objects preserve both the callsite and the referenced destination.

```python
def iter_procedures(document):
    for segment in document.getSegmentsList():
        count = segment.getProcedureCount()
        for index in range(count):
            procedure = segment.getProcedureAtIndex(index)
            if procedure is not None:
                yield procedure


document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

for procedure in iter_procedures(document):
    caller_entry = procedure.getEntryPoint()
    caller_name = document.getNameAtAddress(caller_entry) or hex(caller_entry)

    for call in procedure.getAllCallees():
        target = call.toAddress()
        target_name = document.getNameAtAddress(target) or hex(target)
        print(
            caller_name,
            "calls",
            target_name,
            "from",
            hex(call.fromAddress()),
            "type",
            call.type(),
        )
```

Call reference types are documented as:
- `CALL_NONE`
- `CALL_UNKNOWN`
- `CALL_DIRECT`
- `CALL_OBJC`

### 4.5 Recover names, comments, tags, colors, and bookmarks

The public API supports both annotation export and annotation write-back.

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

address = document.getEntryPoint()
segment = document.getSegmentAtAddress(address)

document.setNameAtAddress(address, "entry_main")
segment.setCommentAtAddress(address, "Recovered entry routine")
segment.setInlineCommentAtAddress(address, "Initial stack setup")

tag = document.buildTag("review")
document.addTagAtAddress(tag, address)

document.setColorAtAddress(0xFF112233, address)
document.setBookmarkAtAddress(address, "main entry")
document.refreshView()
```

Use:
- prefix comments for longer address-level notes
- inline comments for a short remark on one line
- tags for machine-processable grouping
- colors for immediate visual triage
- bookmarks for analyst waypoints

### 4.6 Read and write data

If you already know the address is inside a specific segment, use the segment APIs. If you want Hopper to resolve the containing segment for you, use the document APIs.

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

segment = document.getCurrentSegment()
address = document.getCurrentAddress()

raw_byte = segment.readByte(address)
qword = document.readUInt64LE(address)
blob = document.readBytes(address, 16)

segment.writeByte(address, 0x90)
document.writeUInt32LE(address + 4, 0x12345678)
```

Many read methods return `False` on failure. Check the result instead of assuming the access succeeded.

### 4.7 Reclassify bytes as code or data

You can script binary cleanup and recovery by changing Hopper's byte types:

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

segment = document.getCurrentSegment()
address = document.getCurrentAddress()

segment.markAsUndefined(address)
segment.markAsCode(address)
segment.markAsProcedure(address)
segment.markAsDataByteArray(address, 32)
segment.makeAlignment(address, 16)
```

Useful when dealing with:
- obfuscated binaries
- mixed code and data
- broken procedure boundaries
- ARM and Thumb mode issues

ARM helpers:
- `isThumbAtAddress(addr)`
- `setThumbModeAtAddress(addr)`
- `setARMModeAtAddress(addr)`

### 4.8 Assemble and patch instructions

`Document.assemble(instr, address, syntax)` lets you assemble bytes for an instruction before writing them back.

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

address = document.getCurrentAddress()
bytes_out = document.assemble("nop", address, 0)
if bytes_out:
    document.writeBytes(address, bytes_out)
    document.refreshView()
```

For Intel syntax:
- `syntax = 0` means Intel
- `syntax = 1` means AT&T

### 4.9 Produce a modified binary

After changing bytes, comments, labels, or analysis state, you can save the Hopper database and optionally produce a patched executable:

```python
document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

document.saveDocument()
output = document.produceNewExecutable(remove_sig=False)
print(output)
```

For Mach-O targets, `remove_sig=True` can be useful when the original signature is no longer valid.

### 4.10 Export procedure names to a text file

Write one procedure name per line to a file next to the binary.

```python
from pathlib import Path

document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

output_path = Path(document.getExecutableFilePath() + ".procedures.txt")

lines = []
for segment in document.getSegmentsList():
    for index in range(segment.getProcedureCount()):
        procedure = segment.getProcedureAtIndex(index)
        if procedure is not None:
            entry = procedure.getEntryPoint()
            name = document.getNameAtAddress(entry) or hex(entry)
            lines.append(f"{hex(entry)}  {name}")

output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
print(f"Exported {len(lines)} procedures to {output_path}")
```

### 4.11 Export strings to CSV

Collect all strings across segments and write them as CSV.

```python
import csv
import io
from pathlib import Path

document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

output_path = Path(document.getExecutableFilePath() + ".strings.csv")

buf = io.StringIO()
writer = csv.writer(buf)
writer.writerow(["segment", "address", "value"])

count = 0
for segment in document.getSegmentsList():
    seg_name = segment.getName()
    for text, address in segment.getStringsList():
        writer.writerow([seg_name, hex(address), text])
        count += 1

output_path.write_text(buf.getvalue(), encoding="utf-8")
print(f"Exported {count} strings to {output_path}")
```

### 4.12 Export procedure metadata to JSON

Build a list of procedure records and write them as indented JSON.

```python
import json
from pathlib import Path

document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

output_path = Path(document.getExecutableFilePath() + ".proc_meta.json")

records = []
for segment in document.getSegmentsList():
    for index in range(segment.getProcedureCount()):
        procedure = segment.getProcedureAtIndex(index)
        if procedure is None:
            continue
        entry = procedure.getEntryPoint()
        records.append({
            "address": hex(entry),
            "name": document.getNameAtAddress(entry) or "",
            "signature": str(procedure.signatureString() or ""),
            "basic_block_count": int(procedure.getBasicBlockCount()),
            "segment": segment.getName(),
        })

output_path.write_text(json.dumps(records, indent=2) + "\n", encoding="utf-8")
print(f"Exported {len(records)} procedures to {output_path}")
```

### 4.13 Export cross-references for a procedure

Dump all callers and callees of the procedure at the current cursor position.

```python
import json
from pathlib import Path

document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

procedure = document.getCurrentProcedure()
if procedure is None:
    print("No procedure at the current cursor position.")
    raise SystemExit(1)

entry = procedure.getEntryPoint()
name = document.getNameAtAddress(entry) or hex(entry)

callers = []
for ref in procedure.getAllCallers():
    callers.append({
        "from": hex(ref.fromAddress()),
        "to": hex(ref.toAddress()),
        "type": int(ref.type()),
    })

callees = []
for ref in procedure.getAllCallees():
    callees.append({
        "from": hex(ref.fromAddress()),
        "to": hex(ref.toAddress()),
        "type": int(ref.type()),
    })

result = {
    "procedure": name,
    "address": hex(entry),
    "callers": callers,
    "callees": callees,
}

output_path = Path(document.getExecutableFilePath() + f".xrefs_{hex(entry)}.json")
output_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(f"Exported {len(callers)} callers and {len(callees)} callees to {output_path}")
```

### 4.14 Export segment layout to JSON

Capture the full segment and section layout of the binary.

```python
import json
from pathlib import Path

document = Document.getCurrentDocument()
if document is None:
    print("No active Hopper document.")
    raise SystemExit(1)

if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()

output_path = Path(document.getExecutableFilePath() + ".segments.json")

segments = []
for segment in document.getSegmentsList():
    sections = []
    for section_index in range(segment.getSectionCount()):
        section = segment.getSection(section_index)
        sections.append({
            "name": section.getName(),
            "start": hex(section.getStartingAddress()),
            "length": int(section.getLength()),
            "flags": int(section.getFlags()),
        })
    segments.append({
        "name": segment.getName(),
        "start": hex(segment.getStartingAddress()),
        "length": int(segment.getLength()),
        "file_offset": int(segment.getFileOffset()),
        "procedure_count": int(segment.getProcedureCount()),
        "string_count": int(segment.getStringCount()),
        "sections": sections,
    })

output_path.write_text(json.dumps(segments, indent=2) + "\n", encoding="utf-8")
print(f"Exported {len(segments)} segments to {output_path}")
```

## 5. API reference by class

This section groups the public methods into the operations you typically care about.

### 5.1 `GlobalInformation`

Use this when you need to branch on Hopper version:

| Method | Purpose |
|---|---|
| `getHopperMajorVersion()` | Return the major version string |
| `getHopperMinorVersion()` | Return the minor version string |
| `getHopperRevisionNumber()` | Return the revision string |
| `getHopperVersion()` | Return the full version string |

### 5.2 `Document`

#### Construction and lifecycle

| Method | Purpose |
|---|---|
| `newDocument()` | Create a new empty document |
| `getCurrentDocument()` | Get the active Hopper document |
| `getAllDocuments()` | List all open documents |
| `closeDocument()` | Close the current document |
| `loadDocumentAt(path)` | Load a document from disk |
| `saveDocument()` | Save the current Hopper database |
| `saveDocumentAt(path)` | Save the current Hopper database to a specific path |

#### Metadata and paths

| Method | Purpose |
|---|---|
| `getDocumentName()` | Display name of the document |
| `setDocumentName(name)` | Change the display name |
| `getDatabaseFilePath()` | Path to the Hopper database (`.hop`) |
| `getExecutableFilePath()` | Path to the executable under analysis |
| `setExecutableFilePath(path)` | Change the executable path |
| `is64Bits()` | Whether the document is treated as 64-bit |
| `getEntryPoint()` | Get the document entry point |
| `moveCursorAtEntryPoint()` | Move the cursor to the entry point |

#### Background analysis and logging

| Method | Purpose |
|---|---|
| `backgroundProcessActive()` | Whether Hopper analysis is still running |
| `requestBackgroundProcessStop()` | Ask the background analysis to stop and wait |
| `waitForBackgroundProcessToEnd()` | Block until analysis finishes |
| `log(msg)` | Write a line to Hopper's log window |

#### UI prompts

| Method | Purpose |
|---|---|
| `ask(msg)` | Prompt for a string |
| `askFile(msg, path, save)` | Open a file chooser |
| `askDirectory(msg, path)` | Open a directory chooser |
| `message(msg, buttons)` | Show a dialog and return the clicked button index |

#### Navigation and current context

| Method | Purpose |
|---|---|
| `getCurrentSegmentIndex()` | Segment index at the cursor |
| `getCurrentSegment()` | Segment at the cursor |
| `getCurrentSection()` | Section at the cursor |
| `getCurrentProcedure()` | Procedure at the cursor |
| `getCurrentAddress()` | Current cursor address |
| `setCurrentAddress(addr)` | Set the current address |
| `moveCursorAtAddress(addr)` | Move the UI cursor |
| `moveCursorOneLineDown()` | Move one assembly line down |
| `moveCursorOneLineUp()` | Move one assembly line up |
| `getSelectionAddressRange()` | Get the selected address range |
| `selectAddressRange(addrRange)` | Select a byte range |
| `getHighlightedWord()` | Get the currently highlighted word |
| `getRawSelectedLines()` | Get the selected text lines |
| `refreshView()` | Force the assembly view to refresh |

#### Segments, sections, and address mapping

| Method | Purpose |
|---|---|
| `getSegmentCount()` | Number of segments |
| `getSegment(index)` | Get a segment by index |
| `getSegmentByName(name)` | Get the first matching segment by name |
| `getSegmentsList()` | List all segments |
| `getSegmentIndexAtAddress(addr)` | Segment index for an address |
| `getSegmentAtAddress(addr)` | Segment for an address |
| `getSectionByName(name)` | Get the first matching section by name |
| `getSectionAtAddress(addr)` | Section for an address |
| `newSegment(start_address, length)` | Create a new segment |
| `deleteSegment(seg_index)` | Delete a segment |
| `renameSegment(seg_index, name)` | Rename a segment |
| `rebase(new_base_address)` | Rebase the loaded image |
| `getFileOffsetFromAddress(addr)` | Convert address to file offset |
| `getAddressFromFileOffset(offset)` | Convert file offset to address |

#### Names, labels, and operand formatting

| Method | Purpose |
|---|---|
| `setNameAtAddress(addr, name)` | Set a label name |
| `getNameAtAddress(addr)` | Get a label name |
| `getAddressForName(name)` | Resolve a name to an address |
| `getOperandFormat(addr, index)` | Get user-selected operand format |
| `getOperandFormatRelativeTo(addr, index)` | Get the relative base for operand formatting |
| `setOperandFormat(addr, index, fmt)` | Set operand format |
| `setOperandRelativeFormat(addr, relto, index, fmt)` | Set relative operand format |

#### Tags, colors, and bookmarks

| Method | Purpose |
|---|---|
| `getTagCount()` | Number of tags defined in the document |
| `getTagAtIndex(index)` | Get a tag by index |
| `tagIterator()` | Iterate tags |
| `getTagList()` | List tags |
| `buildTag(name)` | Create or reuse a named tag |
| `getTagWithName(name)` | Look up a tag by name |
| `destroyTag(tag)` | Remove a tag everywhere and delete it |
| `addTagAtAddress(tag, addr)` | Add a tag to an address |
| `removeTagAtAddress(tag, addr)` | Remove a tag from an address |
| `hasTagAtAddress(tag, addr)` | Test whether a tag exists at an address |
| `getTagCountAtAddress(addr)` | Tag count at an address |
| `getTagAtAddressByIndex(addr, index)` | Get a tag from an address by index |
| `tagIteratorAtAddress(addr)` | Iterate tags at an address |
| `getTagListAtAddress(addr)` | List tags at an address |
| `hasColorAtAddress(addr)` | Whether an address has a color |
| `setColorAtAddress(color, addr)` | Set a color |
| `getColorAtAddress(addr)` | Read a color |
| `removeColorAtAddress(addr)` | Remove a color |
| `setBookmarkAtAddress(address, name=None)` | Add a bookmark |
| `removeBookmarkAtAddress(address)` | Remove a bookmark |
| `hasBookmarkAtAddress(address)` | Test for bookmark presence |
| `renameBookmarkAtAddress(address, name)` | Rename a bookmark |
| `findBookmarkWithName(name)` | Find bookmarks by name |
| `getBookmarkName(address)` | Get a bookmark name |
| `getBookmarks()` | List bookmarked addresses |

#### Reading and writing mapped bytes

| Method | Purpose |
|---|---|
| `readBytes(addr, length)` | Read bytes across mapped segments |
| `readByte(addr)` | Read one byte |
| `readUInt16LE(addr)` | Read 16-bit little-endian |
| `readUInt32LE(addr)` | Read 32-bit little-endian |
| `readUInt64LE(addr)` | Read 64-bit little-endian |
| `readUInt16BE(addr)` | Read 16-bit big-endian |
| `readUInt32BE(addr)` | Read 32-bit big-endian |
| `readUInt64BE(addr)` | Read 64-bit big-endian |
| `writeBytes(addr, byteStr)` | Write bytes across mapped segments |
| `writeByte(addr, value)` | Write one byte |
| `writeUInt16LE(addr, value)` | Write 16-bit little-endian |
| `writeUInt32LE(addr, value)` | Write 32-bit little-endian |
| `writeUInt64LE(addr, value)` | Write 64-bit little-endian |
| `writeUInt16BE(addr, value)` | Write 16-bit big-endian |
| `writeUInt32BE(addr, value)` | Write 32-bit big-endian |
| `writeUInt64BE(addr, value)` | Write 64-bit big-endian |

#### Instruction helpers and binary output

| Method | Purpose |
|---|---|
| `assemble(instr, address, syntax)` | Assemble an instruction to bytes |
| `getInstructionStart(address)` | Find the beginning of the instruction at an address |
| `getObjectLength(address)` | Get the byte length of the object at an address |
| `generateObjectiveCHeader()` | Extract generated Objective-C headers from metadata |
| `produceNewExecutable(remove_sig=False)` | Build a modified executable |

### 5.3 `Segment`

`Segment` is the most important low-level analysis surface in Hopper.

#### Type constants

The public API documents these byte types:
- `TYPE_UNDEFINED`
- `TYPE_OUTSIDE`
- `TYPE_NEXT`
- `TYPE_INT8`
- `TYPE_INT16`
- `TYPE_INT32`
- `TYPE_INT64`
- `TYPE_ASCII`
- `TYPE_ALIGN`
- `TYPE_UNICODE`
- `TYPE_CODE`
- `TYPE_PROCEDURE`
- `BAD_ADDRESS`

Use `Segment.stringForType(t)` to convert a type constant into a string.

#### Layout and sections

| Method | Purpose |
|---|---|
| `getName()` | Segment name |
| `getStartingAddress()` | Segment start address |
| `getLength()` | Segment length in bytes |
| `getFileOffset()` | File offset of the segment start |
| `getFileOffsetForAddress(addr)` | File offset for a specific address |
| `getSectionCount()` | Number of sections |
| `getSection(index)` | Get a section by index |
| `getSectionsList()` | List all sections |
| `getSectionIndexAtAddress(addr)` | Section index for an address |
| `getSectionAtAddress(addr)` | Section for an address |

#### Reading and writing bytes

| Method | Purpose |
|---|---|
| `readBytes(addr, length)` | Read a byte range |
| `readByte(addr)` | Read one byte |
| `readUInt16LE(addr)` | Read 16-bit little-endian |
| `readUInt32LE(addr)` | Read 32-bit little-endian |
| `readUInt64LE(addr)` | Read 64-bit little-endian |
| `readUInt16BE(addr)` | Read 16-bit big-endian |
| `readUInt32BE(addr)` | Read 32-bit big-endian |
| `readUInt64BE(addr)` | Read 64-bit big-endian |
| `writeBytes(addr, bytesStr)` | Write a byte range |
| `writeByte(addr, value)` | Write one byte |
| `writeUInt16LE(addr, value)` | Write 16-bit little-endian |
| `writeUInt32LE(addr, value)` | Write 32-bit little-endian |
| `writeUInt64LE(addr, value)` | Write 64-bit little-endian |
| `writeUInt16BE(addr, value)` | Write 16-bit big-endian |
| `writeUInt32BE(addr, value)` | Write 32-bit big-endian |
| `writeUInt64BE(addr, value)` | Write 64-bit big-endian |

#### Types and disassembly state

| Method | Purpose |
|---|---|
| `markAsUndefined(addr)` | Mark one address undefined |
| `markRangeAsUndefined(addr, length)` | Mark a range undefined |
| `markAsCode(addr)` | Mark an address as code |
| `markAsProcedure(addr)` | Mark an address as a procedure |
| `markAsDataByteArray(addr, count)` | Mark a byte array |
| `markAsDataShortArray(addr, count)` | Mark a short array |
| `markAsDataIntArray(addr, count)` | Mark an int array |
| `getTypeAtAddress(addr)` | Get the Hopper byte type |
| `setTypeAtAddress(addr, length, typeValue)` | Set a byte type over a range |
| `makeAlignment(addr, size)` | Create an alignment object |
| `getNextAddressWithType(addr, typeValue)` | Scan forward for a type |
| `disassembleWholeSegment()` | Ask Hopper to disassemble the entire segment |

#### ARM and Thumb helpers

| Method | Purpose |
|---|---|
| `isThumbAtAddress(addr)` | Whether an address is in Thumb mode |
| `setThumbModeAtAddress(addr)` | Force Thumb mode |
| `setARMModeAtAddress(addr)` | Force ARM mode |

#### Names, comments, xrefs, and instructions

| Method | Purpose |
|---|---|
| `setNameAtAddress(addr, name)` | Set a label |
| `getNameAtAddress(addr)` | Read a label |
| `getDemangledNameAtAddress(addr)` | Read a demangled label |
| `getCommentAtAddress(addr)` | Read a prefix comment |
| `setCommentAtAddress(addr, comment)` | Set a prefix comment |
| `getInlineCommentAtAddress(addr)` | Read an inline comment |
| `setInlineCommentAtAddress(addr, comment)` | Set an inline comment |
| `getInstructionAtAddress(addr)` | Fetch an instruction object |
| `getReferencesOfAddress(addr)` | Addresses that reference this address |
| `getReferencesFromAddress(addr)` | Addresses referenced from this address |
| `addReference(addr, referenced)` | Add a cross-reference |
| `removeReference(addr, referenced)` | Remove a cross-reference |

#### Labels, procedures, arrays, and strings

| Method | Purpose |
|---|---|
| `getLabelCount()` | Number of labels in the segment |
| `labelIterator()` | Iterate labels |
| `getLabelsList()` | List label names |
| `getNamedAddresses()` | List addresses that have labels |
| `getProcedureCount()` | Number of procedures in the segment |
| `getProcedureAtIndex(index)` | Get a procedure by index |
| `getProcedureIndexAtAddress(address)` | Get the procedure index at an address |
| `getProcedureAtAddress(address)` | Get the procedure at an address |
| `getInstructionStart(address)` | Find instruction start for an address |
| `getObjectLength(address)` | Byte length of the object at an address |
| `isPartOfAnArray(address)` | Whether an address is inside an array |
| `getArrayStartAddress(address)` | Array start address |
| `getArrayElementCount(address)` | Element count |
| `getArrayElementAddress(address, index)` | Element address |
| `getArrayElementSize(address)` | Element size |
| `getStringCount()` | Number of strings |
| `getStringAtIndex(index)` | Read one string by index |
| `getStringAddressAtIndex(index)` | Read one string address by index |
| `getStringsList()` | List strings and their addresses |

### 5.4 `Section`

`Section` is intentionally small:

| Method | Purpose |
|---|---|
| `getName()` | Section name |
| `getStartingAddress()` | Section start address |
| `getLength()` | Section length in bytes |
| `getFlags()` | Section flags |

### 5.5 `Instruction`

Use `Instruction` when you need architecture or operand-level details.

| Method | Purpose |
|---|---|
| `stringForArchitecture(t)` | Convert an architecture constant to a string |
| `getArchitecture()` | Get the instruction architecture |
| `getInstructionString()` | Mnemonic or instruction text |
| `getArgumentCount()` | Number of operands |
| `getRawArgument(index)` | Raw assembly operand |
| `getFormattedArgument(index)` | Hopper-formatted operand |
| `isAnInconditionalJump()` | Whether the instruction is an unconditional jump |
| `isAConditionalJump()` | Whether the instruction is a conditional jump |
| `getInstructionLength()` | Byte length of the instruction |

Documented architecture constants include:
- `ARCHITECTURE_UNKNOWN`
- `ARCHITECTURE_i386`
- `ARCHITECTURE_X86_64`
- `ARCHITECTURE_ARM`
- `ARCHITECTURE_ARM_THUMB`
- `ARCHITECTURE_AARCH64`

### 5.6 `Procedure`

The public `Procedure` API is centered around entry points, basic blocks, locals, tags, callers, callees, local labels, decompilation, and register renaming.

#### Location and structure

| Method | Purpose |
|---|---|
| `getSegment()` | Segment containing the procedure |
| `getSection()` | Section containing the procedure |
| `getEntryPoint()` | Procedure entry address |
| `getBasicBlockCount()` | Number of basic blocks |
| `getBasicBlock(index)` | Get a block by index |
| `getBasicBlockAtAddress(addr)` | Find the block containing an instruction |
| `basicBlockIterator()` | Iterate all basic blocks |
| `getHeapSize()` | Procedure heap size in bytes |
| `getLocalVariableList()` | List of local variables |

#### Tags

| Method | Purpose |
|---|---|
| `addTag(tag)` | Add a tag to the procedure |
| `removeTag(tag)` | Remove a tag |
| `hasTag(tag)` | Check whether the tag is present |
| `getTagCount()` | Number of tags |
| `getTagAtIndex(index)` | Read one tag |
| `tagIterator()` | Iterate tags |
| `getTagList()` | List tags |

#### Call relationships

| Method | Purpose |
|---|---|
| `getAllCallers()` | Call references into the procedure |
| `getAllCallees()` | Call references out of the procedure |
| `getAllCallerProcedures()` | Caller procedures |
| `getAllCalleeProcedures()` | Procedures called by this procedure |

#### Local labels

| Method | Purpose |
|---|---|
| `hasLocalLabelAtAddress(addr)` | Whether a local label exists |
| `localLabelAtAddress(addr)` | Read the local label |
| `setLocalLabelAtAddress(label, addr)` | Set a local label |
| `declareLocalLabelAt(addr)` | Create a local label and return its name |
| `removeLocalLabelAtAddress(addr)` | Remove a local label |
| `addressOfLocalLabel(label)` | Resolve a local label to an address |

#### Decompiled output and signature

| Method | Purpose |
|---|---|
| `decompile()` | Return pseudo-code or `None` |
| `signatureString()` | Return the C-like signature string |

#### Register renaming

| Method | Purpose |
|---|---|
| `renameRegister(reg_cls, reg_idx, name)` | Rename a register inside the procedure |
| `registerNameOverride(reg_cls, reg_idx)` | Read the override name |
| `clearRegisterNameOverride(reg_cls, reg_idx)` | Remove the override |

The API also publishes register class and register index constants for x86 and ARM, such as:
- `REGCLS_GENERAL_PURPOSE_REGISTER`
- `REGCLS_X86_SSE`
- `REGCLS_ARM_VFP_DOUBLE`
- `REGIDX_X86_RAX`
- `REGIDX_X86_RIP`

Important warning: the Hopper docs note that modifying the document structure can invalidate a Python `Procedure` object. Do not keep long-lived cached procedure handles across structural edits like creating or deleting procedures.

### 5.7 `BasicBlock`

| Method | Purpose |
|---|---|
| `getProcedure()` | Parent procedure |
| `getStartingAddress()` | Block start address |
| `getEndingAddress()` | Address after the last instruction |
| `getSuccessorCount()` | Number of successors |
| `getSuccessorIndexAtIndex(index)` | Successor block index |
| `getSuccessorAddressAtIndex(index)` | Successor block address |
| `addTag(tag)` | Add a tag |
| `removeTag(tag)` | Remove a tag |
| `hasTag(tag)` | Check a tag |
| `getTagCount()` | Number of tags |
| `getTagAtIndex(index)` | Read a tag |
| `tagIterator()` | Iterate tags |
| `getTagList()` | List tags |

### 5.8 `CallReference`

`CallReference` tells you where a call originated and where it points.

| Method | Purpose |
|---|---|
| `type()` | Call type |
| `fromAddress()` | Source callsite |
| `toAddress()` | Referenced destination |

Documented call-type values:
- `CALL_NONE`
- `CALL_UNKNOWN`
- `CALL_DIRECT`
- `CALL_OBJC`

### 5.9 `LocalVariable`

| Method | Purpose |
|---|---|
| `name()` | Local variable name |
| `displacement()` | Stack displacement |

### 5.10 `Tag`

| Method | Purpose |
|---|---|
| `getName()` | Tag name |

## 6. Common pitfalls and defensive habits

### Wait for analysis

Always use:

```python
if document.backgroundProcessActive():
    document.waitForBackgroundProcessToEnd()
```

before exporting procedures, strings, or xrefs.

### Prefer the documented public API

If you find old examples using undocumented helpers such as a direct document-wide procedure list, avoid copying them. In this repository, the stable pattern is segment-based enumeration.

### Treat addresses as your canonical identifiers

The public API consistently revolves around addresses. When you need a stable procedure identity, use `procedure.getEntryPoint()` plus `document.getNameAtAddress(entry)` instead of relying on undocumented convenience methods.

### Handle `False`, `None`, and `BAD_ADDRESS`

Different Hopper APIs use different failure sentinels:
- `False` for failed reads and writes
- `None` for missing objects
- `Segment.BAD_ADDRESS` for invalid address queries

Check them explicitly.

### Refresh the UI after write-back

After setting names, comments, tags, colors, or bookmarks, call:

```python
document.refreshView()
```

so the assembly view reflects your changes immediately.

### Re-fetch after structural edits

After rebasing, segment edits, large-scale retyping, or procedure recovery, do not assume previously held objects are still valid. Re-fetch the document, segment, or procedure handles you need.

## 7. Repository examples

These scripts are the best local examples of Hopper 6.2.1 scripting style in this repository:

| File | What it demonstrates |
|---|---|
| `scripts/hopper/_hopper_utils.py` | Analysis wait pattern, procedure iteration, address and tag helpers |
| `scripts/hopper/hopper_export_metadata.py` | Segment, section, string, procedure, local-variable, and basic-block export |
| `scripts/hopper/hopper_export_callgraph.py` | Call graph extraction through `Procedure` and `CallReference` |
| `scripts/hopper/hopper_export_rust_analysis.py` | Symbol-oriented export and demangling workflow |
| `scripts/hopper/hopper_apply_annotations.py` | Name, comment, tag, color, and bookmark write-back |

## 8. Suggested starting point

If you are new to Hopper scripting, start with this sequence:
1. Get the current document.
2. Wait for background analysis to finish.
3. Enumerate segments.
4. Enumerate procedures through segments.
5. Use entry-point addresses as stable identifiers.
6. Export or annotate.
7. Refresh the UI after write-back.

That sequence matches the approach used by the maintained Hopper scripts in this repository.
