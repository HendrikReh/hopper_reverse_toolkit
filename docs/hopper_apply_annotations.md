# hopper_apply_annotations.py

**Version**: 1.5.0
**Runs in**: Hopper (Scripts > Run Script)

## Purpose

Applies labels, comments, inline comments, tags, colors, and bookmarks back into the active Hopper document from a JSON payload. This is the write-back companion to the export scripts.

## Input

A JSON file with any combination of these top-level keys:

| Key | Record fields | Hopper API |
|---|---|---|
| `labels` | `address`, `name` | `setNameAtAddress` |
| `comments` | `address`, `comment` | `setCommentAtAddress` |
| `inline_comments` | `address`, `comment` | `setInlineCommentAtAddress` |
| `tags` | `address`, `tag` | `buildTag` + `addTagAtAddress` |
| `colors` | `address`, `color` | `setColorAtAddress` |
| `bookmarks` | `address`, `name` (optional) | `setBookmarkAtAddress` |

### Example payload

```json
{
  "labels": [{"address": "0x1000", "name": "entry_main"}],
  "comments": [{"address": "0x1000", "comment": "Recovered entry point"}],
  "inline_comments": [{"address": "0x1004", "comment": "Calls helper"}],
  "tags": [{"address": "0x1000", "tag": "review"}],
  "colors": [{"address": "0x1000", "color": "#FF112233"}],
  "bookmarks": [{"address": "0x1000", "name": "main entry"}]
}
```

## Behavior

- If no file path argument is given, opens a Hopper file picker dialog.
- Addresses accept hex (`0x...`) or decimal strings.
- Colors accept `#AARRGGBB` hex strings or integer values.
- Refreshes the Hopper view after applying annotations.
- Prints a summary of how many items were applied per category.

## Usage

### With a file path argument

```
Scripts > Run Script > hopper_apply_annotations.py /path/to/annotations.json
```

### Without arguments (file picker)

```
Scripts > Run Script > hopper_apply_annotations.py
```

### Programmatic

```python
from hopper_apply_annotations import apply_annotations

summary = apply_annotations(document, payload)
# summary = {"labels": 3, "comments": 5, ...}
```

## Dependencies

- `_hopper_utils.py` (bundled)
- Hopper Python API (`hopper` module)
