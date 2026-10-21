# 03 — Async model contracts

Draft, October 5, 2026. Status and scope: [specification index](README.md). Native bundled-data support is the first complete design path; clocked and QDI bindings remain supported architectural paths.

## Primitive library

The public library is the built [chisel-async](../chisel-async.md). Its pinned upstream contracts own component semantics; this specification defines the simulator binding obligations. Compare exported models and native behavior instead of redefining the library to match the engine. The library and functional MCU work without Chiselator, ACT, a PDK or Yosys.

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

GF180 development exists in the MCU repository, with physical qualification still separate. Native functional fixtures require no cell inventory, PDK or characterization. Physical claims must use their own current revision and evidence; node size alone establishes no suitability.

CIRCT includes synthesis and technology mapping, but physical tools and target qualification belong to [step 4](../chip-build-plan.md). Simulator inputs remain behavioral models and declared timing contracts. No Yosys dependency enters native simulation. [CIRCT synthesis scope](https://circt.llvm.org/docs/Tools/circt-synth/).

## First complete example: minimal async MCU

Integrate the built [RISCay-MCU](../async-mcu.md) at the [pinned baseline](../integration-status.md). It implements RV32E without compressed instructions, with four-phase BD and native Click variants. The reference profile uses 2 KiB executable SRAM and 1 KiB working SRAM. Boot, memory, sleep, peripheral and firmware semantics belong to the MCU repository, not the simulator ABI.

The application is hybrid: async CPU/SoC paths coexist with clocked memory/service, low-frequency timekeeping and reset/watchdog logic. Preserve actual domains and sampling edges. Native S0 requires independent retirement/effect agreement, boot and loader behavior, memory/MMIO, wait/wake, faults and reset/persistence. Do not require a synthetic global CPU clock or physical build.

Treat accepted POR-owned persistent operations independently from application response lifetime: application reset may abort the response while the effect finishes. Receipt boundaries borrow held payload and must not acquire imaginary storage. Each MCU-specific quiescing/rebase contract needs an explicit binding and regression cases; generic reset cancellation cannot override it.

MCU-01–04 in the [test plan](../test-plan.md) qualify functional native integration. MCU-05 covers claimed board/application profiles; MCU-06 covers physical claims. Raspberry Pi power policy is an optional application corpus, not mandatory behavior of the generic core. Small clocked and async fixtures precede full-MCU qualification. Full QDI conversion is not required, and every native protocol capability is qualified separately.

## Optional ACT binding and qualification

ACT runs out of process and must satisfy the architecture's versioned load/inject/advance/yield protocol. Exchange exact time and supported phase information; reach current-time quiescence in both engines before advancing. No API capability is presumed until the pinned actsim probe demonstrates it. Unsupported zero-lookahead or hazard-sensitive boundaries fail explicitly.

Use ACT as an optional simulation backend, not a transitive synthesis/helper dependency. Any proposed exception for RISCay-MCU physical builds does not permit ACT simulation adapters to introduce Yosys. Native MCU execution and core packages remain independent of ACT installation. A missing or failed requested ACT binding is an error, never an automatic native approximation.

Functional acceptance: ASY-01–04, TIM-01/02 and MCU-01–04 cases in INT-02; ACT-01 only for advertised optional ACT support. Exhaust small primitive state sequences; test legal idle versus deadlines, protocol mutations, modeled timing failures, reset, repeated payloads and backend disconnect. MCU-05/06 and mapped physical checks are step 4 gates. Legal-choice exploration and analog/physical verification remain distinct claims.
