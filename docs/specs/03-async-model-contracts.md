# 03 — Async model contracts

Draft, October 5, 2026. Status and scope: [specification index](README.md). Native bundled-data support is the first complete design path; clocked and QDI bindings remain supported architectural paths.

## Primitive library

The public library is [chisel-async](../chisel-async.md), an independently designed evolution of async Chisel library ideas. Build and externally qualify its functional catalog before the main simulator. This specification supplies its initial primitive/channel semantics; the library architecture adds component composition, completeness gates and compatibility obligations. The library must work without Chiselator, ACT, a PDK or Yosys.

Chisel emits annotated primitive extmodules with native simulation bindings. Equivalent SV modules expose the same contracts. This keeps intentional stateful feedback out of anonymous combinational loops and does not require handwritten SV for every Chisel primitive. Every instance declares version, parameters, reset policy, state and delay mode.

| Primitive | MVP behavioral contract |
| --- | --- |
| C-element | Output becomes the common input value when all inputs agree; otherwise holds initialized state. Explicit reset dominates and establishes the configured initial value. |
| Latch | Transparent while enabled; captures/holds when closed. Reset priority and initial value are declared. Zero-delay behavior is functional; setup/hold checks require an annotated timing model. |
| Delay line | Positive integer delay; explicit transport or inertial behavior, captured payload and cancellation generation. Delay values are model data, not physical signoff evidence. |
| Mutex | Two requests, at most one grant. A grant persists until its request withdraws; a new winner is chosen only when no grant is held. Simultaneous eligible requests use a seeded/logged legal choice. No bounded fairness or analog resolution time is implied. |
| Synchronizer | Declared clocked sampling/latency model. Optional latency perturbation is a test model; it does not simulate analog metastability. |

Primitive state starts uninitialized unless explicit initialization/reset establishes it. Unsupported use before initialization fails. Reset cancels pending state-changing primitive transactions; it does not rewind already committed external effects. Each primitive states whether deassertion immediately reevaluates inputs or waits for an edge; C-elements and transparent latches reevaluate immediately, while clocked synchronizers wait for their sampling edge.

For transport delay, each input transition creates a captured output event. For the MVP inertial delay line, an input change cancels the outstanding candidate and schedules the new value after the specified stable interval; if it equals the current output, cancellation suffices. A delivery already due at the current timestamp is processed in the due-driver batch before reactions create new candidates. Test pulses shorter than, equal to and longer than the interval; the equality rule must survive code generation. Other inertial/rejection semantics require separate capabilities.

## Four-phase channel

The first external channel contract uses request, acknowledge and a typed payload, with one outstanding transaction. Idle is `(req, ack) = (0, 0)`. Legal transitions are `00 → 10 → 11 → 01 → 00`. The producer holds payload stable before request assertion and through return to idle. This conservative interface contract simplifies substitution; internal bundled-data launch/capture paths are checked separately.

Allocate an offered transaction ID at request assertion; acceptance occurs at acknowledge assertion, and completion occurs at return to idle. An accepted transaction is not automatically an instruction retirement or a memory write: the endpoint declares its effect point. Repeated equal payloads still produce distinct IDs. Backpressure may delay acknowledgement indefinitely unless the environment contract supplies a deadline.

Reset creates a new channel epoch and returns interface wires to idle. Outstanding handshakes are recorded as aborted; previously committed stores or I/O effects are not rolled back. Each endpoint declares reset effects on its own state and memory. Adapters cannot add invisible buffering, reorder transactions or change reset semantics. Requests that violate phase order or payload stability produce source/instance/transaction diagnostics.

QDI bindings add encoding-specific validity and spacer checks, plus declared environmental/isochronic-fork assumptions. Wrapped clocked blocks declare their local clock and channel adapter. Compare payload/order/reset effects across implementations; compare timing only under compatible acceptance/completion definitions. Four-phase is the first implementation slice; two-phase channels and explicit converters are required by chisel-async's functional completeness gate and have a separate contract. Native simulator qualification for each protocol is tracked independently.

## Bundled-data timing

Source annotations identify launch, protected data paths, capture/control endpoints, setup/hold margins and reset obligations. Functional simulation checks protocol behavior. Annotated simulation additionally checks a concrete implementation's timing obligations; random delays explore scenarios without proving all delays safe.

For each specified launch/capture pair, require earliest permitted capture to follow latest protected data arrival plus the receiver margin. Also verify hold and return/reset constraints. Preserve endpoint provenance through elaboration, optimization, replication and mapping; missing or ambiguous required endpoints fail validation. An optimizer must not erase a delay element or control dependency that implements a timing obligation.

For steps 1–3, TIME-01 qualifies source-to-model endpoint provenance and relative-timing checks using behavioral stages with explicit delay assumptions. Use independently derived passing/failing boundaries, including equality and one-tick offsets; deliberately short control delay, slow data and hold violations must be detected. No cell library, PDK, mapped netlist, Liberty, STA or SDF is required. Report these as model-level checks, not physical timing evidence.

