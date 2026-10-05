# chisel-async library architecture

Draft, October 5, 2026. **chisel-async is the first product to build.** It is an independently designed Apache-2.0 Chisel library for asynchronous circuits, with versioned simulation, compiler and implementation contracts. It evolves the ideas demonstrated by existing async Chisel projects; it is not a renamed copy, a source fork, or a promise of drop-in API compatibility. No library code or qualification results exist yet.

This document extends [async model specification 03](specs/03-async-model-contracts.md). It defines library scope and build order; the [five specifications](specs/README.md) continue to own simulator semantics and interfaces. The first complete chip example remains the minimal async MCU. Library components and example stages are earlier deliverables, not substitutes for that application.

## Product boundaries and reuse

Use the artifact name `chisel-async` and Scala namespace `chiselasync`. Develop it in its own dedicated repository, which the project owner will add when needed. That repository owns library source, bundled SV views, build configuration, independent tests, documentation and releases. It must not depend on Rust, the Chiselator executable, ACT, a GPU, a PDK or Yosys. Chiselator consumes pinned artifacts/contract fixtures rather than maintaining a second library source tree. Repository URL and package publication coordinates are assigned when the repository is added; these names do not claim that a package namespace has been reserved.

Study [ASYNC-Chisel](https://github.com/Jilin-Zhang/ASYNC-Chisel) for its controller/channel approach and [chisel-click](https://github.com/KasperHesse/chisel-click) for generic bundled-data composition. Design our API and implementation from explicit contracts. Keep a provenance record for concepts, papers and any later reused material; preserve notices and review actual licenses before incorporating third-party code. Do not copy their implementation and merely rename symbols, or claim independent verification using a model derived from the same copied implementation.

The intended evolution is broader than updated dependency versions:

- Generic typed channels with distinct protocol/encoding types, explicit initialization and reset behavior.
- Composable control and storage components, not only a controller generator.
- Four-phase and two-phase bundled data, plus a defined QDI family and clocked boundaries.
- Versioned primitive identity, timing/provenance metadata and independently qualified execution views.
- Native platform builds, documented support limits, reproducible tests and compatibility evidence.

## Public vocabulary and completeness target

The names below are proposed API families, not implemented symbols. Library completeness means the catalog is implemented and qualified for its declared modes, with no silent substitution between protocols. It does not mean every async circuit style, every SV construct, or every physical process is supported.

| Family | Public concepts | Required contract |
| --- | --- | --- |
| Structure | `AsyncModule`, explicit reset and local clock ports | Thin `RawModule`-based organization; no hidden global clock |
| Channels | `FourPhase[T]`, `TwoPhase[T]`, `DualRail[T]` | Producer/consumer direction, encoding, acceptance, completion and stable-data interval |
| Storage | `Stage`, `Buffer`, bounded `Fifo`, initialized token source | Capacity, initial tokens, backpressure, ordering and reset effects |
| Composition | `Fork`, `Join`, `Select`, `Merge`, `Arbiter` | Exactly-once delivery; all-consumer completion for fork; operand pairing for join; exclusive merge versus contested arbitration |
| Datapath | Pure combinational transform and guarded stage | Payload shape/width, source-to-capture timing obligation, storage separated from computation |
| Primitives | C-element, latch, delay line, mutex, completion detector | Explicit state/initialization, permitted transitions, delay/effect policy and model version |
| Protocol conversion | Four/two-phase and bundled/dual-rail adapters | Explicit buffering, encoding, reset phase and timing assumptions; no implicit wire casts |
| Clocked integration | Clocked endpoint wrappers, synchronizer and CDC adapters | Named domains, reset sequencing, sampling/latency and CDC assumptions |
| Memory and I/O | Request/response memory ports, ROM/RAM models, GPIO adapters | Acceptance/commit points, response order, backpressure, masks, range and collision behavior |
| Timing and provenance | Launch, data-valid, capture, setup/hold and reset constraints | Stable IDs and checked endpoint mappings; functional versus timed mode explicit |
| Verification | Channel monitors, transaction drivers, scoreboards and trace hooks | Required-activity evidence, failures/replay, no reliance on periodic sampling |

Support common synthesizable payload types: sized `UInt`, `SInt`, `Bool`, nested `Bundle` and `Vec` of supported fields. Flattening and serialization order are versioned and tested. Reject ambiguous widths and unsupported leaves such as analog/clock payloads unless a later explicit contract supports them. Distinguish payload packing from protocol encoding.

Protocol types prevent accidental two/four-phase wiring where possible; elaboration validates what Scala types cannot establish. A width-correct connection does not prove a timing-safe connection. `Decoupled`/ready-valid components require an explicit clocked bridge. Ordinary Chisel arithmetic remains available inside datapaths; users do not rewrite addition or multiplexing in a separate language.

Start with the existing four-phase contract: one outstanding transaction per channel, request/acknowledge return to zero, and conservative data hold through return to idle. Two-phase channels define initial request/acknowledge parity, one transfer per new request transition, and matching acknowledgement. Conversion must preserve exactly-once transactions across reset; renaming wires is insufficient.

For QDI, define dual-rail valid/spacer rules, completion detection and the allowed transitions of the logic family. Encoding an arbitrary binary combinational circuit at its outputs does not establish QDI behavior. Monotonicity, completion, fork assumptions and required gate-level observations remain explicit. Larger arithmetic cells and additional encodings can extend the catalog after this family is qualified.

## Primitive and compiler contract

Use Chisel `ExtModule` declarations for primitives whose state/delay semantics must remain explicit. These have no implicit clock/reset, and Chisel leaves their behavioral implementation external. Native Chisel composition uses those declarations plus normal logic. [Chisel external modules](https://www.chisel-lang.org/docs/explanations/blackboxes).

Every primitive descriptor carries a namespace/name, semantic major/minor version, parameter schema, port widths/directions, reset/initialization policy, effects, required timing information and available views. An instance also has a stable semantic ID and source/hierarchy reference. Model identity must not depend only on a mutable emitted module name.

| View | Purpose | Qualification boundary |
| --- | --- | --- |
| Semantic contract | Human specification, state table and independent expected traces | Reviewed independently of implementation |
| SV simulation model | Run generated designs in a qualified external event simulator | Tested syntax, event/reset/delay behavior and observation scope |
| Chiselator model binding | Bind the same declared primitive to native runtime semantics | Future native-versus-external/reference trace qualification |
| Physical implementation binding | Select characterized cell/macro/netlist views | Process-specific evidence; simulation `#delay` is not an implementation |

These views share interface/identity schemas but not a single behavioral implementation used as its own oracle. Missing required bindings fail. No unresolved primitive becomes zero, an ideal wire, or an arbitrary initialized value. Avoid both a duplicated SV body and native binding executing the same stateful effect; compilation selects one authorized view per instance.

Export a versioned design-contract manifest alongside emitted RTL. It includes channel/primitive instances, payload layouts, reset policies and timing endpoint references. The CIRCT path must preserve or explicitly translate these identities through elaboration, normalization, inlining and optimization. Validate the exported manifest against retained IR/RTL endpoints. An output file that parses but loses a required constraint fails compatibility.

Do not introduce a replacement HDL IR or require a fork of Chisel to begin. Qualify the pinned Chisel/firtool annotation or sidecar mapping mechanism with a small round-trip fixture first. When SystemVerilog enters through circt-verilog/slang, resolve equivalent primitive declarations and the same contract manifest; both language paths must reach equivalent verified circuit semantics.

## Timing and reset discipline

Attach a matched-delay requirement to its protected data path and capture endpoint, rather than expose an unexplained delay number as proof of correctness. Distinguish zero-delay functional, fixed-delay, randomized-delay and implementation-annotated modes in every result. State the transport/inertial policy and pulse handling for each delay primitive.

Reset is part of each component's public behavior. Specify initial tokens, empty/full capacity, channel parity/phase, pending-event cancellation and treatment of accepted effects. Composed reset must not create phantom requests or silently roll back committed memory writes. Test assertion and release at every relevant protocol phase.

GF180MCU remains a candidate for deferred step 4. The library's portable functional release requires semantic contracts and behavioral views, not physical cells or a PDK. Physical bindings, characterization and synthesis-tool decisions are retained in the [step 4 backlog](chip-build-plan.md); no physical stage probe precedes the library, MCU or simulator. No ideal mutex/synchronizer model establishes analog metastability behavior. Normal library builds and functional tests remain independent of synthesis tools.

## Compatibility throughout the stack

Compatibility is a matrix of tested versions and semantics, not a blanket promise. Each release records exact Chisel, Scala, JDK, firtool/CIRCT, simulator and adapter versions. Select the initial tuple in the first build probe; never depend on a floating `latest`. Native Windows x86-64, Linux x86-64 and macOS arm64 are the core build/test targets.

| Boundary | Required evidence | Initial treatment |
| --- | --- | --- |
| Scala/Chisel API | Compile consumer examples; elaborate valid combinations and reject invalid connections/parameters | Required before library alpha |
| Chisel to CIRCT/RTL | Primitive identity, widths, source maps and timing endpoints survive emission | Required before library alpha |
| Standalone SV | External harness uses the same public modules/contracts without Scala | Required before library functional release |
| External simulators | Event-driven traces on the qualified async subset; Verilator additionally on its demonstrated overlap | Required independently of Chiselator; publish each tool's exclusions |
| Chiselator CPU | Native bindings match reference/external observations and schema negotiation | Designed now; required when native backend support is advertised |
| cocotb and svsim | Pin versions; test async drive/observe and ordinary clocked wrappers | cocotb external lane first; no claim that every svsim backend supports clockless execution |
| ACT | Explicit contract/binding and safe event frontier | Optional later qualification, not a library dependency |
| GPU | Eligibility and identical required observations with independent session state | Optional later qualification; no device-specific types in the library API |
| Physical library/SDF/STA | Characterized views, endpoint provenance and passing/failing timing fixtures | Separate target pack; no physical accuracy claim from functional tests |

Pure Chisel elaboration and contract tests must run without a simulator. Event tests need an external engine whose required timing features actually execute on the target platform; an engine that only accepts syntax is insufficient. Bundle external simulation resources in the library artifact so consumers do not fetch ad hoc source files. Source consumption, local artifact publication/installation and clean consumer builds are release tests. Publish native-platform gaps honestly rather than counting WSL as native Windows.

Version Scala API, primitive semantics and serialized metadata separately. Before 1.0, breaking changes require migration notes and fixture updates. A 1.0 claim requires an explicit supported catalog, backward-compatibility policy and tested consumers. Internal simulator APIs never leak into public channel types. An upstream dependency upgrade is a candidate lane until the compatibility corpus passes.

## Scientific validation of the library

Apply the [scientific test plan](test-plan.md#scientific-method-and-limits-of-claims) before optimizing or using the library to validate Chiselator. Hand-derived primitive cases and a small independent reference must precede production model agreement. Chiselator is never the only oracle for the library that defines its own built-in models.

Each catalog entry needs positive, boundary and misuse fixtures; explicit required activity; a known-bad control caught for the intended reason; replay; and a support matrix. Exhaust small state/input spaces and bounded handshake orders. Cover data held under backpressure, repeated equal payloads, reset during each phase, initialized tokens, fork acknowledgement ordering, join pairing, FIFO full/empty, contention, and memory effect points. Type/elaboration rejection and runtime protocol rejection are distinct tests.

Test both generated and handwritten SV wrappers against independently specified transactions. Include structured payload round trips and widths around machine-word boundaries. Faults include dropped acknowledgement, premature data change, duplicate token, short control delay, stale event after reset and lost timing annotation. A compiling library with only golden RTL text tests is not functionally qualified.

The initial library suites are LIB-01 API/elaboration, LIB-02 primitive behavior, LIB-03 composition/protocols, LIB-04 timing/provenance, LIB-05 toolchain/platform compatibility and LIB-06 consumer packaging. They extend the simulator suites without claiming that currently nonexistent backend lanes already pass.

## Library first delivery sequence

| Gate | Deliverable | Exit evidence |
| --- | --- | --- |
| L0 Contracts and build | Independent project, pinned toolchain, typed channel draft, primitive/manifest schema, reference/test harness | Native build probes, one emitted primitive and contract round trip; positive and deliberately bad tests execute |
| L1 Bundled-data foundation | Four-phase channels, state/delay primitives, stage/buffer/FIFO, fork/join/routing and reset discipline | External event traces and independent scoreboards pass; no Chiselator dependency |
| L2 Functional library completeness | Two-phase/converters, qualified QDI family, arbitration, clocked/CDC interfaces, memory/I/O adapters, documentation and examples | Declared catalog coverage, native platform/consumer tests and scientific controls pass; unresolved rows cannot be called complete |
| C0 Complete application | [RISCay-MCU](async-mcu.md) in its own repository, built from pinned chisel-async contracts and first run on an external simulator | Independent ISA/effect and power-policy traces under reset, backpressure, variable latency and Pi fault scenarios; no Chiselator dependency |
| S0 Simulator integration | CIRCT/Arc experiments and native primitive bindings using the established library and RISCay-MCU corpus | CPU runtime preserves the already defined semantics; native/external/reference comparisons agree |
| Step 4 deferred physical work | Later choose dependencies, then perform P1 stage feasibility and P2/P3 chip/board qualification | Physical suites and actual board measurements qualify only their declared claims; no prerequisite for L0–L2, C0 or S0 |

The four-step order is L0–L2 library, C0 RISCay-MCU, Chiselator including S0, then physical chip implementation. All P1–P3 work and physical-tool decisions are deferred to step 4. Small compiler feasibility probes needed to keep functional library contracts representable are allowed earlier. The complete MCU is first verified externally, then used to qualify Chiselator. Optional ACT/GPU integrations have separate later gates. See the [cross-project delivery plan](chip-build-plan.md#product-order-and-physical-gates).

Completeness is tracked by catalog row and view, with states planned, implemented, qualified or explicitly unsupported. Do not use empty stubs, passing compile-only tests or skipped platform jobs to label a row qualified. Re-estimate staffing after L0; earlier simulator estimates did not separately budget this expanded library product. Prefer finishing a coherent, tested family over publishing an API surface that promises unsupported behavior.
