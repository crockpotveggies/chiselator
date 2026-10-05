# Chiselator simulator test plan

Research and proposed implementation plan, updated October 5, 2026. This extends the [software architecture](software-architecture.md) and covers all 32 P0 requirements in the [MVP feature list](mvp-feature-list.md). **No simulator, test harness, or CI jobs described here are implemented yet.**

Treat Chiselator as a compiler, an event scheduler, a native runtime, and a developer product. Each needs its own evidence. The highest priority is an executable specification of observable behavior, an independently implemented small reference evaluator, and permanent regression cases. Optimization follows those foundations.

The [five implementation specifications](specs/README.md) define the proposed contracts this plan validates. The four steps are chisel-async, RISCay-MCU verified externally, Chiselator, then physical chip build. Native Windows x86-64, Linux x86-64 and macOS arm64 are required simulator release lanes. Steps 1–3 require no Yosys, PDK or physical toolchain; the [step 4 backlog](chip-build-plan.md) defers all physical dependency decisions and qualification. Behavioral timing tests remain mandatory without claiming silicon accuracy.

Build and qualify [chisel-async](chisel-async.md) first, then RISCay-MCU on an existing simulator. Their independent references, external SV models and component/application corpus must be usable without Chiselator. When native bindings arrive, reuse those tests as independent evidence; do not redefine expected library or MCU behavior to match the new engine.

## Quality contracts

| Goal | Contract | Evidence |
| --- | --- | --- |
| Accurate | Supported designs follow declared language, primitive, timing, and observation semantics; unsupported behavior is diagnosed | Directed expected traces, independent comparisons, properties, negative tests |
| Reproducible | The same supported inputs, toolchain, configuration, and recorded choices produce the same observable result | Replay bundles, deterministic traces, cache and optimization comparisons |
| Durable | Long runs, repeated sessions, faults, dependency upgrades, and releases preserve correctness and usable diagnostics | Resource stress, fault injection, compatibility fixtures, clean installation tests |

These contracts cover clocked Chisel/SV, bundled-data async, native QDI primitives, and the optional ACT boundary. Two-state MVP behavior is explicit; passing these tests will not establish full SV/X/Z support, analog metastability accuracy, or physical signoff.

## Scientific method and limits of claims

The plan must seek counterexamples, not accumulate green runs. Every accuracy or performance claim needs a falsifiable hypothesis, an independently justified expected result, controls that demonstrate the checker works, a fixed evaluation procedure, and retained evidence. Passing provides bounded evidence under stated assumptions; it does not prove the simulator universally correct.

Separate three questions in reports. NASA's modeling and simulation standard provides relevant precedent for explicit acceptance criteria and credibility assessment; these are our project rules, not a claim of NASA compliance. [NASA model and simulation standard](https://standards.nasa.gov/standard/NASA/NASA-STD-7009).

| Question | Evidence required | Claim that evidence cannot establish |
| --- | --- | --- |
| Does the simulator implement its digital contract? | Independent expected traces, language conformance on the supported subset, bounded exhaustive cases and defect detection | Unimplemented SV semantics or all possible programs are correct |
| Does the modeled circuit represent the intended hardware? | Validated cell models, timing provenance, declared assumptions and independent physical evidence for the intended use | An ideal latch, random delay or two-state run predicts silicon behavior |
| Is this implementation faster? | Correct equal-work runs, a frozen comparison protocol, held-out workloads and reported measurement uncertainty | General speedup from a selected best case or weaker observation mode |

### Register the experiment before evaluation

Commit an experiment record with the test catalog before collecting release or headline benchmark evidence. Exploratory work may change freely, but label it exploratory and retain failed attempts. A changed hypothesis, tolerance, corpus, stopping rule or exclusion requires a new record/revision; it cannot retroactively rescue a failed qualification run.

| Record field | Required decision |
| --- | --- |
| Claim and scope | Exact supported behavior, platform/backend/value mode, assumptions and known exclusions |
| Falsifier and oracle | Observable disagreement that refutes the claim; expected-result provenance and shared implementation dependencies |
| Controls | Known-good case, activated known-bad case, and required evidence that the measured path/checker actually ran |
| Inputs and sampling | Frozen fixture hashes, generator/distribution, seed policy, independent trial unit, bounded search limits and held-out split |
| Acceptance and stopping | Exact comparison or justified tolerance, planned sample/repetition count, required bins, limits and exclusion policy |
| Evidence and review | Raw outputs, analysis revision, result identity and a reviewer other than the implementation author |

Digital values, event order and integer timestamps use exact comparisons. Any cross-tool normalization or physical numerical tolerance is specified before evaluation and justified by the common contract or model precision. Do not widen tolerances after observing a mismatch. An unavailable independent review leaves qualification pending; it does not prevent exploratory development.

For example, OPT-01's claim is that activity tracking preserves every required observation while idle neighbors of an always-active primitive stop executing. Freeze a fixture that activates, settles, then idles; compare traces with the reference and separately assert expected evaluation counts. A deliberately retained activation flag must fail the count check even if values remain correct. This tests both semantic preservation and the claimed reduction in work.

## Research findings and their implications

These are primary-source practices we can reuse. The plan that follows is our proposed application of them, not a claim that upstream projects already validate Chiselator.

