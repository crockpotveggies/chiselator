# Chiselator

Chiselator is the simulator in an open-source chip development stack. The delivery and dependency order is:

1. **chisel-async:** build and independently test the functional library.
2. **RISCay-MCU:** build the RISC-V MCU with that library and verify it on an existing simulator.
3. **Chiselator:** build our simulator and run the established library/MCU corpus.
4. **Physical chip build:** later select and qualify synthesis, PDK, cell, layout and manufacturing dependencies.

Steps 1–3 require no physical chip build, PDK or synthesis tool. Step 4 begins after functional acceptance in Chiselator; its dependencies will be addressed then. The simulator supports comparing QDI, bundled-data, and GALS implementations while retaining first-class support for ordinary clocked Chisel and SystemVerilog designs.

The proposed architecture uses typed channels to exchange block implementations under shared tests, CIRCT-based compiled execution, an optional ACT/actsim process for QDI models, and explicit event semantics for both local clocks and asynchronous logic. Initial bundled-data verification checks behavior under declared timing assumptions; implementation-derived netlist/SDF and static timing validation are deferred to step 4.

The implementation plan combines a Rust runtime and application with a C++ CIRCT/LLVM compiler component behind a versioned C interface. Generated simulation kernels execute directly; built-in simulation does not require an installed Rust or C++ compiler.

**Status:** design proposal. No simulator or executable test suite is implemented yet.

**Build first: [chisel-async](docs/chisel-async.md).** Our independently designed Apache-2.0 Chisel async library will establish typed protocols, composable components, primitive/timing contracts and external-simulator tests before the main Chiselator implementation. Its completeness catalog covers bundled data, two-phase and four-phase handshakes, a defined QDI family, clocked boundaries and memory/I/O. Compatibility is qualified separately at each stack boundary.

The [chisel-async implementation plan](docs/chisel-async-implementation-plan.md) specifies the modern Chisel API/toolchain baseline, improvements grounded in the original ASYNC-Chisel source, repository structure, component contracts, native CI and eleven work packages through the RISCay-MCU handoff. The dedicated [chisel-async repository](https://github.com/BiscutLabs/chisel-async) now implements typed four-phase channels, behavioral and structural functional storage, checked compiler export, independent functional/timing tests and clean consumer checks. Windows/Linux CI passes the timing/compiler baseline; the structural stage also passes on native Windows and WSL. macOS is explicitly deferred. Independent contract review remains before L0 sign-off; the library owns exact evidence and current status.

The first application is [RISCay-MCU](docs/async-mcu.md), a Raspberry Pi power supervisor: a clockless RISC-V core (proposed RV32EC) built with chisel-async, first verified on an existing simulator and later simulated in Chiselator. It has provisional 2 KiB program storage and 256 bytes RAM, independent timekeeping and external power-switch control. Firmware size and physical fit must be remeasured for RISC-V. chisel-async and RISCay-MCU are developed in separate repositories; Chiselator integrates pinned versions and qualification fixtures.

The [step 4 backlog](docs/chip-build-plan.md) retains synthesis, physical async cells, memory implementation, hardware debug/test, physical timing, manufacturing and board bring-up work for later. There is no active physical feasibility probe or pending Yosys decision. Tool and process candidates are deferred research, not dependencies of steps 1–3.

The [five implementation specifications](docs/specs/README.md) define execution semantics, the compiler/runtime interface, async model contracts, application lifecycle, and artifacts/compatibility. The first complete example will be a minimal Chisel async MCU. Native CPU releases target Windows x86-64, Linux x86-64 and macOS arm64, with no Yosys dependency. GF180MCU is a physical-process candidate to qualify separately from functional simulation.

Read the [simulator design proposal](docs/simulator-proposal.md) for the review summary, architecture, clocked and async semantics, one-command user experience, validation gates, and staffing estimates.

The [software architecture](docs/software-architecture.md) defines component ownership, the CIRCT-to-runtime boundary, execution-plan records, scheduler and kernel contracts, API sketches, repository layout, and the first implementation work packages. It includes CPU execution, optional GPU backends and independent simulation batches under shared semantic contracts; GPU support remains experimental and is not required for the MVP.

The researched [MVP feature list](docs/mvp-feature-list.md) compares established simulator capabilities and prioritizes execution, APIs, CLI, reports, installer binaries, MCP integration, and release acceptance tests. It proposes a smaller first-team release within the broader roadmap.

The [simulator test plan](docs/test-plan.md) defines accuracy contracts, independent reference comparisons, deterministic replay, async timing checks, fuzzing, endurance and compatibility tests, and CI release gates for every P0 feature.

Its [scientific qualification rules](docs/test-plan.md#scientific-method-and-limits-of-claims) require falsifiable claims, independent oracles, demonstrated checker activity, known-bad controls, frozen evaluation campaigns and honest uncertainty. Digital correctness, physical timing validity and performance receive separate evidence; passing tests alone cannot establish silicon accuracy.

The first milestones build and independently qualify chisel-async, then RISCay-MCU on an external simulator. Chiselator work then timeboxes the Arc scheduling experiment and tests the ACT process boundary using that established corpus. M1 includes a self-contained simulator executable and familiar testbench adapters; the ordinary SV/Chisel path must work without ACT or an external C++ compiler. Beating GSIM is a later synchronous optimization goal.

Chiselator is licensed under the [Apache License 2.0](LICENSE). Dependencies retain their own licenses. The final project name remains a review decision.
