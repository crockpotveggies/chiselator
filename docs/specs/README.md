# Chiselator implementation specifications

Draft contracts, integration status updated October 20; execution data model added October 25, 2026. The simulator and production APIs are not implemented. Draft analysis schemas and limited documentation tests now exist; see the [contract kit](../schemas/README.md). These specifications refine the [software architecture](../software-architecture.md) and take precedence over overlapping sketches. Changes to observable behavior require a spec change and a regression fixture.

| Specification | Owns | Initial implementation owner |
| --- | --- | --- |
| [Execution semantics](01-execution-semantics.md) | Values, time, scheduling, state and observation | Runtime/compiler |
| [Compiler/runtime interface](02-compiler-runtime-interface.md) | CIRCT support, plans, kernels, ownership and backends | Compiler/runtime |
| [Async model contracts](03-async-model-contracts.md) | Primitives, channels, timing and the MCU example | Async/runtime |
| [Application lifecycle](04-application-lifecycle.md) | Sessions, jobs, CLI, adapters, MCP and native packaging | Application/integration |
| [Artifacts and compatibility](05-artifacts-compatibility.md) | Schemas, cache, reports, replay and release evidence | Integration/release |
| [Execution data model](06-execution-data-model.md) | Plan/session tables, activations versus deliveries, clock-calendar fast paths and CPU/GPU layout experiments | Runtime/compiler |

“Must” denotes a proposed release requirement, not a claim of current support. Owners are engineering roles; assign maintainers when implementation starts. Existing requirement and suite IDs refer to the [MVP list](../mvp-feature-list.md) and [test plan](../test-plan.md).

Specification 01 owns observable scheduling semantics, 02 owns compiler/runtime boundaries, and 06 refines their storage and dispatch design. Specification 06 does not replace CIRCT or the public graph/event schemas. The 20× Verilator stretch ambition and the earlier 0.80× GSIM release gate remain separate under the [performance protocol](../test-plan.md#controlled-performance-experiments).

The companion [extension overview](../extensibility-flow-analysis.md), [plugin API](../plugin-api.md) and [graph/event contract](../graph-event-contract.md) refine public analysis and EXT/FLW requirements. They cannot replace circuit semantics, expose compiler objects or turn incomplete analysis into passing simulation evidence. Read-only analysis plugins are distinct from runtime-loaded primitive plugins in specification 02.

## Settled scope

- Apache-2.0 project code; dependency licenses remain separate.
- [chisel-async](../chisel-async.md) and [RISCay-MCU](../async-mcu.md) are built in dedicated repositories. Chiselator consumes their pinned contracts and independently checked corpus; native acceptance is still pending. The [integration baseline](../integration-status.md) owns inspected revisions and evidence limits.
- Physical implementation remains step 4's separate responsibility. MCU physical development already exists upstream; PDK, synthesis, cell characterization, STA/SDF and manufacturing qualification do not gate functional simulation.
- Chisel and SystemVerilog converge through a pinned, verified CIRCT subset. CIRCT is a family of dialects, not one automatically supported input format. The execution plan is scheduling/storage metadata, not a new HDL IR.
- Rust owns the runtime and application; C++ owns CIRCT/LLVM compilation and initial JIT integration behind versioned C interfaces.
- Native CPU releases target Windows x86-64, Linux x86-64 and macOS arm64. WSL is optional. GPU execution is an optional later backend, with no GPU dependency in the CPU package.
- Public analysis plugins use versioned graph/observation/result artifacts and supervised local processes. The first flow plugin covers clocked, async and hybrid designs through qualified protocol decoders; offline graph/timeline reports precede live updates.
- No Yosys dependency in native simulation. [Physical tool adapters](../chip-build-plan.md#synthesis-decision), including the selected FPGA tool Vivado, have separate qualification.
- The first complete application is the existing hybrid RV32E MCU, in four-phase BD and native Click variants, with clocked service boundaries. Generic boot/peripheral firmware is the baseline; Pi supervision is a separate application profile. Small fixtures precede full-MCU native acceptance.
- Native simulation works without GF180, another PDK, a physical build or ACT. Upstream physical exploration does not change that dependency boundary.

## Implementation gates

1. Pin existing library exports, primitive contracts, probes and independent external evidence; preserve resource hashes and timing identities through import.
2. Freeze both MCU variants, firmware/profile and independent instruction/effect/boot references. Do not relabel upstream passes as native Chiselator qualification.
3. Pin the simulator compiler toolchain; execute scheduling/Arc and native packaging probes. Implement and validate the plan loader, real kernel ABI and session lifecycle. Run equivalent Chisel/SV clocked fixtures on all three native platforms.
4. Integrate the library's delay/process semantics, native async bindings and channel monitors. Run the already qualified MCU at S0 with its independent references; do not redefine primitive semantics inside the simulator.
5. Qualify source timing provenance and model-level delay/constraint fixtures in Chiselator, with hand-derived passing/failing outcomes and no PDK or physical tools. Optional ACT coordination cannot become a native execution dependency.
6. Complete adapters, CLI/MCP reports, replay and package tests against these same contracts. Add optimizations only with off-switch comparisons and measured benefit.
7. Qualify the analysis host, normalized events, transaction lineage and viewer through the public plugin API. Keep physical P1–P3 and mapped-netlist/STA/SDF claims in the [separate target flow](../chip-build-plan.md).

Arc reuse, ACT control APIs and exact frontend coverage remain experiments with explicit pass/fail evidence. An integration that fails its gate stays unsupported; it must not silently weaken semantics. The companion chip plan defines physical tool boundaries separately from these six simulator contracts.
