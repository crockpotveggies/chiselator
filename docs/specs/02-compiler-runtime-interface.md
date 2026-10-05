# 02 — Compiler/runtime interface

Draft, October 5, 2026. Status and scope: [specification index](README.md).

## Inputs and ownership

Chisel elaborates through its pinned JVM toolchain and firtool. SystemVerilog enters through pinned circt-verilog/slang. Both paths use CIRCT normalization and a verified operation subset; accept only operations whose import, lowering, execution and negative tests pass. Clocked/pure logic may use HW/Comb/Seq; processes and timed effects require preserved LLHD semantics or an equivalent verified lowering. Arc reuse is conditional on the scheduling experiment, not assumed because import succeeds.

[chisel-async](../chisel-async.md) instances carry versioned primitive/channel identities, annotations and bindings through extmodules and a checked contract manifest. Its independently tested library corpus precedes native integration. Unsupported black boxes fail with source/instance diagnostics. The supported-operation catalog records operation version, legal types, effects, required tests and backend eligibility. It rejects unsupported constructs before code generation. Validate manifest-to-IR/RTL endpoint mappings so an accepted input cannot silently lose its async or timing contract.

C++ owns CIRCT/LLVM objects, passes, CPU code generation and initial ORC loading. Rust owns validated plan descriptors, sessions, scheduling, built-in models, jobs and reports. Neither frontend nor the runtime invokes Yosys. CIRCT remains the circuit IR; the execution plan below describes scheduling, interfaces and storage.

## Immutable plan

| Record | Required fields/invariants |
| --- | --- |
| Model | Semantic identity, schema/ABI versions, required capabilities, time/value mode |
| Signal | Stable ID, width/signedness, driver policy, visibility and source reference |
| State and memory | IDs, initialization, ports, latency/collision policy, owning region |
| Clock/reset | Source signal, edge/sensitivity, priority, managed-clock policy if applicable |
| Region | Kind, inputs/outputs, effects, dependency edges, kernel entry ID, activity policy |
| Process/subscription | Continuation storage, wake conditions, generation-token ownership |
| Driver | Destination, delay/value policy, allowed effects and cancellation owner |
| Primitive/binding | Model/version, parameters, ports, state layout and contract reference |
| Channel/constraint | Semantic endpoints, protocol/reset rules, timing provenance |
| Backend artifact/layout | Target, kernel ABI, code hash, checked offsets/sizes/alignment |
| Debug map | Stable semantic IDs to source, hierarchy and optimized observations |

Serialize IDs and offsets, never native pointers. Validate counts, widths, references, arithmetic bounds, storage overlap, entry-point kinds, subscriptions and capability requirements before loading executable code or calling a kernel. A model package containing executable objects is trusted local code; schema validation alone does not sandbox it.

Logical identity is independent of partition and memory layout. CPU and future GPU variants may use different layouts and code, but preserve signal identities and semantics. Debug/provenance records must survive transformations; any removed observation is explicit and makes that variant ineligible when the observation is required.

## Three versioned interfaces

| Interface | Operations | Ownership |
| --- | --- | --- |
| Compiler service | Compile, retrieve diagnostics/plan/artifacts, prepare code, release | Opaque C++ handles; compiler frees its own buffers |
| Generated kernel/runtime | Evaluate region, stage declared effects, suspend/wake, emit diagnostics | Borrowed checked context; runtime owns session state |
| Public embedding | Capabilities, model/session lifecycle, drive/read, advance, reports | Opaque Rust handles with C ABI; typed Rust/C++ wrappers |

Use fixed-width integer fields, explicit lengths and sized/versioned C-compatible structures. Buffers specify byte order, alignment, owner and lifetime. No STL containers, Rust collections/enums, exceptions, MLIR objects or generated-code addresses become public data structures. Large bit vectors use explicit byte lengths and mask unused high bits.

Compiler operations are coarse; pure arithmetic stays within compiled kernels rather than calling across the ABI per operator. Each kernel kind has an effect contract:

- Pure evaluation reads declared inputs and produces declared outputs/change information.
- Clock sampling reads its eligible state snapshot and stages owned state updates.
- Process resume updates its continuation and uses declared scheduler/effect helpers.
- Primitive evaluation follows its registered state/driver contract.

Kernel return reports completion or a structured error plus bounded effect output. Runtime helpers validate effect permissions. The compiler and loader agree on exact internal ABI versions; mismatch rejects the artifact. MVP built-in model registration is static and versioned; arbitrary dynamically loaded primitive plugins are deferred.

Code/model handles outlive all sessions and pending work. Session release waits for backend completion before freeing borrowed storage. No kernel retains a borrow beyond its documented execution lease. `unsafe` stays in audited boundary modules with tested lifetime, aliasing, bounds and thread-affinity invariants.

No panic or C++ exception may cross the C ABI. Recoverable failures become status codes and owned diagnostic records. An intercepted internal panic fails the session; it is not safely resumable. Abort/crash containment requires the application worker process. Test actual code loading and callbacks, not only mock handles.

## Backend boundary

The internal executor supports capability query, prepare, submit, collect, request-cancel and release. A submission names sessions/regions, an authorized time/phase frontier, input/effect bindings, work budget and observation requirements. Completion reports actual frontier, whether state is settled, effects/observations, and stop reason. CPU may complete inline; a future GPU executor may retain device state and return a completion token.

CPU is required and default. GPU is optional and initially targets independent run batches. Explicit unsupported GPU requests fail; an `auto` policy may choose CPU and record why. Never silently migrate a failing live device run. Per-session state, random streams and results are independent of lane assignment and batch size.

Any backend must yield for earlier events, callbacks, reset or ACT interaction. It cannot round time, omit required pulses or overflow observation buffers silently. ACT selects an external model binding, independently of CPU/GPU placement. Native models must run with both GPU and ACT absent.

## Optimization and build gates

Use dense graph storage, stable IDs and incremental updates where practical. Begin with serial conservative regions. GSIM-inspired activity tracking, hierarchical bitmaps, hot/cold policies, code sharing and register-cut parallelism are separate transformations with off switches. Profiles include useful/wasted evaluations and held-out validation; an always-run region still performs required downstream activation. Replicate pure logic only.

Build with pinned Cargo and CMake/Ninja toolchains, orchestrated by a developer entry point. Runtime-only tests must run without CIRCT. The release bundles the compiler/runtime; simulation does not compile generated Rust or invoke a host C++ compiler. Qualify mixed linking, ORC allocation/permissions, library loading and error containment on Windows x86-64, Linux x86-64 and macOS arm64.

Acceptance: SEM-05/06, OPT-01/02, INT-01 and DUR-01/03. Include corrupt-plan rejection, C/Rust layout checks, active-session unload rejection, exactly-once release, generated-code memory instrumentation, and a real Chisel/SV kernel trace on each native platform. Arc's 10-working-day gate must produce an ordering matrix and an explicit reuse/fallback decision.
