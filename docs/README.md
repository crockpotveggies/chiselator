# Documentation map

Start with [stack status](integration-status.md). chisel-async and RISCay-MCU are built upstream; Chiselator's execution engine and plugin product remain proposed. Draft schemas and checks in this repository make the analysis design reviewable without implying a working simulator.

| Question | Owning document |
| --- | --- |
| Why this simulator, and what carries over from GSIM? | [Proposal](simulator-proposal.md) |
| What components will we implement? | [Software architecture](software-architecture.md) |
| How do clocked and async execution share efficient storage and scheduling? | [Execution data model](specs/06-execution-data-model.md) |
| What behavior must implementations preserve? | [Six specifications](specs/README.md) |
| What belongs in the first release? | [MVP feature list](mvp-feature-list.md) |
| How do we avoid optimistic accuracy/performance claims? | [Test plan](test-plan.md) |
| How do built upstream products integrate? | [Library](chisel-async.md), [MCU](async-mcu.md) |
| What can tools plug into? | [Extension overview](extensibility-flow-analysis.md), [plugin API](plugin-api.md) |
| How are topology, events and transaction relationships represented? | [Graph/event contract](graph-event-contract.md), [draft schemas](schemas/README.md) |
| Which algorithms and charts should we use? | [Research and algorithm decisions](flow-analysis-algorithms.md) |
| What remains separate physical work? | [Physical implementation boundary](chip-build-plan.md) |

The six implementation specifications take precedence over broad architecture sketches. The plugin and graph/event documents refine public analysis interfaces without changing circuit execution semantics. Schemas are draft version `0.1.0`; prose owns cross-record invariants. Upstream documents own product APIs, source pins and test receipts. Historical dates describe prior research, not fresh verification of all cited tools.
