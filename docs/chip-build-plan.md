# Step 4 physical chip implementation backlog

Deferred plan, October 5, 2026. The dependency order is **1. chisel-async → 2. RISCay-MCU → 3. Chiselator → 4. physical chip implementation**. Steps 1–3 build and verify functional designs using behavioral models and declared timing assumptions. Physical feasibility, implementation and tool qualification begin only in step 4. No physical probe, PDK, synthesis tool or fabricated chip is a prerequisite for steps 1–3.

This document retains the step 4 gaps for later planning, not an active implementation schedule. The [five simulator specifications](specs/README.md) own Chiselator semantics and interfaces; the [MCU plan](async-mcu.md) owns the Raspberry Pi supervisor behavior. RISCay-MCU is verified on an external simulator in step 2 and in Chiselator in step 3. No repository, physical toolchain or qualification result is created by this plan.

## Synthesis decision

**Deferred to step 4; no decision is needed now.** Revisit synthesis tools, PDK, physical cells, host requirements and their licenses when physical implementation starts. Yosys/ABC, CIRCT mapping and licensed alternatives below are research candidates, not selected dependencies or a pending approval request. Steps 1–3 remain independent of Yosys and physical toolchains. The previous question about a Yosys exception is superseded by this deferral; do not install or invoke physical tools under the current scope.

