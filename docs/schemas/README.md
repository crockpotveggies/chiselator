# Draft analysis schemas and checks

All schemas use JSON Schema draft 2020-12 and Chiselator contract version `0.1.0`. They are **design artifacts**, not a released simulator/plugin API. Exact-version negotiation applies during draft development. Their URN identifiers resolve locally; validation does not fetch schemas from the network.

| Schema | Purpose |
| --- | --- |
| [design-graph](design-graph.schema.json) | Logical domains, nodes/ports, channels and boundary contracts |
| [flow-event](flow-event.schema.json) | Normalized transaction/causality/effect events; one JSONL record |
| [capture-manifest](capture-manifest.schema.json) | Input artifact hashes, scope, time window and coverage |
| [plugin-manifest](plugin-manifest.schema.json) | Package identity, roles, exact API/schema versions and native entrypoints |
| [analysis-result](analysis-result.schema.json) | Analysis status, exact or unknown metrics, findings and provenance |

See the [graph/event semantics](../graph-event-contract.md), [plugin protocol](../plugin-api.md) and [worked example](../examples/hybrid-flow/README.md). These are new public analysis formats, not replacements for upstream chisel-async schemas. RPC messages, raw signal capture, wait/occupancy probes, general lineage and component-specific reset validation still need implementation/conformance fixtures.

From the repository root, use a Python environment with the pinned [documentation dependencies](../../tools/requirements-docs.txt):

```console
python -m pip install -r tools/requirements-docs.txt
python tools/check_docs.py
python tools/validate_analysis_contracts.py
python -m unittest discover -s tools -p "test_analysis_contracts.py"
python tools/render_analysis_charts.py
```

`jsonschema` is needed for validation/tests; Matplotlib is only needed to regenerate charts. Neither is a proposed dependency of the native simulator. The validator checks shapes, bundle hashes, graph references, selected lifecycle/order/clock/epoch invariants and fixture identity. Tests include independently specified expected arithmetic and known-bad mutations.

Fixture JSON/JSONL files use LF line endings enforced by `.gitattributes`; content hashes must survive Windows/Linux/macOS checkouts. A fixture edit requires updating its capture descriptor and expected-result input hash deliberately. Do not automatically regenerate expected arithmetic from a production analyzer.

**Limits:** the semantic checker currently accepts known-idle captures and the fixture's four-phase/clocked sampled contracts. It does not execute raw signal decoders, validate all scheduler phases, qualify Click, prove retained-effect ownership, check arbitrary component mappings or validate a production plugin. Unsupported cases fail explicitly where the checker knows the missing capability. Passing this kit cannot establish circuit correctness or full API conformance. Expand it with independent fixtures before advertising another capability.
