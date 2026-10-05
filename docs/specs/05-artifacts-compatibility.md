# 05 — Artifacts and compatibility

Draft, October 5, 2026. Status and scope: [specification index](README.md). Names and versions below are proposed contracts to implement, not existing schemas.

## Identity and serialization

Distinguish semantic model identity, target-specific build key and run identity. Hash canonical content using SHA-256. The semantic identity covers normalized circuit behavior, primitive/channel versions and relevant annotations; its algorithm/version is itself recorded. It is stable across backend layouts within the qualified compiler pipeline, not a promise that different compilers prove arbitrary circuits equivalent.

Build keys include transitive source/elaboration inputs, frontend/CIRCT/LLVM revisions, pass pipeline, flags, ABI/schema versions, target/CPU features, primitive assets, optimization profile and all compile-time timing data. Backend variants have separate keys. Run identity additionally covers dynamic stimuli, memory images, resolved configuration, seed/choice policy, observation scope, dynamic timing/corner data, selected backend and limits. A separate execution ID distinguishes repeat attempts with identical inputs.

For [chisel-async](../chisel-async.md), record library artifact/version, primitive semantic versions, selected simulation/physical views and design-contract manifest hash. Library API compatibility, primitive semantics and metadata schema are separate version domains. A compatible Scala artifact does not authorize reuse of an incompatible runtime binding or physical view.

Use versioned UTF-8 JSON for inspectable MVP plans/manifests and JSONL for streamed records. Canonical hashed JSON sorts object keys and excludes host timestamps, display paths and performance metrics from semantic identity. Preserve arrays whose order is semantic. Encode wide integers and times as decimal strings; encode circuit values as explicitly sized hexadecimal bit strings. Never rely on JSON floating-point precision for circuit state/time. Binary encoding is deferred until measurement justifies it.

## Required artifact bundle

| Artifact | Required content |
| --- | --- |
| `manifest.json` | Schema/version, identities, resolved inputs/config, toolchain/target, capabilities, limits, seeds/choice policy, backend and observation settings |
| `summary.json` | Mode, terminal outcome/reason, actual frontier/settled status, counts, measured metrics and artifact references |
| `results.xml` | Test/seed cases with failure/error distinction; incomplete cases remain visible and never become passing cases |
| `diagnostics.jsonl` | Stable code, severity, source/instance, time/phase, transaction/causal IDs and bounded context |
| `channels.json` / `.csv` | Offered/accepted/completed/aborted/pending counts, interval/units, latency/backpressure and protocol bins |
| `timing.json` | Constraints, source/model endpoints, declared delays and units, coverage, checked/unchecked conditions and violations; step 4 library/corner/SDF/STA fields are explicitly not applicable in functional mode |
| Requested waveform | FST/VCD with signal selection and a separate visibility manifest |
| Optional event/profile records | Ordered causal events or activation/compile counters with instrumentation settings |
| Qualification `evidence.json` | Experiment/catalog revision, claims and limits, expected/executed case inventory, oracle lineage/review, control results, required activity, raw-result references and analysis revision |

Reports with no applicable channel/timing data state “not applicable”; unsupported and unmeasured metrics use null plus a reason, never fabricated zeros. Async throughput is transactions per simulated/host time, with denominators stated. Per-domain clock counts are optional; there is no global MCU cycle counter. Switch counts are not energy estimates.

Qualification runs follow the [scientific method in the test plan](../test-plan.md#scientific-method-and-limits-of-claims). Keep the simulated job outcome separate from the harness verdict: an expected bad-design failure can pass a negative test without turning the job into PASS. Claim status is separately supported within stated scope, refuted, or not established, with independent fields for digital semantics, physical validity and performance. Missing controls, incomplete observations and unexercised required checks cannot support a passing qualification claim. Ordinary user runs need not generate the full qualification bundle.

Use stable semantic IDs in observations. Model comparisons include exact values, transaction order, required timing and termination. Internal engine tests may compare delta/phase traces; external tools compare mutually defined observation points without assuming identical internal delta numbering. A final-state hash is insufficient for transient correctness.

## Cache and publication

Compile into a temporary directory. Validate every artifact/hash, then publish atomically under its build key using a platform-qualified same-filesystem operation and concurrent-writer coordination. A loader only accepts a complete manifest. Interrupted writes, wrong ABI/target, corrupt content and missing assets are cache misses or explicit errors, never executable cache hits.

Run directories are unique and retain incremental progress plus a final completion record. Publication order must distinguish a partial bundle from a completed one. The supervisor may preserve a terminal error even if the worker cannot finish reports. Referenced external inputs must be retained or content-addressed with their availability recorded; a hash alone cannot recreate a deleted stimulus file.

Treat native object caches as executable code from a trusted local build/distribution. Do not silently execute objects from arbitrary report bundles. Dependency and release checksums establish identity, not sandboxing.

## Replay and random choices

Exact replay requires matching executable/model, dynamic inputs, options and toolchain identities. Refuse changed dependencies as an exact replay and list mismatches. A deliberate rerun under another version/platform/backend creates a new linked run and compares semantic observations; it is not the same executable replay. Checkpoint/restore is deferred and must not be conflated with rerunning stimuli.

Random streams are keyed by algorithm version, user seed, stable session/case identity, semantic object ID and decision kind. Advance counters only at defined model decisions. Worker count, tracing, optimization, GPU lane/batch width and unrelated object activity must not change choices. Record arbiter choices and validate their legality during replay. Store external asynchronous inputs at their logical injection boundaries.

Event/simulated-time limits can reproduce exact stops. Wall-time deadlines and host crashes reproduce a failure class and available evidence, not necessarily the same final simulated event on another machine. Retain the actual stopping frontier and partial-input position.

## Compatibility policy

Public API/report schemas use explicit major/minor versions and capability queries. Breaking changes increment major; additive optional fields increment minor and must have documented defaults. Consumers may ignore unknown optional report fields but must reject unknown required capabilities. Unknown outcome codes are errors, not success. Publish compatibility fixtures for every supported version.

Internal compiler service and generated-kernel ABIs require an exact version match. Model/cache formats may be invalidated between releases; document this and rebuild from retained source. Do not promise native object portability between targets. Public handles are opaque and never serialized. Cross-engine/device checkpoint compatibility remains outside MVP.

Support claims require an evidence matrix connecting language feature, CIRCT operation, primitive, backend, observation mode and platform to passing tests. “Frontend parsed it” and “CPU fallback passed” do not establish GPU or end-to-end feature support.

## Release evidence

In steps 1–3, functional qualification can pass while physical validity is explicitly `not established`. Missing step 4 PDK, synthesis, mapped timing or manufacturing evidence is not a functional release failure. Never promote a functional PASS into a physical validity claim.

For each candidate, retain package hashes, dependency locks/notices, schema/catalog revisions, oracle versions, test outcomes including skipped lanes, minimized failures, replay bundles, sanitizer scope, profiling checks and resource/packaging results. Native Windows/Linux/macOS semantic and install lanes are required. Optional integrations publish separate qualification results.

Acceptance: REP-01–05, INT-03/04, DUR-03/04 and PKG-01. Test input/cache corruption, stale ABI, interrupted publication, concurrent writers, changed replay dependencies, missing metrics, partial sweep accounting and report round trips. Preserve a minimal permanent regression for each fixed correctness bug. Attempt reproducible unsigned builds and report the result; package checksums alone do not establish bit-for-bit reproducibility.
