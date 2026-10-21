# Extensibility and hybrid flow analysis plan

Chiselator will expose a versioned tool-extension interface. The first plugin explains traffic, waiting and bottleneck candidates in clocked, async and hybrid designs through a connected graph, transaction timeline and metrics table. The host/analyzer/viewer remain proposed. Draft schemas and a small checked example now exist.

This overview owns product scope. Detailed contracts now live in the [plugin API](plugin-api.md), [graph/event schema](graph-event-contract.md) and [algorithm research](flow-analysis-algorithms.md), avoiding duplicate interface specifications here. The [five specifications](specs/README.md) continue to own circuit semantics. The [current stack baseline](integration-status.md) records the built library and MCU inputs.

## Product outcomes and first release

Select a recorded run, inspect its graph over a simulated-time interval, follow delayed transactions and inspect the evidence behind findings. The same results work through CLI/MCP without a viewer. Offline analysis comes first; live dashboards remain later work.

The first decoder slice is four-phase plus sampled/held-offer clocked interfaces and their qualified boundaries. Native Click follows as a required integration slice for the second existing MCU variant. A four-phase-only milestone is partial, not compatibility with all chisel-async components. Dual-rail/QDI and richer buses have their own qualification gates.

Ordinary clocked designs need no async metadata to simulate. Transaction analysis does need declared interfaces and qualified decoders. Missing metadata is a visible limitation, not permission to infer transactions from signal names.

## Existing tooling and design implications

The following documented features inform the design. They are precedents, not dependencies or evidence that an upstream product implements our hybrid semantics.