Step 4 may extend these checks to mapped cell models and implementation-derived timing. Agreement between STA and simulation with a shared library checks tool consistency, not the library's physical accuracy. Physical claims then require independent characterization evidence and uncertainty over the claimed operating domain; random delay sweeps do not estimate fabrication yield. Follow the test plan's [physical model validation rules](../test-plan.md#detect-optimistic-physical-models).

GF180MCU is a retained step 4 candidate. Its cell inventory, primitive implementations, physical views and characterization are deferred; none is required for the functional fixture. Before any future physical support claim, establish and qualify those implementation details. Node size alone does not establish suitability.

CIRCT includes synthesis and technology mapping, but physical synthesis, place-and-route and tapeout are deferred to the [step 4 backlog](../chip-build-plan.md). Yosys and other physical dependency choices will be revisited then, with no decision required now. Steps 1–3 consume behavioral primitive views and declared delays. [CIRCT synthesis scope](https://circt.llvm.org/docs/Tools/circt-synth/).

## First complete example: minimal async MCU

The application is named RISCay-MCU. Build and independently qualify it on an existing simulator at C0 after chisel-async, then use that fixed corpus to qualify Chiselator at S0. Physical memory technology, hardware debug/test, board and fabrication gates belong exclusively to deferred step 4 in the [chip backlog](../chip-build-plan.md).

Implement the [Raspberry Pi power-supervisor MCU](../async-mcu.md) in its own repository using chisel-async, and simulate it in Chiselator. RISC-V is required; RV32EC is the proposed target, with sequential fetch/decode/execute handshakes, explicit latches/state primitives and request/acknowledge memory interfaces. A narrow internal datapath may implement its full 32-bit architectural semantics. Budget 2 KiB fixed program ROM and 256 bytes RAM provisionally; measure linked firmware, runtime helpers and stack headroom before fixing memory sizes or claiming physical fit. GPIO, pending event capture, wait/wake and an independent timer/RTC interface support the power policy. Use a pinned bare-metal RISC-V compiler/assembler toolchain, without pipelining or caches. Freeze the execution environment and event-wait/interrupt contract before implementation; do not invent a custom WAIT instruction. RISC-V retirement tests complement async protocol and power-policy tests. The ISA and memory sizing belong to the MCU, not the simulator ABI.

The main datapath must make progress without a global periodic clock; elapsed-time policy uses an independent timebase, not instruction counting. Clocked timer peripherals may be wrapped explicitly. A Chisel test driver loads a fixed firmware image and consumes instruction retirement records containing PC, instruction identity, architectural writes and committed memory/I/O effects. An independent instruction-level model predicts that sequence, and a separate supervisor reference checks power transitions. Timing variation may change latency; policy results must follow the same timebase and external-event contract.

Acceptance requires:

- Boot/reset, arithmetic, taken/untaken branches, RAM accesses, GPIO output and external input sequences agree with the independent model.
- Variable memory response latency and bounded backpressure do not lose, duplicate or reorder operations; repeated identical values are included.
- Reset during an outstanding handshake follows the declared abort/committed-effect policy and restarts correctly.
- A halted MCU is distinguished from a stalled obligation; external waiting alone is not reported as deadlock.
- Fixed and randomized legal model delays reproduce failures by seed/choice log. Injected short control delay is caught against the declared behavioral timing contract; physical matched-delay qualification waits for step 4.
- A selected MCU block can be replaced by behavioral, native QDI or wrapped clocked logic under the same transaction scoreboard. Full QDI conversion of the MCU is not required.
- Graceful shutdown waits for a qualified late Pi acknowledgement before external power removal. Boot/heartbeat/shutdown timeouts, stale acknowledgements, low supply and forced-off policies have separate outcomes and negative controls.
- CPU-only reset preserves an already enabled Pi supply through the declared always-on output state; pending events survive wait/acknowledgement races. Real-board electrical behavior is a separate qualification gate.

The project owner will add dedicated MCU and chisel-async repositories. Keep their implementations outside the simulator repository; pin source/images/library contracts in integration manifests and retain only appropriate shared/minimized regression fixtures. The MCU is the first complete application; counters, register swaps and one-stage handshakes remain earlier unit/integration fixtures. MCU-01–04 qualify simulation, MCU-05 qualifies real Pi integration, and MCU-06 qualifies physical feasibility as defined in the application plan.

## Optional ACT binding and qualification

ACT runs out of process and must satisfy the architecture's versioned load/inject/advance/yield protocol. Exchange exact time and supported phase information; reach current-time quiescence in both engines before advancing. No API capability is presumed until the pinned actsim probe demonstrates it. Unsupported zero-lookahead or hazard-sensitive boundaries fail explicitly.

Use ACT as an optional simulation backend, not a transitive synthesis/helper dependency. Any proposed exception for RISCay-MCU physical builds does not permit ACT simulation adapters to introduce Yosys. Native MCU execution and core packages remain independent of ACT installation. A missing or failed requested ACT binding is an error, never an automatic native approximation.

Functional acceptance: ASY-01–04, TIM-01/02 and MCU-01–04 cases in INT-02; ACT-01 only for advertised optional ACT support. Exhaust small primitive state sequences; test legal idle versus deadlines, protocol mutations, modeled timing failures, reset, repeated payloads and backend disconnect. MCU-05/06 and mapped physical checks are step 4 gates. Legal-choice exploration and analog/physical verification remain distinct claims.