CIRCT does contain synthesis and technology mapping. Its published `circt-synth` description scopes the tool to combinational logic; current source also contains a technology mapper and optional ABC integration. The issue is qualification of a complete GF180 flow with preserved async state, memories and timing constraints, not the absence of synthesis in CIRCT. A `firtool` RTL export does not itself establish that flow. [CIRCT synthesis documentation](https://circt.llvm.org/docs/Tools/circt-synth/), [synthesis driver](https://github.com/llvm/circt/blob/main/tools/circt-synth/circt-synth.cpp), [technology mapper](https://github.com/llvm/circt/blob/main/lib/Dialect/Synth/Transforms/TechMapper.cpp).

Yosys is not logically mandatory: another qualified synthesis tool or a bounded CIRCT mapping flow could fill this role. Yosys/ABC was identified as an open-source candidate because it maps logic to cell libraries and is used by LibreLane's synthesis step. No route is selected for step 4 yet, and no default flow is assumed to safely implement async circuits. [Yosys mapping example](https://github.com/YosysHQ/yosys), [LibreLane synthesis](https://librelane.readthedocs.io/en/latest/reference/step_config_vars.html#synthesis).

At the start of step 4, revisit the no-Yosys policy and compare eligible routes on the same stage fixture. Standalone ABC, if used, is a separate dependency to record. A licensed synthesis route is a candidate only if access is available. If no route qualifies then, chip implementation remains unqualified; do not silently grow a general synthesis product or label emitted RTL tapeout-ready. This cannot retroactively block functional library/MCU/simulator releases.

## Product order and physical gates

| Gate | Deliverable and owner | Exit evidence |
| --- | --- | --- |
| L0 Library contracts | chisel-async: pinned JDK/Scala/Chisel/firtool, independent harness, channel/primitive descriptors and emitted SV | Native build probes; one primitive round trip; correct behavior and deliberate failures execute |
| L1 Bundled-data foundation | chisel-async: four-phase storage, composition, memory interface, reset and timing metadata | External event-simulator and independent reference tests; no Chiselator dependency |
| L2 Library functional completeness | chisel-async: declared two/four-phase, QDI, conversion, arbitration, clocked boundary and memory/I/O catalog | LIB-01–06 evidence by supported view/platform; a functional release does not imply physical qualification of every family |
| C0 RISCay-MCU reference release — step 2 | RISCay-MCU: RV32EC proposal, firmware, behavioral memory, functional diagnostics and Pi environment | MCU-01–04 pass on an existing simulator plus independent ISA/policy references; complete source/image/trace bundle; no physical architecture or cell mapping required |
| S0 Chiselator integration — step 3 | Chiselator: compiler/runtime and native primitive support | Established library and C0 workload pass on native CPU with the same observations and independent references |
| P1 Physical stage feasibility — step 4 only | Future target-pack/physical owner: representative bundled-data stage in a selected process | Revisit tools/cells first; then mapped/routed preservation, extracted timing and applicable DRC/LVS evidence |
| P2 Chip implementation — step 4 only | Future RISCay-MCU/physical owner: mapped full chip, pads, power grid, routed layout and test plan | PHY-01–05 below; reviewed area/timing/electrical/layout evidence; no unresolved required constraint |
| P3 Board and silicon — step 4 only | Future RISCay-MCU/board owner: package, PCB, instruments, bring-up and Pi qualification | PHY-06, MCU-05/06; measured behavior and power, with failures retained |

L0–L2 comprise step 1, C0 is step 2, and Chiselator including S0 is step 3. P1–P3 are subdivisions of step 4 and start after step 3's functional acceptance. No physical work runs in parallel as a required earlier gate. Small compiler representability probes belong to functional development and remain allowed. This is the chosen delivery order, not a claim that simulation technically requires fabrication.

Keep QDI completeness in the functional library catalog. Physical qualification of the primitives used by a future chip is deferred to step 4. Optional ACT and GPU execution do not gate the four-step sequence. Native clocked and async functional simulation remain required in step 3.

## Tools and responsibilities

The functional build, external simulation and firmware rows support steps 1–2. All physical-tool rows are retained only as a step 4 research inventory; choosing, installing, pinning or testing them is deferred. A future release matrix records tool revision, host, license, supported scope and evidence. An installed tool or accepted input file is not qualification.

| Work | Proposed tool or artifact | Owner and first probe |
| --- | --- | --- |
| Library build and RTL export | JDK, Scala, sbt, Chisel, firtool; versioned manifest and packaged SV resources | chisel-async L0: clean consumer elaboration on native Windows/Linux/macOS |
| Bootstrap RTL simulation | Icarus plus cocotb; Verilator on its demonstrated common subset | Library/MCU: latch, reset, delay, repeated-data and callback litmus tests |
| Firmware and architecture | GCC/binutils, ELF/ROM/link map; pinned Sail reference and applicable RISC-V architectural tests | RISCay-MCU: RV32E/C configuration, startup, MMIO and tiny-memory test adapter |
| Synthesis and cell mapping | Proposed Yosys/ABC route; bounded CIRCT route as alternative | RISCay-MCU physical scripts: P1 mapping and preservation evidence before adoption |
| Primitive characterization | ngspice with qualified GF180 transistor models; characterization scripts and reviewed circuit/layout views | Library target pack: PVT, slew/load, reset and pulse cases; independent validation cases |
| Place and route | OpenROAD; selected/customized LibreLane steps if their dependencies are permitted | Physical owner: import mapped stage, constrain layout, route, extract and audit |
| Timing | OpenSTA plus relative-timing adapter; netlist, Liberty, SPEF and scoped SDF | Target pack/physical owner: setup/hold/reset inequalities and endpoint completeness |
| Physical verification | Shuttle-approved PDK revision and DRC/LVS decks with their required engines, such as KLayout/Magic/Netgen where applicable | Physical owner: establish which exact decks/engines the chosen shuttle accepts |
| Layout/wave inspection | KLayout; GTKWave or another qualified FST/VCD viewer | Development convenience; headless reports remain sufficient for CI |
| Board and lab | Versioned schematic/PCB/BOM, programmable supply, oscilloscope, logic analyzer and current measurement | RISCay-MCU: safe power/reset/debug access and actual Pi lifecycle measurements |

Cocotb supports Icarus and Verilator, but qualify their different observation behavior. Verilator documents ignored `specify` blocks/timing checks, so it cannot be the sole authority for those checks. An Icarus functional or zero-delay gate run is also not proof of complete SDF coverage. [Cocotb adapters](https://docs.cocotb.org/en/stable/simulator_support.html), [Verilator timing limitations](https://verilator.org/guide/latest/languages.html#specify-blocks).

The official RISC-V architectural tests use a Sail reference; pin and qualify the chosen RV32E/C subset and execution environment. Split or adapt tests that exceed the production memory map, record the adaptation, and retain a separate exact-production-configuration firmware lane. Architectural agreement cannot establish async circuit timing. [RISC-V architectural tests](https://github.com/riscv/riscv-arch-test).

Use existing EDA tools through files/subprocesses. Do not add synthesis, SPICE, place-and-route or layout-checking engines to Chiselator. The wafer.space template is a candidate for pad/slot integration and selected flow scripts, not a turnkey async implementation. Audit its Nix/LibreLane/tool dependencies before executing it. [wafer.space template](https://github.com/wafer-space/gf180mcu-project-template).

## Async implementation and preservation

The following physical requirements are deferred step 4 notes. Steps 1–3 need semantic contracts, behavioral views and source identity/timing metadata only; they do not need the implementation, layout or characterized timing views described here.

The physical target pack supplies a contract, behavioral view, implementation netlist or macro, Liberty timing data, LEF/GDS where applicable, and SPICE/CDL connectivity for each required primitive. Hash related views together and record pin/power/reset correspondence. Select available standard cells first; missing C-elements, mutexes or delay structures require reviewed implementations, not guessed substitutes. Physical completeness is tracked per used primitive.

Partition the design explicitly into ordinary bundled-data combinational datapaths, preserved async state/control/delay structures, and declared clocked peripherals. Only the first class is eligible for unrestricted Boolean optimization within its validated boundaries. QDI logic is not automatically eligible: Boolean equivalence does not preserve monotonicity, hazards or completion assumptions.

For the proposed Yosys route, use qualified blackbox/structural views and mapping rules for protected primitives; keep their behavioral simulation bodies out of the synthesis source set. Preservation attributes are supported mechanisms, not proof of success. Audit cell identity, instance multiplicity, connectivity, reset and timing endpoints after elaboration, synthesis, placement and routing. Protect against removal/merging of delay stages, feedback rewriting, retiming and unintended clock transformations. Every final instance must resolve to an allowed physical implementation and a simulation model; permitted synthesis blackboxes must not become unimplemented chip blocks. [Yosys attributes](https://yosyshq.readthedocs.io/projects/yosys/en/latest/using_yosys/verilog.html).

Retain source-to-cell endpoint mappings independently of tool-generated names. Fail on missing or ambiguous protected endpoints. Review pass lists and default handling of unknown values rather than accepting the flow defaults. A PDK-specific binding converts each intentional delay into a physical structure; RTL `#delay` alone is never that structure.

Compare pre/post-mapping datapath behavior, primitive state transitions and end-to-end transactions. A bounded Boolean equivalence check, if qualified, strengthens datapath checking but does not prove analog or async hazard behavior. The entire flow must detect a deliberately removed delay element and an altered primitive/reset connection before P1 passes.

## Timing and characterization

Start P1 with a small stage containing real arithmetic, storage, request/acknowledge control, matched delay, reset and bounded backpressure. Keep a functional reference independent of the implementation. Route the fixture using the candidate physical views; extract interconnect before concluding that its data/control margin is sufficient.

For each legal operating corner and variation model, check that the earliest capture follows the latest protected data arrival by the required setup time plus stated margin. Check data stability through capture/hold separately. Include control pulse widths, reset recovery/removal where applicable, fanout/slew/load bounds and any declared fork assumptions. Any timing cuts used to analyze feedback must preserve explicit obligations; blanket false-path exceptions or unconstrained endpoints cannot count as passing.

Use OpenSTA path data with a separately tested relative-timing checker. Produce a report listing every obligation, source ID, mapped endpoints, corner, measured paths, margin and disposition. Pin extraction settings, libraries, units and constraints. Cross-check representative paths against transistor-level simulations, and compare the supported SDF dynamic checks to the same implementation. [OpenSTA inputs](https://github.com/parallaxsw/OpenSTA), [ngspice documentation](https://ngspice.sourceforge.io/docs.html).

Characterize applicable voltage/temperature/process conditions and input slew/output load, including reset and short-pulse cases. Use held-out cases to validate models and report their limits. Ideal digital arbitration does not establish physical metastability behavior, and a SPICE sweep does not prove a universal finite resolution time. Review contested input/mutex/synchronizer implementations separately. Measure silicon behavior later; do not infer fabrication yield or standby watts from passing randomized digital runs.

## Memory, firmware, boot and debug

Start with the [MCU plan's](async-mcu.md) provisional 2 KiB ROM and 256-byte RAM budgets. Measure compiled supervisor firmware, helpers, initialized data and bounded worst-case stack before fixing dimensions. Compare a narrow datapath with a full-width candidate using the same firmware and latency requirements; do not transplant the old 8-bit area estimate.

Select ROM implementation explicitly. A fixed image may map to logic or another qualified read-only structure; simulator `$readmemh` support does not imply a fabricated memory can load that file. Record image hash, address/byte ordering and the physical image-generation step. Runtime loading requires actual storage and a loader interface.

Compare a latch-based RAM implementation with a characterized SRAM macro plus local controller. The published GF180 256x8 macro is clocked; its wrapper must satisfy its startup, setup/hold, pulse and completion requirements while exposing the async memory contract. Local clocks are permitted, but neither a direct request-to-clock wire nor a fixed arbitrary response delay is qualified. Inspect actual model/layout files as well as the datasheet before choosing depth, ports and area. [GF180 SRAM](https://gf180mcu-pdk.readthedocs.io/en/latest/IPs/SRAM/gf180mcu_fd_ip_sram/cells/gf180mcu_fd_ip_sram__sram256x8m8wm1/gf180mcu_fd_ip_sram__sram256x8m8wm1.html).

Freeze the RISC-V execution environment, fault behavior and event-wait contract before RTL completion. A proposed minimal blocking MMIO wait needs pending-event, reset cancellation and watchdog semantics; architectural WFI instead needs the corresponding privileged/interrupt design. No simulator-only instruction may hide a missing hardware mechanism.

Specify a small externally accessible test/debug interface before pin budgeting. At minimum plan chip/image identification, retained fault/reset reason, controlled reset, memory test access and observation of execution/handshake progress. Decide between safe halt/readout and a simpler diagnostic mode at the architecture gate; do not imply full RISC-V Debug compliance. Define entry/exit so testing cannot inadvertently cut Pi power or violate a live handshake.

For first silicon, evaluate a ROM recovery monitor plus host-loaded RAM program against fixed ROM with readout-only diagnostics. Record ROM/RAM/pin/area cost, initialization, transfer integrity and recovery behavior. Freeze the choice before tapeout; optional loading is not assumed present in the current memory budget. A physical test clock is allowed and isolated from normal clockless execution.

## Manufacturing and board readiness

Define how to control and observe async state, test RAM/register storage and detect representative stuck-at, transition and interconnect faults. Evaluate explicit test access, component self-test and a qualified scan strategy; automatic synchronous scan insertion is not assumed correct. Include test circuitry in area, leakage, reset and timing checks. Declare measured/estimated fault coverage and remaining limitations rather than labeling a firmware boot comprehensive manufacturing test.

Select the exact PDK variant, cell and I/O libraries, metal stack, operating voltage and corners. Freeze pad/power connections, package/bond map, debug pins, POR/brownout source, decoupling and retained output state. Keep the Pi switch, timer and analog supervision external where already planned. Verify electrical compatibility, back-power paths, ESD/latch-up obligations and power sequencing with the selected pad cells and board. No uncharacterized analog function is inferred from digital RTL.

P2 includes placement/routing, power-grid and current-density checks, extracted timing, antenna/density/fill checks, and reviewed DRC/LVS using the accepted shuttle decks. Record exclusions and authorized waivers explicitly. Confirm slot/package constraints and current submission requirements before a tapeout decision; this plan makes no Run 3 deadline or area promise.

Prepare a board and bring-up procedure before manufacturing: current-limited first power, supply/reset measurements, chip ID/test access, memory/CPU diagnostics, then isolated load-switch tests, then the actual Pi. An FPGA or off-the-shelf MCU can validate firmware policy and board interfaces if useful, but is not evidence that an FPGA reproduces the async ASIC's timing. External clocks used by a prototype remain explicit.

## Tests and evidence

The [scientific test plan](test-plan.md) applies throughout. Keep input generation, oracles and comparators independent where claimed; prove checkers fire with known-bad controls. Preserve failures, incomplete coverage and timing exclusions. Simulator correctness, circuit timing and silicon power are different claims.

These physical suites refine MCU-06 and are all deferred to step 4; they are not Chiselator MVP release requirements. Assign physical maintainers/reviewers when step 4 starts, not as a prerequisite for creating the library or MCU repositories.

| Suite | Required evidence and negative control |
| --- | --- |
| PHY-01 Views and preservation | Cross-view pin/reset/identity checks and post-pass connectivity audit; missing model, removed delay or wrong reset binding fails |
| PHY-02 Relative timing | Routed stage and chip obligations with characterized min/max paths and corner coverage; short control, slow data and hold violation each fail the intended check |
| PHY-03 Memory and boot | Exact production memory/image behavior, startup and event/reset interactions; corrupted image, lost/duplicate response and invalid macro pulse fail |
| PHY-04 Test and physical implementation | Test access/fault coverage plus mapped/routed area, power integrity and DRC/LVS; disconnected test path and representative injected faults are detected |
| PHY-05 Reproducible handoff | Locked tool/PDK/model/image inputs rebuild required artifacts; wrong corner, stale SDF/SPEF or mismatched image is rejected |
| PHY-06 Board and silicon | Instrumented power/reset/debug and real Pi lifecycle/standby measurements; declared fault cases distinguish graceful shutdown from forced removal |

Retain RTL, contract manifest, firmware ELF/ROM/map, synthesis scripts/logs, cell allowlist and view hashes, mapped/routed netlists, constraints, LEF/DEF/GDS, Liberty/SPEF/SDF, SPICE/CDL where used, test coverage, DRC/LVS and power/timing reports, board revision and lab results. Reports cite exact input hashes. Define which artifacts are byte-reproducible and which metrics tolerate explicitly justified numerical variation.

MCU-01–04 must first pass externally at C0 and later pass in Chiselator at S0; use identical firmware and equivalent observation contracts. Different internal schedules need not produce identical delta counts. MCU-05/06 and PHY-01–06 run in step 4 for real-board and physical claims. Steps 1–3 check declared models and timing assumptions without claiming silicon accuracy.

## Repository and platform boundaries

chisel-async owns reusable components, primitive contracts, simulation resources and separately versioned target packs. RISCay-MCU owns chip RTL, firmware, board files, physical scripts, test access and application evidence. Chiselator consumes pinned source/artifact/fixture references. Do not duplicate library or MCU implementations in this repository, and do not create a fourth tool product just for orchestration.

Use machine-readable configuration and portable orchestration for steps 1–3: check functional tools, elaborate, test externally, build firmware, simulate in Chiselator and package functional evidence. Add map, route and physical timing/layout actions only in step 4. These are workflow requirements, not implemented CLI commands. Missing step 4 tools or artifacts cannot prevent steps 1–3 from building, testing or running.

Normal library development and Chiselator retain native Windows x86-64, Linux x86-64 and macOS arm64 goals. Qualify the physical toolchain's host environment independently; a pinned Linux worker/VM or supported local environment may run those jobs without turning WSL into evidence of native Windows simulation support. Keep PDK downloads, synthesis and licensed tools out of normal simulator installation. Project code remains Apache-2.0; inventory tool/PDK licenses and redistribution terms separately, including separately invoked GPL tools.

## First implementation backlog

1. **L0 build probe:** pin the library/export/simulator tuple, package one primitive and manifest, and execute independent positive/negative tests on the native targets.
2. **C0 RISCay-MCU:** decide the functional execution environment, memory request/response model, wait/reset behavior and software-visible diagnostics. Compile firmware, measure byte/stack use, and qualify MCU-01–04 externally after L2. Physical RAM macros, ROM fabrication, pin/power budgets and manufacturing test remain open for step 4.
3. **S0 Chiselator:** implement the simulator against the fixed library/MCU corpus and independent references; retain clocked support and qualify native execution. Model-level timing tests use declared delays and hand-derived expected outcomes without a PDK, STA tool or mapped chip.
4. **Deferred physical chip build:** after step 3, reopen dependencies and scope. Choose a synthesis/PDK route, re-evaluate the MCU's physical architecture and area, and schedule P1 stage feasibility, P2 chip implementation and P3 board/silicon qualification. Re-estimate staffing and dates then; no physical investigation timebox or Run 3 commitment is active now.

The step 4 backlog preserves identified gaps without making them current dependencies. Until that work is undertaken, report physical fit, manufacturability and silicon power as unverified; functional completion remains a separate, achievable milestone.
