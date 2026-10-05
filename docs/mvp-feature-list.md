# Simulator research and MVP feature list

Research and recommendations, updated October 5, 2026. This is a proposed first-team MVP for the [simulator proposal](simulator-proposal.md) and [software architecture](software-architecture.md), refined by the [five implementation specifications](specs/README.md). Every Chiselator feature below is planned, not implemented.

## Recommended MVP

Ship a local simulator that lets the team **install, run a small clocked or async design from Chisel or SV, reproduce a failure, inspect waves and channel reports, and automate the same workflow through CI or MCP**. The first complete application is the [Raspberry Pi power-supervisor MCU](async-mcu.md), built using chisel-async and simulated in Chiselator. Its independent ISA and power-policy references check ROM/RAM, GPIO, event/timekeeping and shutdown/wake behavior. Demonstrate behavioral, QDI, bundled-data, and wrapped clocked implementations of a selected block under shared transaction tests.

Keep the native executable self-contained for SV and already-elaborated RTL. Chisel elaboration still needs its Scala/JVM environment; Python is required only for Python tests, and ACT only for ACT-backed models. No hosted account or external C++ compilation is required for native built-in simulation.

The implementation uses the [hybrid Rust/C++ architecture](software-architecture.md#hybrid-implementation-language-contract). Rust and native compiler toolchains are build-time dependencies; users of the release binary need neither Cargo/rustc nor clang/g++ for built-in simulation. This language choice leaves the P0 feature scope unchanged.

The proposed cut uses small supported language subsets, behavioral delay/constraint fixtures, bounded adapters, and native CPU archives for Windows x86-64, Linux x86-64 and macOS arm64. Broader installer/registry formats follow later. The sequence is chisel-async, RISCay-MCU, Chiselator, then physical chip build. Steps 1–3 exclude Yosys and physical-tool dependencies. PDK/cell selection, synthesis and mapped-netlist/STA/SDF qualification are deferred to [step 4](chip-build-plan.md), with no current tool decision required.

The first deliverable is the independent [chisel-async library](chisel-async.md), built and externally tested before the main simulator. Its completeness catalog is broader than the initial native simulator subset. Library release status and per-backend support are separate; a native release must state any unqualified library protocols rather than imply whole-stack compatibility. This changes build order without renumbering the 32 simulator P0 requirements.

Three categories separate evidence from product decisions:

- **Baseline:** recurring capabilities in the reviewed simulator documentation.
- **Project-specific:** needed for this team's async/clocked comparison workflow even where not universal.
- **Emerging:** integrations such as MCP, whose value is supported by examples rather than established simulator-wide adoption.

Priorities are **P0: required for this MVP**, **P1: next release**, and **P2: later or explicitly outside the initial product**. These feature priorities are distinct from the physical P1–P3 gate names, all of which belong to step 4. P0 timing checks validate behavior under declared model assumptions without a physical flow. A thin P0 MCP adapter is included because agent-driven workflows are a stated requirement; advanced waveform reasoning is not.

## What the simulator landscape actually provides

This is a qualitative survey of seven simulator families, plus testbench and MCP tooling. It is not a statistical market census or an implementation benchmark. “Documented” means the primary source describes the feature; commercial marketing claims about speed are not adopted as measured facts. Online development documentation may describe capabilities absent from older packaged releases, so compatibility tests must pin versions.

| Tool or family | Documented capabilities relevant here | Product lesson |
| --- | --- | --- |
| Verilator | SV-to-C++/SystemC compilation, CLI, tracing, coverage, foreign interfaces; separate docs describe profiling and save/restore | A fast engine needs an integration and observability surface. [Overview](https://verilator.org/guide/latest/overview.html), [interfaces](https://verilator.org/guide/latest/connecting.html), [runtime](https://verilator.org/guide/latest/simulating.html) |
| Icarus Verilog | Source/filelist options, language selection, top/parameter selection, and an interactive VVP mode that can stop and inspect simulation | Support simple batch tests and inspection before a large GUI. [CLI](https://steveicarus.github.io/iverilog/usage/command_line_flags.html), [debugger](https://steveicarus.github.io/iverilog/usage/vvp_debug.html) |
| GHDL | Run limits, assertion policy, VPI/VHPI, waveform selection, hierarchy output, and SDF/VITAL annotation | Explicit termination, visibility, and compatibility limits are ordinary simulator features even across different HDLs. [Runtime documentation](https://ghdl.github.io/ghdl/using/Simulation.html) |
| ACT/actsim | Mixed abstraction, seeded delay randomization, arbitration choices, event stepping, signal/channel tracing, break/watch commands, and SDF delays | Async protocol inspection and reproducible timing exploration deserve native product treatment. [actsim documentation](https://avlsi.csl.yale.edu/act/doku.php?id=tools:actsim) |
| Synopsys VCS | Broad SV verification, coverage/debug integration, save/restore, direct interfaces, multicore execution, X propagation and metastability injection | These are useful breadth references, but building the entire verification suite is not an MVP. [VCS product documentation](https://www.synopsys.com/verification/simulation/vcs.html) |
| Cadence Xcelium | Multiple languages, UVM, incremental/parallel builds, multicore execution, low-power/X capabilities, and specialized apps | Broad language and enterprise verification support are separate investments. [Xcelium product documentation](https://www.cadence.com/en_US/home/tools/system-design-and-verification/simulation-and-testbench-verification/xcelium-simulator.html) |
| Siemens Questa One Sim | Mixed languages, SVA/PSL, code/functional coverage, integrated debugging, profiling and multicore compilation/simulation | Coverage and debug depth matter beyond raw cycles/s. [Questa fact sheet](https://resources.sw.siemens.com/en-US/fact-sheet-questa-one-sim/) |
| cocotb, a harness rather than an engine | Simulator adapters, build/test orchestration, and xUnit-compatible results | Reuse an existing Python test ecosystem and emit CI-readable results. [Build and results](https://docs.cocotb.org/en/stable/building.html), [simulator support](https://docs.cocotb.org/en/stable/simulator_support.html) |
| MCP ecosystem | Tools/resources and local stdio transport; projects such as wave-mcp expose waveform/hierarchy queries | Build structured access around the simulator, with a small integration surface. [MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools), [wave-mcp](https://github.com/Tencent/wave-mcp/blob/main/README.en.md) |

The common workflow is source configuration, compilation/elaboration, bounded execution, diagnostics, inspection, and repeatable regression. The exact HDL, API, coverage, and timing subsets vary substantially. Full four-state behavior, UVM, complete SDF, or checkpoint support must not be inferred from the word “simulator.”

### Distribution and MCP findings

Prebuilt installation is a baseline expectation, but delivery formats differ. Verilator documents package managers, source builds, and container workflows. Icarus documents prepackaged distributions and Windows/MSYS2 options. GHDL publishes platform-specific release assets. A single executable containing the compiler/runtime is our packaging choice, not a universal property of these tools. [Verilator installation](https://verilator.org/guide/latest/install.html), [Icarus installation](https://steveicarus.github.io/iverilog/usage/installation.html), [GHDL releases](https://github.com/ghdl/ghdl/releases).

MCP is an emerging integration surface in this sample, not something the reviewed engine documentation establishes as a universal built-in feature. Tencent's wave-mcp is a concrete primary-source example: it reads waveform/netlist artifacts and explicitly does not run the simulator. That supports producing interoperable artifacts instead of building an entire AI waveform debugger into our first release. Its claims were reviewed, not tested here. [wave-mcp workflow](https://github.com/Tencent/wave-mcp/blob/main/README.en.md).

## P0 execution and circuit features

The supported subset is pinned and machine-readable. The MVP is measured on small reference circuits and the team's first block, not on full Rocket, XiangShan, CVA6, or OpenTitan compatibility.

| ID | Feature | Minimum scope and acceptance test |
| --- | --- | --- |
| SIM-01 | Chisel and SystemVerilog inputs | Both import through CIRCT; equivalent counters and FIFOs pass the same observable checks. Unknown operations and unresolved modules fail at source locations. |
| SIM-02 | Clocked RTL | Combinational logic, registers, reset, memories with explicit collision behavior, both clock edges, and multiple domains; simultaneous-edge state-transfer fixture passes. |
| SIM-03 | Event and time semantics | Blocking/nonblocking ordering and re-entry, delta work, delayed transitions and supported waits; timestamped traces match the reference. |
| SIM-04 | Local and pausable clocks | Clock event sources can stop, stretch, and resume; reset while paused works and canceled edges never fire. |
| SIM-05 | Explicit value model | Two-state native execution with deterministic initialization and shadow initialized bits for primitives; never-reset reads fail. No claim of full X/Z support; ACT unknown crossings require a declared supported policy. |
| SIM-06 | Native compilation and cache | Quick JIT, optional optimized build, content-aware invalidation; a clean host runs supported SV without clang/g++ and a changed include invalidates its cache. |
| ASYNC-01 | chisel-async primitive integration | Integrate the independently released Chisel library and corresponding SV views for C-elements, latches, delays, mutex contracts and wrappers; validate semantic versions/manifest and require no handwritten C++ model for supported bindings. |
| ASYNC-02 | Typed channels and substitution | Four-phase bundled-data and dual-rail QDI contracts, transaction IDs, reset/backpressure; one behavioral/QDI/bundled/clocked block shares one scoreboard. |
| ASYNC-03 | Protocol diagnostics | Completion/spacer/dual-rail checks, invalid handshake sequence, stuck obligation and timeout distinction; injected protocol errors identify channel and transaction. |
| ASYNC-04 | Seeded delay experiments | Deterministic and bounded random delays, explicit transport/inertial policies, independent seed sweeps; failed seeds reproduce and pulse/cancellation fixtures pass. |
| ASYNC-05 | Optional ACT backend | Out-of-process adapter for one pinned ACT/actsim configuration; equal-time exchanges, backend failures and replay are tested. Native Chisel/SV works with ACT absent. |
| TIME-01 | Source timing intent and model-level validation | Preserve source annotations and model endpoints; check declared relative timing with independently derived passing/short-control/slow-data/hold fixtures. Missing assumptions or endpoints fail. No PDK, synthesis, STA or SDF required; implementation-derived qualification is step 4. |

These are project-specific extensions to the baseline workflow. No zero-delay or randomized RTL run is reported as physical timing signoff. If the ACT frontier experiment fails, retain the native MVP work but explicitly mark mixed ACT co-simulation incomplete; do not substitute transaction playback and call it co-simulation.

## P0 APIs and testbench integration

| ID | Feature | Minimum scope and acceptance test |
| --- | --- | --- |
| API-01 | Stable C ABI and C++ wrapper | Create/initialize, drive/read, settle, run-until, next-event, finish, diagnostics; opaque handles and capability/version queries. Two independent sessions cannot corrupt each other. |
| API-02 | Simple SV testbenches | `initial`, supported event controls/`wait`, `#delay`/tested `#0`, `$display`, `$finish`, `$fatal`, memory-file loading and wave system tasks; documented subset with positive and negative fixtures. |
| API-03 | cocotb adapter | One pinned version with timer, edge, read/write and read-only callbacks; one clocked and one handshake regression through normal simulator selection. DPI alone is insufficient. |
| API-04 | Chisel svsim adapter | One pinned Chisel version, normal test invocation after backend selection; reset/clock and primitive-library examples pass without rewriting test logic. |
| API-05 | Basic assertions and user checks | Supported immediate assertions plus channel checkers and harness assertions; severity/stop policy and expected-failure tests. Concurrent SVA breadth is deferred. |

Chisel svsim already has simulator backends; implementing another is a specific compatibility task, not a new Scala test framework. [Chisel svsim documentation](https://github.com/chipsalliance/chisel#chisel-sub-projects). API-03/API-04 are narrow tested adapters, not compatibility with every existing testbench or library version.

## P0 CLI and automation

| ID | Feature | Minimum scope and acceptance test |
| --- | --- | --- |
| CLI-01 | One-command workflow | `init`, `check`, `build`, `run`, `test`, `report`, `replay`, `view`, `doctor`, `capabilities`, and `mcp serve`; `--help` and version/build details work offline. |
| CLI-02 | Familiar source configuration | Filelists, include directories, defines, parameters, top selection, plusargs and `tool.toml`; explicit flags override project values and the resolved configuration is recorded. |
| CLI-03 | Bounded jobs and regression runner | Test filtering, independent seeds, `-j` worker budget, simulated-time and wall-time limits, delta/event budgets, fail-fast option and cancellation. A timeout cannot become PASS. |
| CLI-04 | Structured output and exit status | Human output plus versioned JSON; logs stay off JSON stdout. Distinguish test failure, unsupported/config error, infrastructure error, timeout and cancellation. |
| CLI-05 | Exact rerun and artifact management | Per-run directories, manifests, failed-seed list, build/input hashes and reproduction command; replay verifies identities and refuses a silently changed design. |

All commands are proposed interfaces. Example developer flow:

```sh
tool doctor
tool check -f rtl.f --top-module fifo_tb
tool run -f rtl.f --top-module fifo_tb --trace-fst
tool test --filter handshake --delays random --seeds 200 -j 8
tool report --run <run-id> --format json
tool replay --run <run-id> --seed 1187
tool view --run <run-id>
tool mcp serve --transport stdio --project .
```

`-j` runs independent jobs; reserve `--threads` for within-simulation parallelism when implemented. A canceled sweep records completed, failed and unexecuted cases separately. Replaying inputs is distinct from restoring a checkpoint. `view` opens an installed viewer or prints the artifact path; the simulator does not need its own waveform GUI.

## P0 debugging reports and coverage

| ID | Feature | Minimum scope and acceptance test |
| --- | --- | --- |
| OBS-01 | Waveforms and visibility | VCD/FST, signal selection, hierarchy/source mapping and observation coverage; known wave fixtures open in an existing viewer and preserve requested transitions. |
| OBS-02 | Failure diagnosis | Error code, source, instance, physical/delta/phase time, channel/transaction and bounded recent causal events; `explain` documents the error. |
| OBS-03 | Results and CI reports | Human summary, versioned JSON and JUnit/xUnit XML; assertion failure, crash, timeout and cancellation retain distinct outcomes. |
| OBS-04 | Channel and timing reports | Accepted/completed/aborted transactions, throughput, latency distribution, backpressure, obligations, source/model constraint mapping and check coverage; injected faults appear in machine-readable output. Physical evidence is marked not applicable in functional mode. |
| OBS-05 | Minimal coverage and profiling | User-defined hit counters, protocol-state/transition bins, observed signal transitions, compile-stage time, wall time, RSS and opt-in activation/event counters. Seed results merge only for compatible designs/configurations. |

Coverage terminology must stay precise. P0 protocol bins are functional coverage for declared channels; they are not full SV covergroups, source line/branch coverage, or proof of complete verification. Report eligible bins, hits, excluded items and observation scope. Signal transitions per transaction are a switching proxy, not watts or joules. Selected-interface counts cannot fairly rank styles with different unobserved internal logic.

### Required report bundle

| Artifact | Required contents |
| --- | --- |
| `manifest.json` | Schema/toolchain/model/input hashes, resolved config, value/observation modes, seeds, backend/corner identities, exact commands |
| `summary.json` | Outcome and reason, test counts, wall/simulated time, compile stages, cache result, memory metrics and links to artifacts |
| `results.xml` | One case per test/seed with failure versus error classification; partial sweeps remain partial |
| `diagnostics.jsonl` | Stable codes, severity, source/instance, logical time, transaction identity and replay references |
| `channels.json` and `channels.csv` | Latency/throughput with units and observation interval, completed/pending/aborted counts, backpressure and protocol bins |
| `timing.json` | Constraint IDs, source/model endpoints, declared delays/units, coverage, checked and unchecked cases, supported violations; physical input fields are not applicable until a step 4 capability is qualified |
| Selected `waves.fst` or `waves.vcd` | Captured signals and declared observation coverage; generated when requested |
| Optional `events.jsonl` / `profile.json` | Bounded causal trace or runtime/compiler counters; instrumentation settings included |

Use `null` or an explicit unsupported/unmeasured reason for missing metrics, never fabricated zeros. Async runs have no single global cycle count; report transactions and simulated time, with per-domain clock counts where useful. Normalize latency comparisons to the same acceptance/completion definition. A minimal offline HTML summary is P1 because text, JSON, CSV and existing wave viewers already support the MVP workflow.

## P0 installer and release features

| ID | Feature | Minimum scope and acceptance test |
| --- | --- | --- |
| DIST-01 | Self-contained native releases | Windows x86-64 ZIP, Linux x86-64 archive and macOS arm64 archive; embedded compiler/runtime and primitive assets. Native SV fixtures run without a host Rust/C++ compiler, Yosys or network access on each target. |
| DIST-02 | Portable core and optional integrations | Native path/process/JIT and semantic tests on all three targets; `doctor` distinguishes core requirements from optional ACT, GPU, Python, JVM and viewer dependencies. WSL is optional and cannot substitute for native Windows qualification. |
| DIST-03 | Maintainable installation | Checksums, dependency/license notices, release notes, documented system requirements, relocatable install/uninstall, cache compatibility and upgrade tests; package recipes build in CI. |

Native archives on all three targets are P0. MSI/winget, Homebrew, `.deb`/`.rpm`, OCI images, platform pip wheels and Nix packaging are P1 distribution expansion. Registry publication and signing are reported separately from tested downloadable packages.

Chisel users still need their JVM/Scala build, and cocotb users need Python. Custom C++/DPI source requires compilation; prebuilt compatible libraries do not. The core install includes no ACT linkage. Publish an optional ACT setup recipe and validated versions separately.

## P0 MCP integration

Use the same project resolution, job runner and report schemas as the CLI. MCP should translate structured requests into those operations. It must not parse human log text to decide whether a test passed or invent a separate scheduler.

| ID | Feature | Minimum scope and acceptance test |
| --- | --- | --- |
| MCP-01 | Embedded local stdio server | Capability negotiation, discovery, schema-checked tools and readable resources; launches from the same executable without Node/Python for MCP itself. Protocol stdout is clean; simulator output is captured separately. |
| MCP-02 | Bounded simulation jobs and results | Start/check/test, poll, cancel, inspect diagnostics and fetch bounded reports; a failed run yields the same status and artifact identities as the CLI. Disconnect/cancel behavior is explicit and tested. |

Proposed tool surface:

| Tool | Input | Result |
| --- | --- | --- |
| `inspect_project` | Project/config reference | Tops, capabilities, bindings, resolved feature support and setup issues |
| `start_job` | Mode `check`/`run`/`test`, project, test selection, seed policy, limits | Job ID, accepted configuration hash and initial status |
| `get_job` | Job ID and optional update cursor | Phase/status, measured progress, bounded recent diagnostics and artifact IDs |
| `cancel_job` | Job ID | Cancellation acknowledgement and eventual terminal state |
| `read_report` | Run ID, report kind and pagination/filter | Structured summary, failures, channel or timing results |
| `list_signals` | Compiled model/run ID, hierarchy filter and page | Available signal metadata and visibility limitations |

Expose manifests and bounded diagnostic/report content as MCP resources. Return artifact references for large binary waves; never dump a waveform into a tool response. Long runs return a job ID promptly, with subsequent calls retrieving status. Ordinary job APIs suffice initially; do not depend on an experimental protocol extension for task execution.

The server is local and project-scoped, with typed simulation options rather than an arbitrary shell-command tool. Job cancellation stops its associated worker processes and writes an incomplete-run manifest. A test failure is a valid job result; malformed requests or tool execution failures are separate errors. MCP logs go to stderr, with only protocol messages on stdout, as required by the transport. [MCP stdio](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports), [tools and schemas](https://modelcontextprotocol.io/specification/2025-11-25/server/tools), [resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources).

Defer remote HTTP hosting, arbitrary live signal forcing, automatic RTL edits, testbench generation, LLM calls inside the simulator, a chat UI, and deep waveform root-cause analysis. FST/VCD export leaves room to use a separate waveform MCP tool. MCP clients may help author tests, but authored tests do not become trusted passing evidence until executed.

## Features to defer deliberately

| Feature family | Priority | Why it waits |
| --- | --- | --- |
| Full four-state operators, native two-phase integration and richer metastability models | P1 | Two-phase belongs to chisel-async's functional catalog; native simulator support still needs its own qualification. Initialized-state checks bound the initial engine. |
| Source line/branch/toggle coverage, broader SVA, covergroups, UCIS interoperability | P1 | Valuable mainstream verification breadth; requires correct source mapping and sampling semantics |
| DPI-C subset and expanded Verilator C++ compatibility | P1 | C ABI and simple wrappers come first; context, purity and threading contracts need dedicated tests |
| Native checkpoints and restore | P1 | A seed replay is sufficient initially; correct snapshots must include queues, processes, monitors and random state |
| Interactive REPL, breakpoint/watch UI and bounded waveform queries | P1 | API stepping/inspection and failure traces support early debug; full source debug is another subsystem |
| HTML report, report comparison, SAIF export and mapped area summaries | P1 | Add once reliable JSON/channel/timing data exist; no energy estimate without a physical model |
| Offline PGO, activity-aware partitioning, code sharing and within-run threading | P1 | Preserve extension points and baseline counters now; correctness and reproducible benchmarks precede optimization |
| Broader platform installers and package registries | P1 | Expand the tested release matrix instead of claiming every package works on day one |
| Mapped libraries/STA/SDF integration | Deferred step 4 | Requires later physical dependency and artifact qualification; no mapped fixture gates the functional MVP |
| Broader full-chip SV coverage and ACT boundary patterns | P1/P2 | Expand from the functional MVP's explicitly supported subset |
| UVM, classes, constraints solver, full concurrent assertions, VHDL/SystemC frontend | P2 | These would turn a targeted simulator into several additional language/verification products |
| Built-in waveform IDE, enterprise coverage database, GUI regression farm, cloud accounts | P2 | Existing tools plus portable artifacts cover the team's early workflow |
| UPF, analog/mixed-signal, fault certification and hardware acceleration | P2 | Separate semantics, infrastructure and validation requirements |
| Distributed async execution and coordinated ACT checkpoints | P2 | Cross-engine causality and serialization are substantial correctness projects |

## MVP release gates and build order

The companion [simulator test plan](test-plan.md) maps all P0 requirements to concrete suites and defines oracle selection, replay, durability, CI, and release evidence.

The MVP remains a substantial compiler/runtime project. Feature rows are acceptance contracts, not equally sized tickets or promises that familiar simulator features are cheap.

1. **Build chisel-async first:** complete L0–L2 library contracts, components, external views and independent qualification. Pin the library toolchain and preserve CIRCT/RTL timing identities before committing its API.
2. **Build RISCay-MCU second:** finish C0 firmware, RTL and independent ISA/power-policy qualification on an existing simulator using behavioral primitive/memory views. No physical feasibility gate applies.
3. **Prove native semantics:** begin Chiselator; pin CIRCT/Arc and ACT versions, finish bounded scheduling/frontier experiments using the established corpus and publish supported operations.
4. **Deliver the common workflow:** native clocked Chisel/SV, C API, minimal SV tests, CLI/jobs/cache, JSON results, waves and compiler-free release binary.
5. **Integrate the async library and MCU:** channel substitution, native primitive bindings, optional ACT-backed QDI, randomized tests, pausable clocks and protocol reports; qualify the existing RISCay-MCU workload in Chiselator at S0.
6. **Qualify modeled timing:** annotation provenance, declared delay assumptions and relative-constraint checks with passing and deliberately failing behavioral fixtures. Mapped-library/SDF/STA work belongs to step 4 after the simulator.
7. **Finish adapters and release:** cocotb/svsim, thin MCP, packaging, documentation and reproducibility checks. Adapter work can proceed once the API is stable.

| Gate | Required evidence |
| --- | --- |
| Clean install | Each native archive runs SV fixtures without rustc, clang/g++, ACT, Yosys or network; real Windows/Linux/macOS install and semantic tests pass |
| Dual-language clocked correctness | Counter, memory, reset, simultaneous clocks and paused-clock fixtures pass reference/external comparisons |
| Mixed-style usefulness | One block substituted among behavioral, QDI, bundled and wrapped synchronous forms passes the same transaction tests under backpressure |
| Complete async application | chisel-async Pi supervisor MCU runs in Chiselator and passes MCU-01–04: independent retirement/effect and power-policy traces, variable latency/backpressure, reset, stale acknowledgement and timeout cases. Real-board compatibility and physical fit have separate MCU-05/06 gates. |
| Real failure detection | Never-reset state, illegal handshake, lost annotation, zero-time nonconvergence, and violations of declared model timing produce expected diagnostics |
| Reproduction | Selected failing seeds replay with matching artifact identities; changed inputs are rejected as exact replay |
| Harness parity | C++/SV/cocotb/svsim see consistent defined observation points and outcomes |
| Automation parity | CLI and MCP return equivalent reports; cancellation, crash and timeout never become PASS |
| Evidence quality | Profiling build runs in CI; every supported feature has positive/negative tests; no unexplained differential mismatch in the release corpus |

Do not gate the first-team MVP on beating GSIM. Publish reproducible baseline throughput, compile latency and memory, with correct results and declared observation modes. The broader proposal's comparative v1 performance targets remain later gates. A product that finds the team's async bugs and works in daily tests is a useful MVP even before it wins a throughput benchmark.