| Tool | Relevant capability | Application here |
| --- | --- | --- |
| [AMD Vitis Dataflow Viewer](https://docs.amd.com/r/2025.2-English/ug1702-vitis-accelerated-reference/Dataflow-Viewer) | Process/channel graphs, source navigation, filtering and measured channel/process behavior from RTL co-simulation | Link topology to measured traffic and waits. This is an HLS-specific workflow, not automatic profiling for arbitrary Vivado RTL. |
| [Synopsys Verdi](https://www.synopsys.com/verification/debug/verdi.html) | Transaction/protocol views, latency/bandwidth analysis, waveform comparison and tracing | Follow transactions and compare behavior across runs. |
| [Cadence Verisium Debug](https://www.cadence.com/en_US/home/tools/system-design-and-verification/ai-driven-verification/verisium-debug.html.html) | Connected waveform/source/hierarchy/schematic views and Python functions, widgets and integrations | Expose structured analysis and presentation extension points. |
| [Vivado CDC report](https://docs.amd.com/r/en-US/ug906-vivado-design-analysis/Report-Clock-Domain-Crossings) | Structural analysis of clock-domain crossings, distinct from timing-slack analysis | Keep crossing structure, runtime behavior and physical timing findings separate. |
| [ACT channel loggers](https://avlsi.csl.yale.edu/act/doku.php?id=sim:loggers) and [Workcraft verification](https://workcraft.org/help/verification) | Successful token logging and checks such as transition consistency, deadlock freeness and mutex protocol properties | Preserve async protocol meaning and distinguish observed failures from formal properties. |
| [Verilator execution profiling](https://verilator.org/guide/latest/simulating.html#execution-profiling) | Execution timelines and host-thread work distribution | Keep simulated hardware performance separate from simulator execution cost. |
| [Perfetto plugins](https://perfetto.dev/docs/contributing/ui-plugins) and [trace processing](https://perfetto.dev/docs/analysis/trace-processor) | Trace-scoped tracks, tabs and commands; queryable recorded traces | Separate capture, analysis and presentation, and support offline queries. |
| [QEMU plugins](https://www.qemu.org/docs/master/devel/tcg-plugins.html) | Version negotiation, opaque internals and efficient instrumentation | Publish explicit compatibility and batch observations without exposing compiler objects. |

## Extension boundaries

Plugins can decode qualified recordings, analyze graph/events, or export validated results. Presentation is declarative data. Execution backends, circuit mutation, new primitive semantics and synthesis jobs use separate interfaces and are not granted by the initial analysis API.

## Plugin packaging and lifecycle

The [API contract](plugin-api.md) defines local stdio JSON-RPC, exact draft-version negotiation, package manifests, native process supervision, cancellation, staging and publication. Artifacts travel as immutable files, not high-volume RPC messages. Installed plugins are trusted code; a process is not a security sandbox. No imported artifact can install or launch a plugin.

Analysis status is COMPLETE, PARTIAL, UNSUPPORTED, CANCELED or ERROR. Timeout is an ERROR with a structured reason. Simulation outcome remains independent. Required-analysis gates cannot pass on incomplete results. The first-party analyzer uses the public API and is accompanied by an independently implemented exporter to expose accidental private dependencies.

## Shared graph and observation contract

The [schema contract](graph-event-contract.md) separates logical topology, causal event DAGs and dynamic wait graphs. Graph IDs are model-scoped, events retain exact femtoseconds and sequence, and boundary relationships preserve per-channel transaction identities. Effects have separate ownership and reset epochs. Schemas, an illustrative bundle and selected negative controls are in the [contract kit](schemas/README.md).

Capture actual commits before coalescing. Required observations are lossless or fail explicitly. Imported traces with missing phase or causal metadata cannot support analyses requiring that information. Re-analysis does not rerun the simulator.

## Protocol and hybrid semantics

Four-phase offer/accept/return-to-idle, native Click parity and clocked sampling are distinct contracts. Plain Chisel Decoupled transfers only establish a token at fire; do not assign an earlier stable offer without stronger declared rules. A bridge captures on its actual consumer edge, not a nearby parent-clock edge. Receipt boundaries may borrow source payload with zero internal payload slots.

Correlate with explicit boundary evidence, tags or qualified queue order, never payload equality or timestamp proximity. Fork/join has multiple causal parents and overlapping intervals. Application reset may abort a response while an accepted POR-owned effect still commits. The detailed [boundary examples](graph-event-contract.md#crossing-a-clockedasync-boundary) illustrate these distinctions.

## Metrics and interpretation

Report offers, acceptances, completions and aborts separately. Define half-open windows, offer cohorts, pending/preexisting observations and coverage. Latency and traffic use simulated time; host analysis/simulator cost is separate. Occupancy requires capacity and queue observations. Wait reasons need component evidence. Unknown is not zero.

High traffic alone is not a bottleneck. The initial analyzer sorts named metrics with evidence, sample counts and limits; it has no opaque hotspot score. Wait cycles are candidates, deadlines are policy checks, and deadlock proof requires a qualified closed model. [Algorithm decisions](flow-analysis-algorithms.md) cover streaming decoders, SCCs, causal path analysis, exact statistics and layout choices.

## Graph report and automation

Publish the logical graph, normalized events, capture manifest, analysis result and optional CSV/local-view bundle. Preserve plugin/decoder/metric versions, input hashes, configuration, requested scope and coverage. Comparisons require compatible model mappings, workloads and metric definitions; intentional experimental differences are explicit.

Graph, timeline and metric table share IDs and evidence references. Clock/reset domains, protocol badges, unknown coverage and feedback remain visible. CLI/MCP use the same job service; viewer plugins cannot inject executable UI. Physical-tool overlays such as Vivado reports may be added later through versioned mappings and provenance.

## Delivery sequence and acceptance

| Increment | Deliverable | Exit evidence |
| --- | --- | --- |
| A Contracts | Draft schemas, exact definitions and independent known-answer fixtures | Current small kit is a start; add raw decoders, Click, reset/effects, fork/join and missing-data controls |
| B Host/SDK | Portable process host, typed SDK and independent exporter | Negotiation/cancel/crash/limits/publication tests on all native targets |
| C Offline analyzer | Decoders, causal relationships and exact metrics | Independent expected counts/times/lineage; unsupported evidence stays unknown |
| D Capture/viewer | Runtime capture and linked graph/timeline/table | Instrumented/uninstrumented circuit agreement; visual/report consistency; measured overhead |
| E MCU integration | Both qualified variants and clocked service boundaries | Independent retirement/effects and delayed-service/reset/persistence controls |

EXT/FLW requirements remain in the [MVP list](mvp-feature-list.md#p0-extensibility-and-hybrid-flow-analysis); PLG-01–04 and FLOW-01–08 remain in the [test plan](test-plan.md#extension-and-hybrid-flow-analysis-qualification). Schema checks are not a completed release gate. Re-estimate implementation effort after host/decoder probes.

## Deferred capabilities and experiment decisions

Defer live delivery, remote marketplaces/services, untrusted plugin sandboxing, arbitrary UI code, execution-changing plugins, automatic RTL/buffer edits, broad formal verification and physical signoff. Prototype layout/rendering and capture/index budgets before choosing dependencies. Future CPU/GPU backends must preserve required observations or report the requested analysis unsupported.