| Source finding | Application |
| --- | --- |
| LLVM separates unit, small regression, and whole-program tests; uses lit for regressions and prefers them for IR transformations | Apply that separation with Rust runtime unit tests, C++ compiler/helper tests, lit/FileCheck and end-to-end design tests. [LLVM testing guide](https://llvm.org/docs/TestingGuide.html) |
| Verilator documents success and expected-failure regressions, waveform comparison, and its regression driver | Test rejected programs and diagnostic behavior alongside successful simulations. [Verilator internals](https://github.com/verilator/verilator/blob/master/docs/internals.rst) |
| sv-tests organizes focused tests by SV features and supports multiple tool runners | Import a pinned, reviewed subset as a conformance baseline; record whether each result checks parsing, elaboration, or execution. [sv-tests](https://github.com/chipsalliance/sv-tests) |
| cocotb specifies callback phases and documents different value-change trigger behavior with Verilator | Define observation points before comparing traces; one simulator adapter cannot serve as the oracle for every callback. [cocotb timing model](https://docs.cocotb.org/en/stable/timing_model.html) |
| actsim exposes seeded random timing, randomized arbitration choices, and SDF annotation | Pin backend settings and distinguish deterministic replay from exploration of legal async outcomes. [actsim documentation](https://avlsi.csl.yale.edu/act/doku.php?id=tools:actsim) |
| Verismith generates valid Verilog and reduces failures; libFuzzer supports coverage-guided fuzzing with deterministic targets | Combine valid design generation with byte-level robustness fuzzing and preserve minimized counterexamples. [Verismith](https://github.com/ymherklotz/verismith), [libFuzzer](https://llvm.org/docs/LibFuzzer.html) |
| Reproducible Builds defines reproducibility in terms of identical artifacts from specified inputs and environment | Separate reproducible simulation results from bit-for-bit reproducible release builds. [Definition](https://reproducible-builds.org/docs/definition/) |
| MCP Inspector offers a CLI for exercising tools and resources | Use a pinned client for protocol smoke tests, with our own job-lifecycle assertions. [Inspector CLI](https://github.com/modelcontextprotocol/inspector/blob/main/clients/cli/README.md) |

For SV semantic disputes, consult the selected language edition and document the applicable clauses. IEEE 1800-2023 is available through the IEEE GET program. This research reviewed its availability, not the full language standard; clause-by-clause review is an implementation prerequisite. [Accellera announcement](https://www.accellera.org/news/press-releases/394-accellera-announces-ieee-1800-2023-standard-available-through-ieee-get-program).

## Establish the executable specification first

Before relying on a differential test, define what it compares. Maintain a versioned support catalog with each language feature, CIRCT operation, primitive, and external interface marked supported, rejected, or experimental. A frontend accepting an operation does not make the entire simulation path supported.

Each supported entry requires its import/lowering/runtime constraints, value model, timing behavior, observation points, positive test, boundary test, negative test where applicable, and owner. Required stage coverage is an intersection: import success alone cannot satisfy execution coverage.

Publish contracts for integer time resolution and overflow, delta/phase processing and re-entry, initialization, memory collisions, reset priority, delayed payload capture and cancellation, driver resolution, callbacks, and termination. Every intentional restriction must either be rejected or appear as an explicit supported mode. Deterministic ordering must not be presented as proof that a racing SV program has a unique language-defined result.

The reference evaluator should execute tiny hand-authored models with an independently written queue and arbitrary-width value implementation. A small Python interpreter is a practical starting point. It may consume the documented model format but must not reuse the production queue, activity algorithm, arithmetic lowering, or event cancellation helpers. Keep hand-authored inputs and expected traces to avoid making production compiler output the sole specification.

### Oracle selection

An oracle is the source of the expected result. No single one covers this project.

| Test subject | Primary expected result | Cross-check and limitation |
| --- | --- | --- |
| Scheduler, delay, reset, callbacks | Reviewed contracts and small reference evaluator | Icarus/another event simulator on a demonstrated common subset; review disagreements against the language contract |
| Ordinary clocked SV | Exact outputs at agreed stable sample points | Verilator and, where supported, Icarus from original source; pin flags, initialization, and semantics |
| Chisel path | Independently specified counters/FIFOs/arithmetic and transaction scoreboards | Compile emitted SV with another engine; this still shares Chisel elaboration, so it cannot alone validate that frontend |
| Activity tracking and LLVM optimizations | Reference traces plus native full-scan execution | Full-scan/tracked agreement only isolates optimization bugs; both may share a compiler or scheduler defect |
| Native async primitives and channels | Explicit state-machine contracts, safety properties, expected event traces | ACT on matched models/settings; transaction equivalence does not establish gate hazard equivalence |
| Bundled-data timing | Steps 1–3: independently derived inequalities and behavioral delay fixtures with declared assumptions | Step 4 only: mapped implementation, STA and annotated dynamic checks with matched library/corner; no physical evidence prerequisite for functional tests |
| GSIM comparisons | Chiselator reference/other validated engine on the overlap | GSIM is a useful additional comparator and benchmark, not an authority over SV or async semantics |

Optional formal equivalence may later strengthen restricted transformations, but it is outside the initial simulator validation dependency set. EQY and transitive Yosys helpers remain excluded from core library/simulator tests. Any separately approved physical-build equivalence lane must qualify its own export path, assumptions and exact scope; Boolean equivalence cannot establish async timing/hazard correctness. Begin with independent reference, source-level differential and optimized/unoptimized comparisons.

Record oracle lineage per claim: shared elaborator, normalized IR, scheduler, cell library, stimulus generator and comparator. Two engines consuming the same incorrectly lowered plan do not independently validate lowering. STA and dynamic simulation using the same wrong cell data do not validate those data. Critical semantic families require reviewed hand-derived cases and at least one separately implemented checker/reference; source import additionally requires source-level comparisons on the shared supported subset. Tool majority voting is not an oracle. Reduce every disagreement and resolve it against the contract or physical evidence; retain an unresolved result as a blocked claim.

Our contract can itself be wrong. Review SV scheduling/value fixtures against the selected language clauses and Chisel expectations against independent intended circuit behavior. A convenient implementation rule that disagrees with the language must become an explicit rejected/restricted capability or be corrected; rewriting the reference to match production cannot establish conformance. Preserve disagreements and their resolution evidence alongside the regression.

### Compare the right observations

Use exact integer values and timestamps. Normalize signal identities through the source map; record width, signedness, value mode, initialized status, and observation point. Internal scheduler comparisons include physical time, delta, phase, and ordered causal events. External comparisons use only mutually observable phases: equal internal delta counts are not assumed across engines.

Compare every selected event or sample, assertions, termination reason, and transaction sequence. A final-state hash is a quick integrity check, not enough to detect transient errors or lost transactions. On mismatch, preserve the first divergence and bounded preceding events. Compare whole selected traces for small fixtures; use streaming comparison and chunk hashes with retained mismatch windows for larger runs.

Race-free tests expect exact equality. Tests intentionally exercising legal nondeterminism check a specified set of outcomes and safety properties. Do not discard inconvenient mismatches as races without a reduced reproducer and reviewed explanation. Do not normalize away real glitches in a mode that promises to observe them.

## Directed accuracy suites

### Library qualification before the simulator

These suites qualify chisel-async's catalog and execution views, separately from simulator support. A later native binding must pass the existing cases plus the runtime suites below. Shared schemas may describe interface layout, but reference behavior must remain independently implemented.

| Suite | Required evidence |
| --- | --- |
| LIB-01 API and elaboration | Typed protocol directions, generic/nested payloads, widths, reset/initialization parameters; invalid protocol mixing and unsupported payloads fail at the documented layer |
| LIB-02 Primitive behavior | Independent C-element/latch/delay/mutex/completion contracts, bounded exhaustive transitions, event/reset boundary traces and activated known-bad controls |
| LIB-03 Composition and protocols | Four/two-phase channels, explicit converters, QDI validity/spacer, stage/FIFO capacity, fork/join pairing, routing/arbitration, clocked/CDC and memory/I/O contracts; exactly-once effects under backpressure/reset |
| LIB-04 Timing and provenance | Stable primitive/endpoint IDs and manifest survive Chisel/CIRCT/RTL paths; dropped constraints fail; external timed views distinguish functional tests from characterized physical evidence |
| LIB-05 Stack and platforms | Pinned Chisel/Scala/JDK/firtool and qualified external-simulator matrix on native Windows/Linux/macOS; later native/ACT/GPU lanes require actual backend evidence, not mocks or fallback |
| LIB-06 Consumer packaging | Independently buildable library, bundled SV resources, local published artifact consumed by a clean sample, schema/version mismatch rejection, notices and upgrade/migration fixtures |

Every required catalog row needs active checks and retained evidence, not merely a compiling declaration. Record planned/implemented/qualified/unsupported status by component, mode and backend. A missing future backend does not block the standalone external-simulator library release, but cannot be advertised as compatible. Full-stack compatibility requires all claimed lanes. No backend is the sole oracle for a library whose models it executes.

### Runtime qualification

The IDs below name proposed suite families. Each row expands into small fixtures, usually with a successful case and an injected error. They are not claims about existing tests.

| Suite | Required cases and pass condition |
| --- | --- |
| SEM-01 Values | Widths 1, 7, 8, 31, 32, 33, 63, 64, 65, 127, 128, 129 and larger random widths; signed extension, truncation, concatenation, selection, overflow and shifts at/above width. Division by zero and unknown values follow explicit supported policy, never accidental host/LLVM behavior. |
| SEM-02 Clocked state | Posedge/negedge, sync/async reset, coincident domain edges, register swap, reset/edge priority, clock pause/stretch/resume, reset while paused. All state samples use the specified visibility rules. |
| SEM-03 Scheduling | Blocking/NBA, NBA causing new active work, repeated phase re-entry, `#0`, event controls, waits already satisfied, delayed assignment payload capture, timed wakeup cancellation, same-time multiple events, exact `run_until` boundary, settle/resume equivalence. |
| SEM-04 Storage | Memory read/write latency, byte enables, signed addressing policy, range boundaries, initialization files, and every supported same-address read/write and multiple-write collision mode. Unsupported ambiguity fails explicitly. |
| SEM-05 Frontends | Equivalent Chisel/SV examples; parameters, includes, packages, supported aggregates and module bindings. Illegal CIRCT operations, unresolved modules, unsupported SV constructs and malformed annotations diagnose source locations. |
| SEM-06 Execution plans | Bad IDs, overlapping storage, invalid widths/alignment, incompatible ABI, missing kernels, malformed subscriptions, time overflow and invalid time conversion are rejected before unsafe execution. |
| OPT-01 Activity | Always-active primitive beside cold regions, bitmap boundaries and partial words, duplicate activations, fanout, initialization flags, clearing/re-activation in the same timestamp. Assert both outputs and activation counters. |
| OPT-02 Transformations | Narrowing, constants, dead logic, region splitting/merging, repeated instances, hot/cold policy, and hierarchy preservation. Compare full-scan/tracked, quick/optimized code and instrumentation on/off; side effects occur exactly once. |
| ASY-01 Primitives | C-element hold/set/reset, latch transparency/closing, delay line, mutex exclusivity and reset. Exhaust small input/state sequences, including reset during a pending transition and reads before initialization. |
| ASY-02 Protocols | Four-phase order, dual-rail validity/spacer, repeated identical payloads, backpressure, reset abort, transaction duplication/loss/reordering. Behavioral, bundled, QDI and wrapped clocked implementations pass the same scoreboard. |
| ASY-03 Time and progress | Transport versus inertial pulse handling, canceled deliveries, zero-time nonconvergence, legitimate positive-time oscillation, future wakeups, environmental stalls and genuinely blocked obligations. Different outcomes retain distinct diagnostics. |
| ASY-04 Choices | Simultaneous mutex requests, recorded choices, seed variation, bounded schedule exploration. Never grant both; preserve data and declared fairness assumptions. A random policy alone does not guarantee bounded service. |
| ACT-01 Coordination | Equal-time bidirectional exchanges, zero lookahead, differing time units, backend unknown values, resets, message fragmentation, disconnect/crash/timeout, absent optional ACT. No advance beyond a safe frontier. |
| TIM-01 Provenance | Source constraint survives elaboration, inlining, splitting and replication with correct model endpoints. Missing/ambiguous endpoints, missing delay assumptions and incompatible units fail; no physical views required. |
| TIM-02 Model timing fixture | Behavioral stage with hand-derived passing/failing relative timing under declared delays. Too-short control, too-slow data and hold violations fail at expected boundaries, including equality/one-tick offsets; no cell mapping, PDK, STA or SDF dependency. |

The GSIM stale-flag report motivates OPT-01, but its patches were not available for inspection. Reconstruct the failure pattern from the reported behavior and label its provenance. A correctness-only trace may miss needless execution of pure logic; activation-count assertions are essential. Profiling fixtures must produce known nonzero useful/wasted activation counts and compile the instrumented build in CI.

Bundled-data tests should state the inequality being checked, such as earliest capture-control arrival exceeding latest data-valid arrival plus the receiving element's required margin, together with hold/reset obligations. Select corners consistently with the actual timing model; arbitrary mixing of incompatible extrema is not a substitute for a defined analysis. Include annotation loss and wrong pin mapping as deliberately failing fixtures.

QDI tests must declare environmental and isochronic-fork assumptions. Zero-delay settling alone does not establish QDI correctness, and finite random-delay sampling cannot prove it. Similarly, modeled synchronizer latency or arbitration does not reproduce analog metastability. These limits belong in test reports as well as documentation.

## Generated tests and tests of the checkers

Use three complementary generation paths:

1. **Valid designs:** a constrained generator for combinational expressions, small clocked machines, and separately defined async networks. Restrict the external comparison corpus to common supported, initialized, race-free semantics. Record rejected cases separately so a shrinking supported subset cannot look like an improving pass rate.
2. **Stateful sequences:** generate drive/settle/advance/reset/read/cancel operations against the session API. Compare the production state machine with the reference and exercise invalid call sequences deliberately.
3. **Malformed inputs:** coverage-guided fuzzing of plan loaders, config, source annotations, declared timing data, report readers and MCP messages. Add SDF parser fuzzing when that step 4 capability is implemented. Bound time, recursion, allocations and output; distinguish clean rejection from crash or hang.

Start with retained seeds and short fixed PR campaigns; expand random generation nightly. Seed derivation is versioned and independent of worker assignment. Retain the generated design and stimulus as well as the seed, because generator changes can make old seeds produce different inputs. libFuzzer's deterministic-target guidance is particularly relevant to reusable sessions. [libFuzzer documentation](https://llvm.org/docs/LibFuzzer.html).

On failure: save artifacts, reproduce with the pinned environment, minimize the design and stimulus while preserving legality and the mismatch, classify the responsible layer, then add a permanent fixture before fixing it. A reducer must preserve the race-free or timing assumptions that made the comparison meaningful. Upstream bugs receive a minimized upstream report and a locally tracked regression or capability restriction.

Metamorphic tests compare executions that should agree under stated conditions: one long advance versus segmented advances; cache cold versus warm; instrumentation on versus off; independent job counts; and substitution preserving declared transactions. For hierarchy/name changes, remap semantic IDs and choice streams or use nonrandom fixtures; renaming must not accidentally change the random experiment.

Maintain deliberate defect variants to validate the checkers: drop an activation, leave a flag set, apply NBA early, deliver a canceled edge, change a delayed payload, reuse a random stream, lose a transaction, drop a timing constraint, corrupt a cache entry, and convert timeout into PASS. Each named mutant must trigger its intended check. This measures whether the test detects the defect it claims to cover, beyond executing the affected line.

### Prevent tests that pass without exercising their claim

A required fixture declares evidence that its stimulus, design and checker ran: expected reset exit, relevant edges/transactions, assertion antecedent hits, comparison sample count and explicit completion. Use case-specific expected counts or justified minima; a generic nonzero count is insufficient. An intentionally idle fixture instead records the actions that establish idle and its expected zero work. Zero assertions failing is not useful when no assertion was exercised.

For MCU tests, require a firmware completion marker plus the expected retirement/effect sequence and planned instruction/branch/memory bins. Compare against independent inputs and an independently specified ISA model; the production retirement stream cannot generate its own expected answer. A trace that ends early, repeats records, stays in reset or emits a completion marker without the required work must fail. Test live environment assumptions by deliberately withholding memory acknowledgement and by violating a declared timing bound; neither may yield ordinary PASS.

Validate the measurement pipeline as well as the engine:

| Control | Required detection |
| --- | --- |
| Remove/change/duplicate/reorder a reference trace record, including the final record | Comparator reports the first mismatch or length/completeness error |
| Feed an empty trace or accidentally compare a file with itself | Required sample checks and expected/actual provenance checks reject the experiment |
| Disable a required monitor or skip its triggering stimulus | Monitor registration/hit requirements fail |
| Inject a wrong value, early capture or lost transaction | Intended semantic/protocol checker fails, not merely an unrelated crash |
| Omit a case, duplicate a seed result, or truncate the final report | Expected-case inventory and unique case/attempt identities expose incomplete evidence |
| Mark a failing job successful in an intermediate report | Independent outcome reconciliation rejects the report |

These are mandatory controls for the harness/report release lane (INT-04 and DUR-03), with semantic controls owned by their SEM/OPT/ASY/TIM suites. A defect variant counts as detected only if it built, reached its target and triggered the expected check. Separate equivalent/inapplicable mutants with a reviewed reason; do not silently remove survivors. Preserve both the simulator outcome and the harness verdict: a correctly detected bad design may make a negative test PASS while its simulated job remains FAIL.

### Exhaust small domains and explore timing boundaries

Enumerate all input/state combinations for small arithmetic and primitive fixtures where feasible, and all legal event-order choices within an explicitly recorded depth/time bound for tiny handshake networks. Include initialization, simultaneous events, reset at each protocol phase, over-width arithmetic and one-tick-before/equal/one-tick-after timing boundaries. Report explored and total bounded states/transitions when known; an exhausted budget means incomplete exploration. No solver or Yosys dependency is required for a small explicit enumerator.

For nondeterministic arbitration, checking that every observed outcome is legal is only one direction. Tiny bounded tests must also exercise each specified alternative; an implementation that always chooses one winner cannot claim full choice exploration. Fairness or outcome probabilities are tested only when the contract explicitly promises them. Keep digital boundary tests separate from continuous physical timing claims.

### Random testing and statistical honesty

Use adversarial directed cases and stratified random campaigns covering activity, width, fanout, clock relations, reset phase, delay margin and backpressure. Publish generated/accepted/rejected/executed counts, unique designs, attempted seeds, missing cases and per-stratum outcomes. A million cycles of one design are not a million independent designs. Selection by a generator's legality filter changes the tested population and must be disclosed.

Define an independent trial as a fresh complete design/stimulus/delay sample under a fixed declared distribution, if that independence assumption is justified. Replaying a seed provides reproducibility evidence, not another independent observation. Coverage-guided/adaptive fuzzing, related seeds and reused designs generally do not justify a simple binomial confidence bound. Report their exploration and discovered defects without attaching an invented probability of correctness.

For a fixed campaign of n independent identically distributed trials with zero observed failures, the one-sided 95% exact binomial upper bound is `p_upper = 1 - 0.05^(1/n)` (approximately `3/n`). At n = 10,000 it is about 0.03%. This bounds the probability of a **detected failure under that sampling distribution and checker**, not the probability that the simulator is wrong, nor silicon failure rate. NIST documents exact binomial confidence limits; this zero-failure expression follows by solving `(1-p)^n = 0.05`. [NIST exact binomial limits](https://itl.nist.gov/div898/software/dataplot/refman2/auxillar/exacbino.htm).

Do not stop or extend sampling until a favorable bound appears. Fix the sample count/stopping rule in advance, or specify a justified sequential method before running. Stopping early to preserve a discovered failure is allowed and reported as incomplete. Predeclare separate claims and any multiple-comparison treatment; no pooled confidence claim over arbitrary heterogeneous strata. A single unexplained semantic failure blocks the affected support claim regardless of the aggregate pass rate.

### Detect optimistic physical models

Two-state seeded initialization can hide reset/X-sensitive behavior. Exhaust both initial values in tiny relevant state spaces and use external four-state comparisons for reset/X-sensitive boundary fixtures where supported. A required hardware conclusion that depends on unknown propagation remains unqualified if the two-state contract cannot represent it. Keep primitive initialization errors, missing timing checks and unsupported analog effects visible rather than substituting benign defaults.

For bundled-data timing, sweep control/data delay and setup/hold margins around each expected boundary. The checker must transition from passing to failing at the independently derived boundary, including equality policy and time precision. Include correlated corner scenarios and adversarial slow-data/fast-control cases only under explicitly justified model assumptions; independent uniform random gate delays do not represent a calibrated manufacturing distribution. Record sensitivity to initialization, reset, delay policy and observation scope.

TIM-02 establishes model-level timing-checker behavior under declared assumptions in step 3. Step 4 physical claims additionally need independently justified cell characterization and references appropriate to the claim, such as qualified transistor-level characterization or measured data. Such evidence must include uncertainty and its applicable voltage/temperature/load/slew domain. Physical calibration data and validation cases must be separate; never tune a delay model to the same examples used to claim predictive accuracy. Those physical checks do not gate steps 1–3, and functional completion cannot be reported as physical qualification.

## Reproducibility and replay

### Three separate guarantees

| Guarantee | Proposed MVP requirement |
| --- | --- |
| Exact rerun | Same pinned executable/model, stimuli, settings and recorded choices reproduce canonical observations and termination. Changed dependencies are refused as an exact replay. |
| Semantic portability | Supported deterministic cases agree across native Windows x86-64, Linux x86-64 and macOS arm64 and allowed optimization modes. Optional backends and future within-simulation threading must qualify the same contract. |
| Reproducible build | Rebuild the release in two clean environments using the same locked inputs and compare unsigned payloads. Before claiming bit-for-bit reproducibility, remove or account for build paths, timestamps, archive order and other variance. |

The first two are P0 simulator release gates. Attempt the third in release CI and publish its status; do not confuse checksums or a successful rebuild with bit-for-bit reproducibility. Signed package envelopes may vary and need a declared comparison boundary. [Reproducible Builds definition](https://reproducible-builds.org/docs/definition/).

### Required replay bundle

Record source and transitive include hashes; elaborated inputs; memory/stimulus files; bindings and primitive versions; exact tool/CIRCT/LLVM/Chisel/ACT revisions; target/CPU features and ABI; compiler flags and pass pipeline; initialization/value/time/observation modes; library/SDF/STA identities; resolved config and plusargs; generator/PRNG algorithm versions and seeds; external input/choice log; executable/model hashes; and schema versions.

Archive the small fixture inputs or content-addressed references to retained artifacts, not just hashes. A hash cannot recover a vanished file. External harnesses must supply deterministic stimuli or record their inputs. Record permitted environment settings explicitly without dumping unrelated secrets. Keep performance measurements separate from canonical semantic output.

Random streams belong to semantic objects and decision kinds, with counters advanced at defined model events. Host call order, allocation addresses, tracing, cold-region skipping and unrelated object activity must not change a decision. Test these invariants. Exact choice-log replay validates that a recorded choice is still legal; it must not force an impossible execution after a semantic change.

### Reproduction matrix

| Suite | Perturbations and expected result |
| --- | --- |
| REP-01 Replay | Fresh process repeated runs, replay of failing seeds, deliberately changed include/model/library/version, missing artifact. Equality or precise incompatible-input error. |
| REP-02 Environment | Locale/timezone, working directory, path spaces/Unicode, allocator layout, process launch order, and `-j 1` versus concurrent independent jobs. Canonical outputs agree. |
| REP-03 Engine modes | Cache cold/warm, quick/optimized kernels, tracked/full-scan, waves/profiling off/on within an equivalent observation contract. Observations agree. |
| REP-04 Random isolation | Add unrelated region or observer, vary optimization, replay mutex decisions and delays. Mapped semantic objects keep the same streams. |
| REP-05 Release inputs | Lockfile honored, two clean builds, offline rerun, restored artifact bundle, corrupt/truncated cache and concurrent cache writers. No silent reuse of incompatible code. |

For a wall-time timeout, reproduce the failure class and available evidence rather than promise the same last simulated event on different machines. Exact stopping-point replay uses event/simulated-time limits or a recorded cancellation boundary. Report deterministic execution separately from wall-clock performance variance.

## Optional backend qualification

The architecture reserves optional GPU execution and independent session batches. These checks become mandatory for each advertised accelerator capability; they add no GPU requirement to the CPU MVP and do not change the 32 P0 requirements below.

| Check | Acceptance evidence |
| --- | --- |
| Backend eligibility | Unsupported operations, callbacks, value/timing modes and observation requests fail an explicit GPU request. Automatic selection reports a CPU fallback reason; fallback does not count as a GPU pass. |
| Semantic equivalence | Eligible clocked and async fixtures match the CPU/reference at the declared observation points, including initialization, phase order, delayed payloads and legal recorded arbitration choices. |
| Batch independence | Batch size, lane compaction, job order and completed/failed/canceled neighbors do not change a session's random choices, state or result. Cover partial batches and memory limits. |
| Ownership and completion | Reads wait for publication; callbacks run at their required phase; cancellation and destruction do not free in-flight buffers. Inject device failure and verify honest partial results without silent migration or repeated side effects. |
| Artifacts and installation | Backend/target/layout mismatches cannot hit cache; incompatible devices/drivers fail clearly; CPU packages run without GPU dependencies. Test the declared device/toolchain matrix and use device memory/race checking supported by that toolchain. Host sanitizers alone do not qualify device code. |
| Replay and performance | Preserve failing inputs/choices for supported CPU semantic replay. Compare complete cold/warm turnaround, transfers, tracing and reports against parallel CPU runs, with equal semantics and observation scope. Retain device-specific failures as such. |

Run actual hardware tests before promoting GPU support. Mock executor tests can validate selection and lifecycle, but cannot establish device correctness. Record skipped device lanes explicitly. Accelerated async runs retain exact event semantics; coarse time stepping or dropped pulses cannot be accepted as performance optimizations of an exact mode.

## Product integration and long term reliability

| Suite | Required evidence |
| --- | --- |
| INT-01 C ABI | Separately compiled C/C++ consumers and Rust wrappers; public and internal ABI layout/version checks; handle ownership, buffer lifetimes, two independent sessions, callback/reentrancy rules, errors after finish and cancellation. Exercise actual compiler/JIT kernels and prevent panic/exception escape. |
| INT-02 Harnesses | Pinned cocotb/svsim versions; clocked and handshake tests; callback phase and read-only write rules; fatal/assert/finish behavior; memory files; consistent defined sample points across harnesses. |
| INT-03 CLI | Every P0 command, help/offline doctor, config precedence, filelists/includes/parameters, bad arguments, exit codes, test filtering, partial sweeps, fail-fast and cancellation. No log contamination of JSON stdout. |
| INT-04 Reports | Schema validation, independent VCD/FST readback, selected signal/transition checks, source mappings, exact counts and units, JUnit failure/error distinction, missing metrics and incomplete runs. Incompatible coverage results cannot merge. |
| INT-05 MCP | Discovery/schema/protocol errors, bounded outputs, identical CLI/API semantic results, polling, repeated cancellation, disconnect policy, concurrent jobs and stderr/stdout separation. Test the documented protocol version with Inspector and a minimal client. |
| DUR-01 Session endurance | Repeated create/load/run/cancel/destroy; JIT resource release, multiple sessions, ACT children and file descriptors return to expected baselines. Reset is not used as a substitute for destruction testing. |
| DUR-02 Long simulation | Long clocked and async runs; counters near overflow; queue growth/drain; cancellation tombstone cleanup; trace rotation/backpressure; no unbounded growth for bounded fixtures. |
| DUR-03 Fault injection | Full output disk, write permission loss, backend crash, interrupted compilation/cache publication, missing libraries, bad manifests and truncated reports. Preserve an honest partial/error result and clean up child processes. |
| DUR-04 Compatibility | Previous supported report/API fixtures, incompatible model/cache rejection, upgrade/reinstall, optional dependency absence and pinned/upstream-canary toolchains. Never silently change replay semantics. |
| PKG-01 Distribution | Clean native Windows x86-64, Linux x86-64 and macOS arm64 archive installs; no compiler/network/ACT/Yosys needed for built-in SV; separate JVM/Python lanes; relocation/uninstall/checksums/notices and declared system baselines. WSL is optional evidence only. |

INT-02 integrates the separately maintained [Pi power-supervisor MCU](async-mcu.md) with Chiselator. Its RTL uses pinned chisel-async releases; its own repository owns firmware, board profiles and application fixtures. Pin all three project revisions in test manifests. The project owner will add the MCU and library repositories; their absence is pending implementation, not passing integration evidence. Keep independent ISA and supervisor references outside production behavior paths. Functional simulation does not depend on ACT or a PDK.

The application suites below refine INT-02 and the release's complete-application gate. They do not add new simulator P0 feature IDs. MCU-01–04 run first externally at C0, then in Chiselator at S0, using the same firmware and equivalent observable contracts. MCU-05 and MCU-06 are deferred step 4 gates for real Pi compatibility and physical claims, not prerequisites for C0 or S0.

| Suite | Required evidence |
| --- | --- |
| MCU-01 Firmware and execution | RISC-V RV32E/C architectural and generated instruction tests use a qualified independent reference; cover registers, arithmetic, mixed instruction widths, memory/fault semantics and exactly-once MMIO effects. Linked supervisor firmware, helpers and worst-case stack fit measured budgets (provisional 2 KiB ROM/256-byte RAM); retirement, committed I/O and event wait/wake match the declared execution environment |
| MCU-02 Normal power lifecycle | Cold boot/ready, button and scheduled wake, requested and OS-initiated shutdown, reboot and complete power cycle; independent policy oracle verifies late acknowledgement before switch-off |
| MCU-03 Fault and timeout policy | Boot hang, stale/missing heartbeat, early/stale/absent shutdown acknowledgement, low supply, timer failure/overflow and bounded retries; forced-off never reports graceful completion |
| MCU-04 Async and reset integrity | CPU reset preserves the declared retained enable state; reset in every relevant phase, simultaneous event/clear/wait, backpressure and replayed delay variation do not lose events or duplicate effects |
| MCU-05 Real Pi integration | Versioned Pi/OS/kernel/overlay/board profile and real-board measurements qualify the simulated environment, wake/shutdown/reboot and electrical power-off behavior |
| MCU-06 Physical feasibility | Revised memory/control area estimate, mapped floorplan, preserved async constraints, routed timing/DRC/LVS and whole-supervisor power/reset/watchdog measurements before physical claims |

The [step 4 PHY-01–06 suites](chip-build-plan.md#tests-and-evidence) retain view/preservation, physical relative timing, memory/boot, test/layout, reproducible handoff and board/silicon evidence for later. Their owners, dependencies and P1–P3 schedule will be addressed in step 4. None belongs to the 32 functional simulator P0 requirements. Do not require a physical stage fixture to pass functional release gates or claim physical closure from behavioral tests.

Inject premature switch-off, a lost event and stale shutdown completion as negative controls and require the intended checker to fire. The Pi environment must include nonresponsive and delayed cases; an always-cooperative stub is insufficient. Compare deadline behavior against independent timer events, not CPU instruction counts. Sudden power loss without backup energy is not a graceful-shutdown promise. TIM-02 qualifies declared model timing; physical stage timing and revised area estimates wait for step 4.

Run AddressSanitizer/UndefinedBehaviorSanitizer on C++ compiler/native components and leak checks where supported; use separately qualified Rust and mixed-language instrumentation lanes and a separate ThreadSanitizer build for supported concurrent paths. Pin compatible toolchains and document which modules are instrumented. ASan detects memory errors through compiler instrumentation and a runtime, while TSan targets data races. [ASan](https://clang.llvm.org/docs/AddressSanitizer.html), [TSan](https://clang.llvm.org/docs/ThreadSanitizer.html).

Rust runtime tests run through Cargo without CIRCT. Review and test each `unsafe` wrapper's ownership, aliasing, bounds and thread-affinity obligations. In `tests/ffi`, compare C and Rust sizes/alignment/offsets; inject callback and compile failures; test exactly-once release, attempted unload with active sessions, and debug/release arithmetic equivalence. Test contained unwinding panics and process-level abort supervision separately. A panic must not escape the C ABI or leave a session advertised as safely resumable. Mixed-language tests exercise real kernel calls; mock handles alone cannot validate JIT lifetimes.

**Instrumenting the host does not automatically instrument JIT-generated kernels.** Plan an explicitly instrumented LLVM lowering or a test-only compiled-kernel lane, plus guarded layouts and boundary tests. Prove the chosen lane detects an intentionally bad generated memory access before claiming generated-code sanitizer coverage. Keep this engineering probe in M0/M1.

Proposed starting endurance budgets: 10,000 session lifecycles nightly; an 8-hour weekly mixed clocked/async soak; and a 24-hour release-candidate soak. Calibrate these after the first working slice. Measure live allocations, queued events, JIT code, child processes and open handles as well as RSS. Use repeated batches after warmup and fixture-specific envelopes; bounded allocator retention is different from continuing resource growth.

Keep release binaries, dependency locks, report schemas and minimized regressions for every supported release. Retain ordinary CI artifacts for a proposed 30 days and unresolved failure bundles until resolution; retain small bug fixtures in Git permanently. Serialized model/cache formats may be invalidated across versions if documented; public result/API compatibility requires explicit version negotiation and tests. Checkpoint compatibility testing begins when that P1 feature exists.

## MVP requirement traceability

This table covers the complete P0 feature list. Suite ownership becomes a named maintainer before implementation; a mapped but unimplemented suite does not satisfy a requirement.

| Requirement IDs | Main suites |
| --- | --- |
| SIM-01 | SEM-05, INT-02 |
| SIM-02, SIM-04 | SEM-02, SEM-04 |
| SIM-03 | SEM-03, ASY-03 |
| SIM-05 | SEM-01, ASY-01, ACT-01 |
| SIM-06 | SEM-06, OPT-02, REP-05, PKG-01 |
| ASYNC-01, ASYNC-02 | LIB-01, LIB-02, LIB-03, LIB-04, LIB-05, LIB-06, ASY-01, ASY-02 |
| ASYNC-03 | ASY-02, ASY-03, INT-04 |
| ASYNC-04 | ASY-03, ASY-04, REP-01, REP-04 |
| ASYNC-05 | ACT-01, DUR-03, PKG-01 |
| TIME-01 | TIM-01, TIM-02 |
| API-01 | INT-01, DUR-01 |
| API-02, API-03, API-04 | SEM-03, INT-02 |
| API-05 | ASY-02, INT-02, INT-04 |
| CLI-01, CLI-02 | INT-03, PKG-01 |
| CLI-03, CLI-04 | INT-03, DUR-03 |
| CLI-05 | REP-01, REP-05 |
| OBS-01, OBS-02 | INT-04, TIM-01 |
| OBS-03, OBS-04 | INT-04, ASY-02, TIM-02 |
| OBS-05 | OPT-01, OPT-02, INT-04 |
| DIST-01, DIST-02, DIST-03 | PKG-01, DUR-04, REP-05 |
| MCP-01, MCP-02 | INT-05, DUR-01, DUR-03 |

## Harness architecture and CI policy

Use the architecture's proposed directories: Rust unit tests within `crates`, plus `tests/unit`, `tests/ffi`, `tests/lit`, `tests/reference`, `tests/integration`, `tests/differential`, and `tests/packaging`. Add `tests/contracts` for feature metadata and expected observations, `tests/corpus` for reduced bugs, and `tests/stress` for endurance/fault injection. Cargo runs Rust tests; CTest coordinates C++ compiler/helper tests; lit/FileCheck verifies transformations and diagnostics; Python orchestrates external tools, trace comparison, replay and packaging. The developer build/test entry point combines these lanes with shared result schemas and artifact management.

A proposed machine-readable case record contains `id`, `requirements`, `owner`, `semantic_contract`, `fixtures`, `required_capabilities`, `oracle`, `observation_points`, `seed_policy`, `limits`, `expected_status`, `expected_diagnostics`, and `ci_tiers`. Add `experiment_revision`, `oracle_lineage`, `required_activity`, `expected_observation_count`, `controls`, and `review_status` for scientific qualification. Campaign records define the sampling/stopping rules and expected case inventory. A linter rejects missing requirements, nonexistent fixtures, unsupported claimed capabilities and empty selected suites. A feature cannot become supported until all required stages pass.

Use PASS, FAIL, ERROR, TIMEOUT, CANCELED and explicit NOT_RUN/SKIP outcomes. Negative tests pass only for the expected diagnostic and phase; any crash or arbitrary nonzero exit is insufficient. Missing required oracle infrastructure blocks the gate. Optional ACT can be absent in native-only tests, but the ACT qualification lane must actually run before claiming ACT support.

| Tier | Proposed workload | Initial budget and policy |
| --- | --- | --- |
| Local | Unit, focused compiler regression, tiny semantic traces | Target under 2 minutes with an existing build; no frontend needed for runtime-only tests |
| Pull request | Cargo runtime tests, compiler/ABI tests, native semantic smoke on all three targets, affected integrations, fixed fuzz seeds, replay smoke, profiling build, qualified sanitizer lanes, comparator and required-activity controls | Target 15 minutes on warm workers; mandatory semantic smoke even for narrow selection |
| Nightly | Full supported feature corpus, external differential tests, fresh fuzz seeds, random timing, ACT/cocotb/svsim, lifecycle stress, broader sanitizer lanes | Initial 4 worker-hours fuzz budget; record completed cases/coverage, not just elapsed time |
| Weekly | Endurance, dependency canary, timing fixtures, native installation/relocation on all three targets, clean rebuild comparison | Isolated workers; upstream canary failures do not change locked toolchains automatically |
| Release candidate | All P0 lanes on exact candidate packages, replay from previous artifacts, defect and harness controls, frozen evaluation campaign, compatibility and 24-hour soak | Publish evidence and claim review; required failure, missing control or missing lane blocks release |

These budgets are planning assumptions, not measurements. Separate cold CIRCT builds from warm PR runtime targets. Use immutable dependency cache keys and pinned tool paths. Test a new toolchain in a canary lane; update the lock only after semantic, integration and replay evidence passes.

Flaky semantic failures are defects, not green results after retries. Infrastructure retries keep the first result. A quarantine requires an issue, owner, expiry and visible status; quarantining a required correctness case cannot satisfy its release gate. Fixing a failing test by replacing its expected trace requires contract review and independent evidence.

### Coverage and release evidence

Report feature-stage coverage, value/width/phase/primitive-state bins, exercised error codes, differential cases and exclusions, retained random seeds, defect-variant detection, sanitizer coverage, and package lanes. Use code coverage to locate gaps, not as a claim that a percentage establishes correctness.

A release requires all supported P0 contracts tested; all designated defect variants caught for the intended reason; comparator/report controls passing; required activity and observation counts satisfied; independently reviewed oracle provenance; no unexplained differential mismatch or known correctness defect in the supported subset; reproducible selected failing seeds; no unresolved sanitizer finding in covered paths; completed resource and installation gates; and validated reports. An unresolved semantic capability must remain experimental/rejected and cannot count toward an MVP requirement that needs it.

The evidence bundle records exact candidate hashes, test catalog/experiment revisions, oracle lineage and review, planned versus executed cases, control results, required-activity evidence, oracle/tool versions, pass/fail/not-run totals, coverage denominators, failure reproductions, resource trends, supported platforms and limitations. Retain raw observations and the versioned analysis that produces summaries. Keep diagnostics about the circuit separate from failures of Chiselator or its test infrastructure.

Report each claim as supported within its stated scope, refuted, or not established. Maintain distinct evidence for digital semantics, physical model validity and performance; never collapse them into one “accuracy percentage.” A missing physical validation result remains not established even when every digital regression passes. Required semantic claims with missing evidence block release; optional physical/performance claims can remain unestablished without being advertised as supported.

## Controlled performance experiments

Performance gets a separate lane after correctness qualification. Treat it as an empirical comparison with declared conditions and reproducible raw results, consistent with the disclosure principles in SPEC's run rules; these are Chiselator experiments, not SPEC scores. [SPEC run and reporting rules](https://www.spec.org/cpu2017/Docs/runrules.html).

1. Freeze design/input hashes, semantic/observation modes, completion work, tool revisions, flags, CPU/GPU resources, repetition count and statistical method before evaluation. Separate tuning/training, development validation and held-out evaluation inputs. After a held-out case guides a change, record that exposure and use a fresh holdout for a new generalization claim; retain the old case as a regression.
2. Require equal completed architectural work, output correctness and observation/checking scope. Instrumentation-free measurements still verify required outputs and completion. Qualify that mode against an instrumented run of the same artifact/configuration where possible; do not disable assertions in only one competitor. Publish original versus patched GSIM and PGO variants as distinct baselines with their exact patch/profile hashes.
3. Measure cold time to first correct result, warm simulation, total compile/JIT time, peak memory and full turnaround separately. Define cache clearing and warmup. Include GPU preparation/transfers/synchronization and required reports in end-to-end measurements; kernel-only time is separately labeled. Compare GPU batches with equivalent CPU batch throughput as well as per-case latency.
4. Use repeated independent process launches with balanced/randomized competitor order on a controlled host. Record affinity, worker/core counts, memory limits, power/thermal state and background interference where measurable. Select repetition count and uncertainty method using a separate pilot, then freeze them. Retain all runs; exclude only according to predeclared infrastructure criteria and preserve the excluded evidence.
5. Publish per-workload paired ratios, raw times, dispersion and an uncertainty interval appropriate to the sampling unit. Do not treat iterations inside one process as independent machine trials. If a prespecified interval includes no improvement, report the result as inconclusive for a speedup claim. Report practical effect size, not only statistical significance.
6. Publish regressions, unsupported designs, crashes and timeouts alongside successes. A fixed common supported subset may have a clearly labeled geometric mean of per-design speedups, but missing/failed cases cannot silently disappear into that denominator. No cherry-picked best run or unqualified extrapolation to all chips.

Each optimization also needs an off-switch ablation: same inputs and semantics, changed optimization only. Measure profile overhead and hold training costs separate from execution while including them in turnaround claims. Beating GSIM remains a later goal; an incorrect run cannot produce an accepted speedup result.

## Implementation sequence and required effort

Start with chisel-async L0–L2 and LIB-01–06, then RISCay-MCU C0 with external MCU-01–04, before the main engine. Establish reference/trace infrastructure there, then reuse it during simulator M0/M1. Physical P1–P3 starts only in step 4. The estimates below are earlier engineering judgments for simulator validation infrastructure; they do not budget the expanded library, MCU, physical or board work and must be re-estimated after the functional probes, with step 4 estimated later.

| Work package | Deliverable | Estimated effort |
| --- | --- | --- |
| 1 Contracts and catalog | Scheduling/value/observation decisions, first 20–30 tiny semantic cases, support metadata | 1–2 engineer-weeks |
| 2 Independent baseline | Reference evaluator, trace comparator, Cargo/CTest/lit/Python skeleton, ABI and negative-result checks | 2–4 engineer-weeks |
| 3 Differential and replay | Verilator/Icarus adapters, dual-language fixtures, generators/reducer, manifests and preserved failures | 2–4 engineer-weeks |
| 4 Async and timing validation | Primitive/channel corpus, optional ACT coordination checks, behavioral passing/failing timing fixture; physical extension deferred to step 4 | 3–5 engineer-weeks, historical estimate to revisit |
| 5 Product and release qualification | API/adapters/MCP/report tests, sanitizers, endurance, install/upgrade CI and evidence bundle | 3–5 engineer-weeks |

Total initial planning range: **11–20 engineer-weeks**, excluding simulator implementation, major Arc/ACT integration changes, and ongoing corpus maintenance. Split ownership across compiler, runtime/async, and integration/release engineers; have someone other than the production scheduler author review the reference model and expected traces. Re-estimate after work packages 1–2. Reserve ongoing verification capacity in each feature estimate.

Infrastructure needs: native Linux x86-64, Windows x86-64 and macOS arm64 runners with locked dependencies, artifact storage, and an isolated endurance/performance host. Commercial simulator licenses are optional additional evidence, not a dependency of the initial public test suite. Preserve licenses/notices for imported test corpora. Re-estimate the earlier effort range after the three-platform build/JIT probes and MCU reference scope are established; that range is not a new commitment for the expanded release matrix.

The immediate next implementation step is library L0: create its build/test skeleton, pin tool versions, emit one typed channel/primitive with a checked manifest, and execute independent positive and negative cases through an external simulator. Complete the library families before the main engine. Simulator qualification then starts with a counter, coincident-edge register swap, NBA re-entry, captured delayed assignment, canceled paused-clock edge, initialized C-element, repeated-payload handshake, and replayed seed. These small cases exercise the contracts before large CPU benchmarks make failures difficult to diagnose.
