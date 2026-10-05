# Chiselator implementation specifications

Draft contracts, October 5, 2026. These specify proposed behavior; no simulator, API, schema or test described here is implemented yet. They refine the [software architecture](../software-architecture.md), and take precedence over overlapping architecture sketches. Changes to observable behavior require a spec change and a regression fixture.

| Specification | Owns | Initial implementation owner |
| --- | --- | --- |
| [Execution semantics](01-execution-semantics.md) | Values, time, scheduling, state and observation | Runtime/compiler |
| [Compiler/runtime interface](02-compiler-runtime-interface.md) | CIRCT support, plans, kernels, ownership and backends | Compiler/runtime |
| [Async model contracts](03-async-model-contracts.md) | Primitives, channels, timing and the MCU example | Async/runtime |
| [Application lifecycle](04-application-lifecycle.md) | Sessions, jobs, CLI, adapters, MCP and native packaging | Application/integration |
| [Artifacts and compatibility](05-artifacts-compatibility.md) | Schemas, cache, reports, replay and release evidence | Integration/release |

“Must” denotes a proposed release requirement, not a claim of current support. Owners are engineering roles; assign maintainers when implementation starts. Existing requirement and suite IDs refer to the [MVP list](../mvp-feature-list.md) and [test plan](../test-plan.md).

## Settled scope

- Apache-2.0 project code; dependency licenses remain separate.
- Build [chisel-async](../chisel-async.md) first as an independently designed, standalone Chisel library. Its functional catalog and external tests precede the main simulator implementation; backend compatibility is qualified as integrations become available.
- Build RISCay-MCU second, using the library and a qualified external simulator; build Chiselator third against that independently checked corpus. chisel-async and RISCay-MCU have separate dedicated repositories, to be added by the project owner. Chiselator consumes pinned versions/contracts and does not host duplicate implementations.
- Physical chip implementation is step 4, after functional acceptance in Chiselator. All physical feasibility, synthesis, PDK, cell characterization, STA/SDF integration and manufacturing dependencies are deferred to that step; none gates steps 1–3.
- Chisel and SystemVerilog converge through a pinned, verified CIRCT subset. CIRCT is a family of dialects, not one automatically supported input format. The execution plan is scheduling/storage metadata, not a new HDL IR.
- Rust owns the runtime and application; C++ owns CIRCT/LLVM compilation and initial JIT integration behind versioned C interfaces.
- Native CPU releases target Windows x86-64, Linux x86-64 and macOS arm64. WSL is optional. GPU execution is an optional later backend, with no GPU dependency in the CPU package.
- No Yosys dependency in steps 1–3. The [step 4 synthesis decision](../chip-build-plan.md#synthesis-decision) is deferred, not an outstanding approval request. Do not add physical tools or physical qualification gates to the functional library, MCU or simulator scope.
- The first complete example is the [Raspberry Pi power-supervisor MCU](../async-mcu.md), built with chisel-async and simulated using Chiselator. It uses bundled-data handshakes, explicit primitive bindings and independent timekeeping. Small clocked and async fixtures come first to validate the engine. Ordinary clocked designs remain first-class.
- GF180MCU is a retained step 4 candidate to reassess, not a selected process or required PDK. Native simulation works without a physical build, PDK or ACT.

## Implementation gates

1. Complete chisel-async L0–L2: pin the functional toolchain, implement its contracts/component families, and qualify them against independent references and external simulators on the native targets. Small CIRCT representability probes may accompany library work; physical probes do not.
2. Build RISCay-MCU and qualify C0 externally with instruction/effect and power-policy references. Define functional memory, boot, wait/reset and diagnostics without selecting physical memory, pins or manufacturing-test hardware. A working Chiselator is not a dependency.
3. Pin the simulator compiler toolchain; execute scheduling/Arc and native packaging probes. Implement and validate the plan loader, real kernel ABI and session lifecycle. Run equivalent Chisel/SV clocked fixtures on all three native platforms.
4. Integrate the library's delay/process semantics, native async bindings and channel monitors. Run the already qualified MCU at S0 with its independent references; do not redefine primitive semantics inside the simulator.
5. Qualify source timing provenance and model-level delay/constraint fixtures in Chiselator, with hand-derived passing/failing outcomes and no PDK or physical tools. Optional ACT coordination cannot become a native execution dependency.
6. Complete adapters, CLI/MCP reports, replay and package tests against these same contracts. Add optimizations only with off-switch comparisons and measured benefit.
7. Only after step 3's functional acceptance, begin step 4 planning: select physical dependencies and schedule P1–P3 from the [deferred backlog](../chip-build-plan.md). Mapped-netlist/STA/SDF and physical claims require new qualification then.

Arc reuse, ACT control APIs, exact frontend coverage and GF180 cell availability remain experiments with explicit pass/fail evidence. An integration that fails its gate stays unsupported; it must not silently weaken semantics or introduce an unapproved dependency. The companion chip plan defines physical tool decisions separately from these five simulator contracts.
