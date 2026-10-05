# 04 — Application lifecycle

Draft, October 5, 2026. Status and scope: [specification index](README.md).

## Session state machine

| State | Allowed operations / transition |
| --- | --- |
| Created | Configure initialization and callbacks; initialize into Ready or Failed |
| Ready | Settled, readable state; drive into Pending, advance into Running, or finish |
| Pending | Inputs staged but not settled; accept further input drives, or settle/advance into Running; settled reads are unavailable |
| Running | Coordinator owns execution; only the documented cancellation token may be signaled concurrently |
| Suspended | Interior work-budget stop; report phase/unsettled state, resume or finish; no settled reads or new drives |
| Finished | No further circuit execution; inspect retained results and release |
| Failed | No resume; inspect diagnostics and release |

Successful settling/advancement returns Ready. A stop reports actual time, phase, reason and read eligibility. An initialization error fails the session. `finish` is idempotent, terminates pending execution and finalizes monitors once; it does not convert pending obligations or previous failure into success. Releasing any handle invalidates it and must free its owned resources exactly once. Cancellation during a job ends that job; a budget pause in the embedding API may remain resumable.

One caller owns a session at a time. Callbacks run on the coordinator and may use only phase-approved operations. No recursive advance or arbitrary concurrent API calls. Different sessions may run concurrently and share immutable model code. A model cannot unload while sessions or backend submissions reference it.

## Jobs and outcomes

CLI, regression runner and MCP use one job service: `Queued → Resolving → Compiling → Running → Finalizing → Terminal`. Check/build jobs skip execution. Reports record both job mode and phase so a successful build cannot masquerade as a passing simulation.

Terminal outcome is one of PASS, FAIL, ERROR, TIMEOUT or CANCELED, with a stable reason code. Unsupported source/capability and invalid configuration are ERROR reasons. A simulation passes only when its test's explicit success condition is met and mandatory monitors pass. Quiescence, reaching a budget, `$finish` without the configured success condition, missing cases and an empty filtered test set do not imply PASS. Standalone runs may define orderly `$finish` as their success condition; test jobs must declare theirs.

Record the first terminal cause, retain later cleanup/report errors separately, and never overwrite a failure with successful cleanup. Sweeps retain each test/seed result, including not-started cases. Default aggregate precedence is ERROR, FAIL, TIMEOUT, CANCELED, then PASS; publish the counts so aggregate status cannot hide partial work.

Proposed CLI exit codes are 0 success, 1 test failure, 2 configuration/unsupported input, 3 internal/infrastructure error, 4 timeout and 5 cancellation. Machine-readable reason codes provide detail. The same outcome mapping applies to CLI and MCP; an ordinary failed test is a successful MCP request returning a failed job result.

## Supervision and limits

Use the same executable's worker mode for isolated compile/run jobs. Launch with native process APIs and argument arrays; do not depend on a shell, POSIX signals, `fork`, or path rewriting. The supervisor owns process groups/job objects, captures output, enforces limits and reaps children. In-process embedding retains its performance option but cannot promise containment of a fatal native crash.

Limits include wall time, simulated time, event/delta work, memory and output size. Distinguish a normal requested `run_until` boundary from a test budget that expires before success. Cancellation requests cooperative stop first, then terminates the owned worker after a documented grace period. Finalization records actual completed work and partial artifacts. Device cancellation requires completion acknowledgement before referenced buffers can be freed.

Required observation buffers apply bounded backpressure or fail; they never silently drop events. Optional diagnostic history is an explicitly bounded ring with truncation metadata. Disk-full or report-write failure remains visible in supervisor status/stderr even when no complete report can be written. Host I/O scheduling does not determine circuit order.

## CLI, APIs and adapters

The executable owns project resolution, `check/build/run/test`, reports, replay, capability/doctor queries and local MCP. Resolve explicit CLI options over project config over documented defaults. Record the full resolved configuration. Ambient environment settings are admitted only through named, recorded inputs.

The public C API and Rust/C++ wrappers use the same session engine. SV testbench processes use its scheduler. Pinned cocotb and Chisel svsim adapters must map their timing and lifecycle semantics explicitly; unsupported triggers fail rather than silently becoming approximate callbacks. DPI-C breadth and broader Verilator compatibility remain later scope.

Package/version reporting includes the [chisel-async](../chisel-async.md) library and primitive/manifest compatibility range. Its elaboration and external-simulator tests are independently runnable before Chiselator exists. `doctor` and capability queries report missing or incompatible bindings; a working library build alone does not qualify a native simulator adapter.

MCP is a thin local stdio facade: inspect project, start/poll/cancel job, read reports and list signals. Validate typed inputs, paginate output and return artifact references for large waves. Protocol messages alone use stdout; logs use stderr. Disconnect cancels jobs owned by that server instance by default; detached work is deferred. Neither CLI nor MCP invents another success rule or accepts an arbitrary shell command as a simulation option.

## Portable release boundary

| Native target | MVP delivery | Required evidence |
| --- | --- | --- |
| Windows x86-64 | Relocatable ZIP | Real Windows JIT, path/process, cleanup, install and semantic tests |
| Linux x86-64 | Relocatable tar archive | Declared libc/system baseline, JIT and clean-host tests |
| macOS arm64 | Relocatable archive | Native arm64 JIT permissions, packaging and clean-host tests |

Core execution semantics and source support must agree across all three. Platform modules isolate dynamic library loading, executable memory, process supervision, atomic file publication and OS resource accounting. Use portable logical paths in manifests and explicit host paths at I/O boundaries. Test spaces, Unicode, long paths, case sensitivity and relocation.

The CPU package bundles required compiler/runtime assets and needs no host Rust/C++ compiler, GPU driver, PDK or Yosys for built-in SV/compiled-RTL simulation. Chisel elaboration needs its JVM build environment; cocotb needs Python; compiling custom foreign code needs the corresponding compiler. Optional ACT/GPU support has its own advertised platform matrix. Missing optional dependencies must not prevent native startup.

WSL, OCI images, MSI/winget, Homebrew and deb/rpm recipes are conveniences or later packaging expansion, not substitutes for the three native archive gates. Publish checksums, dependency notices, system requirements, release notes and signing status. Do not claim registry publication or signing without evidence.

Acceptance: INT-01–05, DUR-01–04 and PKG-01. Test lifecycle misuse, callback restrictions, timeout/cancel/crash distinctions, missing optional dependencies, child cleanup, disk full, MCP disconnect and CLI/MCP parity. Run native packaging and semantic smoke tests on each target, with a clean-host release lane before shipping.
