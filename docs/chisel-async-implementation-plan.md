# chisel-async implementation plan

Planning baseline, October 5, 2026. Build an independently designed Apache-2.0 library that lets Chisel users compose asynchronous hardware, emit portable SystemVerilog, and verify it before Chiselator exists. [BiscutLabs/chisel-async](https://github.com/BiscutLabs/chisel-async) owns implementation and exact evidence for its behavioral, timing/compiler and clean-consumer foundation. External review identified an internal delay race in the custom structural controller; it is withdrawn and its counterexample is retained. The published long-hold replacement and first cross-encoding architecture probes have bounded digital evidence. Optimized read-probe export and ChiselSim bridge tests now have bounded development evidence. L0 still requires broader qualification and independent review. Zero-delay successes alone do not establish suitability for catalog composition.

**Review-driven sequencing change:** before CA-06, compare published controllers under their actual capacity, handshake and delay assumptions. Validate logical token channels separately from physical encodings, type-changing transforms and explicit timing policies using minimal bundled, dual-rail completion/storage and clocked Decoupled bridge examples. Pull these narrow CA-08/09 experiments forward; the full QDI/application catalog retains its later scope. Require checked observation and timing-intent preservation under optimization/deduplication; do not infer arbitrary synthesis preservation from compiler export.

**Published controller and architecture probes implemented:** the library's [fully decoupled long-hold stage](https://github.com/BiscutLabs/chisel-async/blob/main/docs/long-hold-controller.md) now declares separate min/max/model delays for each control cell, data and latch; guards use worst-case bounds, and sweep overrides are checked against them. The [logical-channel probes](https://github.com/BiscutLabs/chisel-async/blob/main/docs/logical-channels.md) bind shared payload/reset intent to bundled, dual-rail RTZ and Decoupled interfaces, with a completion/storage example and explicit-clock bridge pair. Tests exercise encoding-specific commit/hold rules, backpressure, reset and activated faults. `python tools/qualify.py` sets up and runs the complete campaign, including independent published-JAR consumers, and is also the CI entry point.

**Optimized export and Scala simulation implemented:** [read-probe export](https://github.com/BiscutLabs/chisel-async/blob/main/docs/optimized-export-and-simulation.md) removes hardware observation ports, adds passive timing-marker instances, and enables release optimization/deduplication by default. Eight replicated two-stage paths share six hardware definitions versus 25 in debug, with independent traffic and mapping corruption checks. Five native Scala simulation cases exercise clocked bridges, wide transport and payload faults, also against the published JAR. Next: independent contract/export review and a frozen release campaign. L0 and CA-06 remain gated; no physical qualification is claimed.

**October 5 platform decision:** scope the current L0 attempt to Windows and Linux and defer macOS qualification. WSL is supplementary Linux-under-WSL evidence, not native Windows evidence. The three-platform release target below remains the long-term requirement; macOS has no passing qualification claim.

The delivery order remains **chisel-async → RISCay-MCU → Chiselator → physical chip implementation**. The dedicated chisel-async repository now owns implementation and references the versioned original of this plan. Retain this document as the stack-level planning baseline rather than duplicate library status here. No PDK, synthesis tool, Yosys, ACT, GPU or physical chip is required for the first three steps. Physical bindings and physical-tool decisions remain in the [step 4 backlog](chip-build-plan.md).

## Lessons from the original library

The source audit uses ASYNC-Chisel commit [`1af2cf4f621aa77657cab25858cc4a038a7291d6`](https://github.com/Jilin-Zhang/ASYNC-Chisel/tree/1af2cf4f621aa77657cab25858cc4a038a7291d6). These are observations about that revision, not claims about every project using its ideas. Preserve the useful ideas of bundled handshake ports, configurable controllers, local firing events and compositional examples. The implementation below is an independent evolution, with no drop-in compatibility promise.

| Observed source behavior | Limitation for our stack | Planned response |
| --- | --- | --- |
| [build.sbt](https://github.com/Jilin-Zhang/ASYNC-Chisel/blob/1af2cf4f621aa77657cab25858cc4a038a7291d6/build.sbt) pins Chisel 3.5.4, Scala 2.13.8 and chiseltest 0.5.4. | Its dependency/API choices do not establish compatibility with current Chisel/CIRCT. | Qualify a current compiler tuple, current APIs, clean consumers and upgrade lanes. |
| [AsyncLib_ACG.scala](https://github.com/Jilin-Zhang/ASYNC-Chisel/blob/1af2cf4f621aa77657cab25858cc4a038a7291d6/src/main/scala/tool/AsyncLib_ACG.scala) uses `Map[String, Any]`, casts and integer flags for controller configuration; `HS_Data` carries a width-parameterized `UInt`. | Misspelled keys and invalid combinations are difficult to diagnose; payload and protocol intent are weakly represented. | Immutable typed configurations, exact validation, generic payloads and distinct protocol APIs. |
| The same controller extends `Module`, exports a firing `Clock`, and updates handshake state in `withClockAndReset` scopes. | A local pulse is a legitimate design technique, but its event, pulse and reset assumptions need explicit contracts; an implicit top-level clock is unnecessary. | `RawModule` composition, explicit state primitives, and named local-event or clocked adapters where required. |
| [AnalyzeCircuit.scala](https://github.com/Jilin-Zhang/ASYNC-Chisel/blob/1af2cf4f621aa77657cab25858cc4a038a7291d6/src/main/scala/tool/AnalyzeCircuit.scala) reparses emitted FIRRTL using Scala FIRRTL APIs and searches `ACG` names with fixed enumeration bounds. | Identity depends on compiler naming and bounded searches. | Explicit semantic IDs, a versioned manifest and checked endpoint mappings through CIRCT. |
| [DelayElement.v](https://github.com/Jilin-Zhang/ASYNC-Chisel/blob/1af2cf4f621aa77657cab25858cc4a038a7291d6/src/main/resources/ASYNC/DelayElement.v) uses `assign #(0.2*DelayValue)`; the controller supplies fixed delay arguments. | These simulation constants do not specify which data path they protect or demonstrate timing closure. | Integer time units, named delay policies, endpoint obligations and passing/failing model fixtures. |
| [tb_FIFO.v](https://github.com/Jilin-Zhang/ASYNC-Chisel/blob/1af2cf4f621aa77657cab25858cc4a038a7291d6/testbench/tb_FIFO.v) sends 16 random values with fixed waits and prints success/failure. | This test does not enforce failure through assertions or qualify broad reset/backpressure behavior. | Automated failing assertions, independent scoreboards, exhaustive small cases, negative controls and replay. |

Do not characterize the original as having no tests or no composition examples. Its scope is narrower than the product we need. Maintain `docs/provenance.md` with inspected revisions, conceptual influences and any third-party material actually incorporated. Its [MIT license](https://github.com/Jilin-Zhang/ASYNC-Chisel/blob/1af2cf4f621aa77657cab25858cc4a038a7291d6/LICENSE) does not change our Apache-2.0 choice; any later code reuse needs attribution and an explicit provenance entry.

## Toolchain and modern Chisel baseline

Use the following **candidate baseline for L0 qualification**, not a claim of demonstrated compatibility. Chisel [7.16.0 was released October 1, 2026](https://github.com/chipsalliance/chisel/releases/tag/v7.16.0); its [compiler configuration](https://github.com/chipsalliance/chisel/blob/v7.16.0/etc/circt.json) selects firtool 1.160.0. The [release build](https://github.com/chipsalliance/chisel/blob/v7.16.0/build.mill) supports the Scala 2.13.18 compiler-plugin tuple.

| Dependency | Initial decision | L0 evidence |
| --- | --- | --- |
| Chisel | `org.chipsalliance %% chisel % 7.16.0` | Resolve artifact, compile and elaborate representative consumers. |
| Scala and compiler plugin | Scala 2.13.18; `org.chipsalliance % chisel-plugin % 7.16.0 cross CrossVersion.full` | Matching full Scala version; generic Bundle and negative-compilation tests. |
| CIRCT | firtool 1.160.0 | Exact binary version/hash, resource emission and endpoint-preservation probe. |
| JVM and build | JDK 21 LTS; sbt 1.12.4, following the [official template structure](https://github.com/chipsalliance/chisel-template) | Pin JDK vendor/patch and launcher checksum in the toolchain manifest; native builds. |
| Scala tests | ScalaTest 3.2.20; bounded enumeration first, property generation as needed | Deterministic test inventory and failures; no legacy chiseltest dependency. |
| External event lane | Start qualification with Icarus Verilog 13.0 and cocotb 2.1.0 | Actual reset, delayed-drive, latch, feedback and event-observation probes on each OS. |
| Secondary lane | Implemented ChiselSim clocked bridge lane pins Verilator 5.046; the earlier 5.052 candidate was not qualified | Native Windows uses a scoped generated-build adapter; Linux uses the unmodified backend. Async cell timing/four-state behavior remain with Icarus. |

Icarus and Verilator versions are available in their [upstream tags](https://github.com/steveicarus/iverilog/tags) and [Verilator release tags](https://github.com/verilator/verilator/tags); cocotb 2.1.0 is published on [PyPI](https://pypi.org/project/cocotb/2.1.0/). Availability is not qualification. Pin Python, cocotb, test dependencies, simulator build options and native packages after the probes. If a candidate fails, retain the failure and change the tuple explicitly; do not silently disable the test or substitute a different backend.

Scala 2.13 is the initial consumer baseline. Scala 3 is a separate future qualification lane, not a reason to block the functional library or advertise an untested cross-build. Use one sbt build, not parallel sbt and Mill implementations. Release builds must not use floating dependency versions.

Apply these API rules:

- Base asynchronous composition on `chisel3.RawModule`. `AsyncModule` is only a small convenience base with an explicit active-high `AsyncReset` port and contract registration. Ordinary clocked modules remain supported through explicit `Clock`/reset ports and `withClockAndReset`.
- Use `chisel3.ExtModule` and its built-in `addResource` for asynchronous primitives and their packaged SV views. Avoid deprecated experimental imports and the old `HasBlackBoxResource` pattern. Keep resource paths classpath-relative, not relative to the caller's working directory. [Current external-module API](https://www.chisel-lang.org/docs/explanations/blackboxes).
- Generate with `circt.stage.ChiselStage`, using `emitSystemVerilogFile` for deliverable RTL and `emitCHIRRTL`/`emitHWDialect` for compiler fixtures. Do not build new dependencies on the legacy Scala FIRRTL compiler or its graph transforms. [Versioned stage implementation](https://github.com/chipsalliance/chisel/blob/v7.16.0/src/main/scala/circt/stage/ChiselStage.scala).
- Use generic `Bundle`/`Vec`, compiler-plugin type cloning and `chiselTypeOf` when deriving a type from bound hardware. Avoid handwritten `cloneType`, reflection into Chisel internals and repeated conversion of user payloads into untyped bit vectors.
- Use `:<>=` for validated bidirectional channel connections and `:<=`/`:>=` where direction is intentionally separate. Library connectors also check exact widths, protocol identity and reset-domain compatibility; connection operators alone are not a protocol checker. [Connectable operators](https://www.chisel-lang.org/docs/explanations/connectable).
- Use ChiselSim for qualified clocked wrappers and API smoke tests. `simulateRaw` exists and does not apply automatic reset stimulus; qualify time advancement and the underlying simulator before adopting it for clockless tests. cocotb on an external event simulator is the initial asynchronous lane. [Chisel testing APIs](https://www.chisel-lang.org/docs/explanations/testing).

No custom Chisel fork, new HDL or replacement compiler IR is planned. The manifest records semantics and references existing hardware objects; it is not a second executable circuit representation. Keep any necessary experimental annotation API behind one internal adapter. Chisel's [annotation guidance](https://www.chisel-lang.org/docs/explanations/annotations) treats annotations as implementation details, so public users should call library APIs rather than construct them.

## Repository and package layout

Use one publishable core artifact initially. Keep verification helpers separate so a hardware consumer does not acquire Python or simulator dependencies merely by importing the library. The following is the target layout; current implemented paths and remaining work are tracked in the dedicated repository:

```text
build.sbt                         project/build.properties
src/main/scala/chiselasync/
  core/                           AsyncModule, typed configuration, domain IDs
  protocol/                       FourPhase, TwoPhase, connectors, payload layout
  primitives/                     CElement, Latch, DelayLine, Mutex declarations
  bundled/                        stages, storage, routing, transforms
  qdi/                            dual-rail family, completion, qualified cells
  interop/                        protocol converters and clocked bridges
  memory/                         request/response ports, ROM/RAM, GPIO boundaries
  metadata/                       descriptors, registration, manifest validation
src/main/resources/chiselasync/sv/ behavioral primitive views
src/test/scala/                    API, elaboration, parameter and packaging tests
examples/                         separate, non-published generators
verification/reference/           independent state/transaction models
verification/cocotb/              event drivers, monitors, scoreboards
verification/fixtures/            handwritten SV and deliberately bad designs
verification/contracts/           case inventory, bounded models, observations
verification/corpus/              minimized regressions and replay records
schemas/                          primitive, design and trace schemas
tools/                            portable runner and toolchain qualification
docs/                             protocols, component catalog, guides, provenance
.github/workflows/                native CI and release qualification
```

Build layers in this order: `core → protocol/primitives → bundled/qdi → interop/memory`; a later group may depend on an earlier group. Metadata schema types are small shared values; export tooling may inspect components, but components never depend on the test runner. No package imports Chiselator implementation types. Avoid mutable process-wide registries: each elaboration has its own contract context, tested with multiple generators in one JVM.

Publish the JAR, sources, ScalaDoc, versioned schemas, behavioral SV resources, checksums, notices and a qualification report. Exported designs include RTL, a deterministic source list, the manifest and model resource hashes. Source-list paths must work from a clean consumer directory, including directories containing spaces. Assign Maven coordinates only when the repository and publishing ownership are available.

## Public API and connection discipline

The public vocabulary below is a proposed contract, not compilable sample code. Implement and compile examples before freezing signatures.

| API | Meaning and constraints |
| --- | --- |
| `FourPhase[T]` | Producer-oriented `req`, `bits`, and flipped `ack`; consumer uses `Flipped`. One outstanding transaction. |
| `TwoPhase[T]` | Distinct nominal type with request/acknowledge parity and explicit initial phase. |
| `DualRail[T]` | Return-to-zero encoding: two rails per payload bit, acknowledgement and completion defined by its protocol; not interchangeable with bundled channels. |
| `FourPhase.connect`, `TwoPhase.connect`, `DualRail.connect` | Typed connection helpers; validate exact layout, domain and protocol metadata before wiring and registering an edge. |
| `BufferConfig`, `ResetPolicy`, `DelayPolicy`, `ArbitrationPolicy` | Immutable case classes and sealed choices with validated parameters; no string-keyed bags or Boolean arguments with unclear meaning. |
| `PayloadLayout[T]` | Recursive leaf names, widths, signedness, bit offsets and serialization version; generated and checked from supported Chisel types. |
| `PrimitiveDescriptor`, `ChannelContract`, `TimingContract` | Versioned declarations independent of the simulator implementation. |

Supported payloads are sized `UInt`, `SInt`, `Bool`, nested `Bundle` and `Vec` containing supported leaves. Reject unknown/zero widths, empty payload aggregates, embedded clock/reset/analog/probe leaves and mixed-direction payloads in the initial release. Provide a separate control-only token channel instead of relying on a zero-bit integer. Record field ordering explicitly and test it against emitted ports; never use unordered map iteration as a wire format.

Library connectors must reject implicit width truncation/padding and two/four-phase mixing. Normal Chisel types and casts can bypass library helpers; do not claim Scala makes all misuse impossible. At export, diagnose unregistered library-channel edges or require an explicit external-endpoint declaration carrying the same contract. A handwritten SV integration uses that declaration and the same runtime monitors. Compile-time, elaboration-time and runtime rejection each get separate tests.

Channel behavior is defined at handshake events, not by a generic clocked `fire = valid && ready` expression:

- **Four phase:** start at request/acknowledge `00`; request rises after the payload is valid; acknowledgement rises after receiver acceptance; request falls; acknowledgement falls. Hold the payload through return to `00`. Each request round trip represents one transaction, including repeated identical payloads.
- **Two phase:** idle request equals acknowledgement. A new request transition presents a transaction; matching acknowledgement completes it. Hold data through completion. Specify parity during initialization and reset so reset cannot masquerade as a token.
- **Dual rail:** `00` is spacer, `01`/`10` encode values, and `11` is invalid. Completion covers every payload bit; acknowledge valid data and spacer separately. The exact indication and fork assumptions belong to the qualified cell family.

Channels share one reset domain by default. Different or independently reset domains require an explicit bridge with a restart protocol. Specify what is flushed, what may be retried and what is already committed. A connector cannot manufacture exactly-once delivery across independently resetting endpoints without that agreement.

The default coordinated reset flushes uncommitted in-flight tokens, restores declared initial occupancy/phase, and cancels pending internal model events. Drivers and scoreboards mark aborted transactions explicitly. A committed memory or I/O effect is not rolled back or automatically replayed. Reset release permits traffic only after every participating endpoint is initialized; independently resetting bridges must establish readiness before accepting new requests.

## Component contracts and implementation strategy

Stateful asynchronous behavior lives behind explicit primitive boundaries. Do not express a latch as an incomplete Chisel `when`, depend on an anonymous combinational feedback loop surviving optimization, or cast arbitrary handshake levels to clocks throughout the library. A qualified local pulse implementation may use a named event/clock adapter with pulse-width and reset obligations. The compiler must see that distinction.

### Primitive foundation

| Primitive | Initial semantics | Required tests |
| --- | --- | --- |
| C-element | Start with resettable two-input form: unanimous inputs change output; disagreement holds state. Generalize arity by explicit composition and contract. | Every Boolean state/input case; reset dominance; unequal input arrival; held state; unknown-input policy in four-state external views. |
| Latch | Parameterized payload storage; transparent while enabled, retains value when closed; explicit initialization and reset. | Open/close boundaries, data while closed, reset at capture and model setup/hold obligations. |
| Delay line | Declared integer tick delay, transport or inertial policy, pulse handling and reset cancellation. | Equal-time ordering, short pulses, replacement/cancellation, overflow and stale events after reset. |
| Mutex | At most one grant; persistent request and release protocol; nondeterministic allowed winner. | Simultaneous requests, delayed resolution, never two grants, replay and both legal outcomes. |
| Completion detector | Completion of all rails in the declared valid/spacer phase. | Every small input permutation, partial arrival, invalid encoding and incomplete return to spacer. |

Each primitive needs a reviewed transition/observation specification, an independently written expected-result model, a Chisel declaration, an SV behavior view and a versioned descriptor. A native Chiselator view comes in step 3. Simulation delay, randomized arbitration and metastability abstractions are explicitly simulation policies, not proof of a realizable or analog-accurate cell.

Use logical reset epochs in the test/model contract to prevent delayed pre-reset actions from reappearing after reset. Define initialization before the first transaction, including a deliberate reset sequence at time zero. Never silently coerce an unknown initial primitive state into zero. The two-state contract applies only after its initialization requirements hold; external four-state diagnostics have their own expected outcomes.

### Bundled data foundation

| Component | Initial implementation choice | Acceptance behavior |
| --- | --- | --- |
| `Buffer` and `Stage` | One-entry storage built from primitive contracts; stage separates combinational transform from capture. | One input acceptance per stored item, no overwrite, output holds under backpressure. |
| `Fifo` | Bounded composition of qualified stages before specialized implementations. | FIFO order, exact capacity, full/empty transitions; depth below one rejected. |
| Initialized token source | Explicit initial payloads and occupancy, including reset behavior. | Emits the declared tokens exactly once per initialization epoch; enables tested feedback examples. |
| `Fork` | Broadcast with per-consumer completion state. | Every branch consumes once; producer completion waits for all required branches. |
| `Join` | Independently hold each operand until a pair/set is available. | Pair corresponding accepted operands without loss or cross-pairing. |
| `Select` | Route to one destination using a selection captured with the transaction. | Changing later selection cannot redirect an outstanding transaction. |
| Exclusive `Merge` | Caller guarantees non-overlapping requests; monitor the assumption. | Contention is a diagnosed contract violation, not arbitrary priority. |
| `Arbiter` | Compose mutual exclusion with a declared service policy. | Preserve winner payload and losers' requests; fairness only under stated policy/environment assumptions. |
| Combinational transform | Normal Chisel logic between controlled storage boundaries. | Declare source-to-capture timing obligation; do not infer data validity from a fixed number of host callbacks. |

Begin with four-phase bundled data to match the existing contract and simplify observation. This is our design choice, not a claim that ASYNC-Chisel's toggle-based controller is four-phase. Implement two-phase controllers separately; reuse pure payload/layout utilities and checked primitives where their semantics match. Do not make one controller toggle between incompatible protocols through a Boolean flag.

Zero-delay functional mode is allowed only for components with defined quiescent behavior. Timed mode needs a declared delay for every relevant primitive/path obligation. An intentional free-running token ring with no positive delay has no finite settled result: diagnose non-progress/oscillation rather than invent a clock tick. Legal idle and waiting on an external endpoint are not automatically deadlock.

### Functional completeness before the MCU

L2 adds the remaining catalog rather than moving it into an indefinite post-MCU backlog:

- Two-phase storage/routing counterparts and explicit two/four-phase converters. Each converter owns buffering, phase state and coordinated reset; prove token conservation under stalls.
- A bounded QDI family: return-to-zero, strongly indicating dual-rail storage/completion, fork/join/routing, and NOT, two-input AND/OR/XOR, two-way select and one-bit full-adder cells. Each cell must acknowledge all required input arrivals and returns to spacer, including logically redundant operands; qualify its monotonic transitions and fork assumptions. Arbitrary binary Chisel arithmetic followed by an encoder remains bundled-data computation inside an explicit adapter, not a QDI claim. Larger arithmetic and other encodings can be later extensions.
- Bundled/dual-rail converters with explicit valid/spacer completion, storage, timing and reset boundaries. Test all rail arrival orders for small widths.
- Clocked `Decoupled` bridges in both directions, each taking a named clock/reset domain. A clocked transfer occurs on a clock edge with valid and ready; bridge storage keeps payload stable while the async handshake completes. Synchronize control and hold multibit data under the declared protocol rather than independently synchronizing each payload bit. Digital latency variation tests do not establish metastability MTBF.
- Single-request memory interfaces with explicit read/write operation, address, byte mask, payload and response/error. Define one outstanding operation per port initially, response ordering, write commit, bounds, alignment and read/write collision behavior. Provide functional ROM/RAM views, image hashing and reset policies; physical macros wait for step 4.
- GPIO/interrupt adapters with level/pulse capture and pending-until-acknowledged behavior. Test acknowledgement coincident with a new event, CPU-only reset and separate always-on state, supporting the [RISCay-MCU supervisor contract](async-mcu.md).

No RISC-V decoder, ISA emulator or Pi-specific power policy belongs in the library. Memory and clocked boundaries are reusable components; firmware, timer policy and the complete clockless core belong to RISCay-MCU in step 2.

## Timing and compiler export contracts

Use exact integer time with a declared unit, checked conversions and explicit equality policy. Canonical exported time follows [execution specification 01](specs/01-execution-semantics.md): integer femtoseconds in the nonnegative signed 64-bit range. An external simulator's precision must represent the selected fixture times exactly or reject the case; it must not round silently. Femtosecond representation does not imply femtosecond physical accuracy.

Library timing declarations describe launch, data-valid, capture and release observations. A model check requires `capture_time >= data_valid_time + setup` and data stability through `capture_time + hold`; same-time event ordering must still satisfy the declared observation phases. Record the source of each delay value as assumed, randomized or externally supplied. Random samples are stress inputs, not a manufacturing distribution.

Build a behavioral fixture with independently delayed data and control paths. For example, data valid at tick 8 with setup 2 must fail capture at tick 9 and pass at tick 10 when the declared phase ordering holds. Sweep hold violations and one-tick offsets as well. The checker observes these paths; it must not delay capture itself to make the design pass. Track validity by transaction/launch identity as well as value, because two identical payloads can still have different timing obligations. This tests the declared model; it does not infer real combinational delay from untimed Chisel arithmetic.

The design manifest must contain:

| Record | Required fields |
| --- | --- |
| Design identity | Schema version, design/configuration hash, library/toolchain versions, compilation options and resource hashes. |
| Primitive instance | Semantic kind/version, unique instance ID, parameter values, selected view, ports, initialization, reset domain and effects. |
| Channel | Protocol/version, endpoint IDs, payload layout, capacity, initial phase/tokens and environment assumptions. |
| Timing obligation | Launch/data/capture endpoint IDs, unit, bounds, delay/pulse policy, provenance and supported modes. |
| Export mapping | Source location/hierarchy, compiler targets, resulting RTL/IR references, and any declared transformed or merged targets. |

Assign deterministic IDs within a design/configuration using explicit user labels where available and deterministic elaboration paths otherwise. IDs need not survive arbitrary source refactoring; never advertise them as globally permanent. Avoid wall-clock timestamps, absolute checkout paths and unordered iteration in semantic hashes. Retain human-readable source paths separately.

L0 must prove a minimal endpoint round trip before the API expands. Start with retained primitive ports and explicit contract anchors using supported compiler mechanisms. Inspect actual emitted names/targets and validate every required endpoint. Do not assume `suggestName` or `dontTouch` alone gives a complete mapping. If arbitrary custom annotations do not survive, use the checked sidecar/anchor route or narrow the supported export configuration; do not ignore lost metadata. Reject ambiguous mappings, duplicate IDs, missing resources and unbound stateful primitives.

Future Chiselator integration consumes the CIRCT representation plus these contracts and selects one execution view per primitive. It must not execute both an SV body and a native model for the same stateful effect. Raw SV clients use equivalent declarations and the manifest. CIRCT import and native-model qualification belong to step 3; library step 1 establishes inspectable fixtures and does not require the full simulator frontend.

## Verification and reproducibility

Implement the [scientific test rules](test-plan.md#scientific-method-and-limits-of-claims) as release criteria, not just documentation. The production SV implementation, independent transaction/reference model and test driver must have separate behavioral code. They may share type/schema definitions and test inputs. Comparing two simulators running the same faulty SV is useful but cannot be the only correctness evidence.

| Existing suite | Concrete library work |
| --- | --- |
| LIB-01 | Compile consumer APIs; enumerate directions, payload shapes and parameters; require specific diagnostics for invalid widths, protocol mixing, mixed domains and illegal initial occupancy. |
| LIB-02 | Hand-derived primitive cases plus exhaustive finite state/input combinations; event/reset boundary tests; injected stale events and double grants. |
| LIB-03 | Transaction scoreboards for all catalog entries; bounded event-order enumeration, stalls, equal payloads, resets, contention, converter parity, QDI rails, CDC and memory commit. |
| LIB-04 | Manifest/RTL/IR endpoint checks; independent timing-boundary sweeps; corrupted metadata, missing view and shortened-delay controls. |
| LIB-05 | Exact native toolchain/backend matrix; model feature probes; qualified ChiselSim and standalone SV lanes. |
| LIB-06 | Publish locally, consume from a clean unrelated project, extract resources, replay retained cases and reject incompatible schema/semantic versions. |

For each component, write the small state model and invariants before production behavior. Enumerate bounded interleavings to check token conservation, capacity, mutual exclusion and reset epochs. These checks qualify the specified finite model; they do not prove arbitrary RTL or silicon. RTL observations must independently match that model. Progress properties require explicit eventual-response assumptions; an environment allowed to stall forever cannot support a bounded-liveness claim.

Drivers and monitors wait on protocol transitions and qualified simulator observation phases. Use absolute simulation-time deadlines and a separate host timeout for hung tools; do not sample only every N cycles. Tests must count accepted/completed transactions and verify expected observation counts so an unconnected design or zero-test selection cannot pass. Same-time races get a stated partial-order contract or recorded allowed choice; process-registration order must not become an undocumented arbiter.

Required negative controls include a dropped acknowledgement, duplicate token, altered payload under backpressure, premature fork completion, wrong join pairing, double grant, illegal dual-rail value, short control delay, stale event after reset, duplicate memory commit and deleted timing endpoint. A negative test passes only when the intended checker fires at the intended phase. A crash, unrelated assertion or timeout is not equivalent.

Each run retains configuration/tool/resource hashes, seeds and arbitration choices, case inventory, required activity, event/transaction trace, outcome and replay command. Use an explicitly versioned PRNG or recorded choices rather than relying on simulator-specific `$random` sequences. Compare required observations; allow only declared timing/choice differences. Keep minimized failures as permanent regressions. Freeze validation seeds/cases separately from tuning examples and report all selected outcomes, including infrastructure failures and unsupported cases.

Use JUnit plus structured JSON for results and VCD/FST where supported for diagnosis. Release reports distinguish functional behavior, declared-delay timing tests, four-state diagnostics and backend compatibility. No throughput, power, area, physical timing or metastability accuracy claim follows from these tests.

## Native portability and release automation

Native Windows x86-64, Linux x86-64 and macOS arm64 are required targets. Test three separate capabilities: JVM/API tests, firtool emission, and actual external event simulation. The [firtool 1.160.0 release](https://github.com/llvm/circt/releases/tag/firtool-1.160.0) provides artifacts for these platforms; this does not establish that the complete harness works. cocotb documents [native platform setup](https://docs.cocotb.org/en/stable/install.html) and [simulator-specific limits](https://docs.cocotb.org/en/stable/simulator_support.html), which the probe must resolve.

Use Scala/JVM and Python process APIs with argument arrays, pathlib-style paths and deterministic working directories. Keep essential build logic out of Bash-only scripts. A `.cmd` or PowerShell entry point and a Unix entry point may invoke the same runner. Containers are optional conveniences; WSL does not count as native Windows evidence. A documented native tool dependency is acceptable; an undeclared Linux VM requirement is not.

Proposed developer commands, implemented in the dedicated repository, are `sbt test`, `sbt "examples/runMain ..."`, `python -m chiselasync_verify qualify`, `python -m chiselasync_verify run --suite LIB-03`, and `python -m chiselasync_verify replay <case>`. The runner discovers tools, checks versions, reports missing required capabilities and emits actionable diagnostics. It must not silently download an unpinned compiler or fall back to another simulator.

| CI tier | Required work |
| --- | --- |
| Pull request | Scala compile/API tests, deterministic elaboration and metadata checks, primitive/composition smoke tests, required negative controls; native emission/consumer checks on all three OS targets. |
| Nightly | Full supported event matrix on all three OS targets, bounded explorations, fixed randomized campaigns, replay, resource/path edge cases and minimized regression corpus. |
| Release | Fresh dependency installation, complete required suite inventory, native clean consumers, standalone SV consumption, backward-compatibility fixtures, documentation examples and artifact checksums. |

The release gate fails if a required lane is skipped, has no observations or lacks its oracle. Candidate dependency upgrades run separately and replace the baseline only after qualification. Pin CI actions and retained runner/tool identities. Publish catalog status by component, protocol, mode and platform; planned or implemented rows are not qualified rows.

## Implementation work packages

Each package should become one or more reviewable issues/PRs in the dedicated repository. Role names identify responsibilities to assign when implementation starts; they are not a staffing claim. API/compiler ownership and verification ownership should review each other's contracts, with independent async-domain review for QDI and arbitration.

| Package | Depends on | Deliverables | Exit evidence and owner |
| --- | --- | --- | --- |
| CA-01 Build and external-tool probe | Repository added | sbt skeleton, exact toolchain manifest, native CI, one explicit-reset `RawModule`/`ExtModule` resource and event fixture. | LIB-05/06 smoke passes on each target; deliberate model failure fails the run. Build/CI owner. |
| CA-02 Protocol and reference contracts | CA-01 | Four/two-phase state tables, reset/commit policy, payload schema, primitive contracts, independent small reference and trace schema. | Hand-derived cases and bounded enumerations agree; conflicting/undefined cases resolved before implementation. Verification owner plus async review. |
| CA-03 Typed API and export proof | CA-02 | Channel types, configuration validation, domain-aware connectors, manifest writer and retained endpoint fixture. | LIB-01/04; generic nested payload round trip, invalid connections rejected, lost endpoint detected. API/compiler owner. |
| CA-04 Primitive foundation | CA-02, CA-03 | C-element, latch, delay, descriptors and independent SV views. | LIB-02; exhaustive small cases, reset/pulse boundaries and replay. Library and verification owners. |
| CA-05 First complete library example | CA-04 | Four-phase one-entry buffer with a pure transform; packaged generator and external driver. | Reset, equal payloads, stalled output and model timing controls pass from a clean consumer. L0 closes with CA-01–05. |
| CA-06 Four-phase composition | CA-05 | FIFO, initial tokens, fork, join, select and exclusive merge; feedback and fork/join examples. | LIB-03/04 including occupancy, pairing, backpressure and reset; all foundation docs executable. L1 gate. |
| CA-07 Arbitration and two-phase | CA-06 | Mutex/service policies, two-phase counterparts and two/four-phase converters. | Legal winner exploration, conservation, parity/reset and contention controls. Async and verification owners. |
| CA-08 QDI family and converters | CA-04, CA-06 | Named indication/fork assumptions, dual-rail cells/storage/completion/routing and bundled converters. | Rail-order enumeration, invalid-rail/spacer controls, component-level obligations; external async review. |
| CA-09 Clocked and application boundaries | CA-06, CA-07 | Decoupled bridges, CDC control models, ROM/RAM interfaces, GPIO/pending-event adapters. | Clock/reset phase sweeps, repeated data, independent reset rejection/restart, exactly-once memory effects and event races. |
| CA-10 Packaging and functional release | CA-07, CA-08, CA-09 | Full catalog, guides, executable examples, compatibility policy, clean Scala/SV consumers and release artifacts. | LIB-01–06 on every required target; scientific controls pass; no incomplete required catalog rows. L2 gate. |
| CA-11 Consumer handoff | CA-10 | Pinned release, contract fixtures, small memory/IO/control examples and integration guide for RISCay-MCU. | Independent repository consumes the release without library source patches or Chiselator. Step 2 can begin. |

Implement a minimal buffer during L0 to test the whole workflow, rather than declaring the compiler and packaging solved after syntax checks alone. L1 broadens the four-phase family; it is a usable foundation milestone but is not the requested complete library release. L2 includes the defined two-phase, QDI, arbitration, clocked and memory/IO catalog before RISCay-MCU implementation.

The first complete *chip* example remains RISCay-MCU. Library examples are smaller qualification fixtures: one-stage transform, fork/join, initialized feedback, two/four-phase conversion, dual-rail completion, clocked bridge and variable-latency memory. They must run without a global periodic clock except where a clocked boundary is explicitly under test.

## Risks and decisions resolved by implementation

| Risk | Earliest experiment | Required response |
| --- | --- | --- |
| Compiler loses primitive or endpoint identity | CA-03 round-trip fixture with optimization and resource extraction. | Qualify a supported anchor/export path before broad API work; preserve the failing regression. |
| External engine accepts syntax but has unsuitable event behavior | CA-01 timed/reset/feedback probes on each OS. | Publish exact exclusions and qualify another pinned engine if needed; missing required coverage blocks release. |
| Two-state initialization hides reset defects | CA-02/04 explicit initialization plus independent four-state diagnostic cases. | Require reset contracts; retain unknown values in applicable observations rather than converting them silently. |
| Composition is correct individually but wrong under concurrency | CA-06 bounded fork/join/feedback schedules and adversarial stalls. | Fix contracts/implementation, not the expected trace; add the minimized interleaving. |
| QDI or arbitration scope exceeds available expertise | CA-02 contract review, then CA-07/08 cell-level demonstrations. | Obtain specialist review, expose remaining unsupported scope and re-estimate; never label a stub complete. |
| API is pleasant locally but unusable downstream | CA-05 clean consumer, repeated through CA-10. | Test public APIs/resources independently of the source checkout and document migration. |

Do not attach a firm delivery date before L0. Re-estimate after native tools, export preservation and the first independently verified buffer work; QDI and reset/concurrency review are likely the largest uncertainties. Continue these tasks in the dedicated repository under its current qualification gates. Physical technology and implementation choices remain explicitly deferred to step 4.
