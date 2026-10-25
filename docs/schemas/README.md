# Draft analysis schemas and checks

All six schemas use JSON Schema draft 2020-12 and Chiselator artifact contract version `0.2.0`. They are **design artifacts**, not a released simulator/plugin API. Exact-version negotiation applies during draft development. The process API remains `0.1.0`; its lifecycle did not change. Their URN identifiers resolve locally; validation does not fetch schemas from the network.

| Schema | Purpose |
| --- | --- |
| [design-graph](design-graph.schema.json) | Logical domains, nodes/ports, channels and boundary contracts |
| [flow-event](flow-event.schema.json) | Normalized transaction/causality/effect events; one JSONL record |
| [probe-event](probe-event.schema.json) | Separate JSONL stream: compressed consumer-edge classes, explicit queue snapshots/operations, waits and probe gaps |
| [capture-manifest](capture-manifest.schema.json) | Input artifact hashes, scope, time window and coverage |
| [plugin-manifest](plugin-manifest.schema.json) | Package identity, roles, exact API/schema versions and native entrypoints |
| [analysis-result](analysis-result.schema.json) | Analysis status, exact or unknown metrics, findings and provenance |

See the [graph/event semantics](../graph-event-contract.md), [plugin protocol](../plugin-api.md), [receipt example](../examples/hybrid-flow/README.md) and [two pipeline examples](../examples/pipeline-bottleneck/README.md). These are public analysis formats, not replacements for upstream chisel-async schemas. Flow-event adds only `clock.state`; probe kinds never enter its closed union. Design-graph adds sampling policies, wait-vocabulary references and declared storage. Capture/result hashes and coverage include the optional probe artifact; plugin-manifest advertises probe support independently. The transaction-only example exporter deliberately omits it. All fixtures migrate together to `0.2.0`; no automatic draft compatibility is inferred.

From the repository root, use a Python environment with the pinned [documentation dependencies](../../tools/requirements-docs.txt):

```console
python -m pip install -r tools/requirements-docs.txt
python tools/check_docs.py
python tools/validate_analysis_contracts.py
python -m unittest discover -s tools -p "test_analysis_contracts.py"
python tools/render_analysis_charts.py
```

`jsonschema` is needed for validation/tests; run the chart command only when chart inputs change. Neither dependency is proposed for the native simulator. The validator checks shapes, bundle hashes, graph references, selected lifecycle/order/clock/epoch invariants, probe coverage and fixture identity. Tests include independently specified arithmetic and known-bad mutations with specific rejection messages. The formula in the test file is an independent fixture oracle, not a shipped analyzer.

Fixture JSON/JSONL files use LF line endings enforced by `.gitattributes`; content hashes must survive Windows/Linux/macOS checkouts. A fixture edit requires updating its capture descriptor and expected-result input hash deliberately. Do not automatically regenerate expected arithmetic from a production analyzer.

**Limits:** the semantic checker accepts known-idle channel captures, four-phase/clocked sampled contracts, single-polarity consumer domains, capture-start queue snapshots and known-idle waits. Probe captures crossing reset, queue recovery after a gap, raw signal decoding, Click, full scheduler phases, retained effects, arbitrary component mappings and host/plugin lifecycle remain unqualified. Missing probes remain explicitly unavailable. Passing this kit cannot establish circuit correctness or full API conformance. Upstream component probes/vocabularies/ABI are required before runtime acceptance.
