# export_graphml.py

**Version**: 1.4.0
**Runs in**: Command line (outside Hopper)

## Purpose

Converts a Hopper callgraph JSON export (`*.callgraph.json`) into GraphML format for use with external graph analysis tools such as Gephi, yEd, or Cytoscape.

## Output

A `.graphml` file containing the call graph as a directed graph with named nodes.

## Behavior

- Nodes include a `name` data attribute from the callgraph export.
- Edges are deduplicated by (source, target) pair.
- Nodes referenced in edges but missing from the node list are auto-created without a name attribute.
- All IDs and names are XML-escaped.

## Usage

```bash
python export_graphml.py <callgraph.json> <output.graphml>
```

### Arguments

| Argument | Required | Description |
|---|---|---|
| `input_json` | yes | Path to `*.callgraph.json` |
| `output_graphml` | yes | Destination GraphML file path |

### Example

```bash
python export_graphml.py myapp.callgraph.json myapp.graphml
```

## Output format

```xml
<?xml version="1.0" encoding="UTF-8"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns">
  <key id="name" for="node" attr.name="name" attr.type="string"/>
  <graph id="G" edgedefault="directed">
    <node id="0x1000"><data key="name">main</data></node>
    <edge source="0x1000" target="0x2000"/>
  </graph>
</graphml>
```

## Dependencies

- `_hopper_utils.py` (bundled)
