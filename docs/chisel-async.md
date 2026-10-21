# chisel-async integration

The library is built and maintained in [BiscutLabs/chisel-async](https://github.com/BiscutLabs/chisel-async). Its APIs, component catalog, timing contracts and qualification evidence belong there. This document owns only its Chiselator integration. See the [inspected baseline](integration-status.md) for the exact revision, RC1 release versus RC2 development distinction and platform limits.

The current library includes four-phase stages/FIFOs/fork/join/selection/arbitration, native Click components, a bounded dual-rail family, memory/event interfaces, clocked bridges and capture receipts. It exports structural contracts, semantic hashes and observation interfaces. Library completeness does not automatically imply native Chiselator compatibility.

## Library-first delivery sequence

The original library-first build phase has happened. The active sequence is now **pin → import → preserve → compare → qualify**. The [old implementation-plan path](chisel-async-implementation-plan.md) is retained as a pointer, not a duplicate roadmap.

| Boundary | Required implementation and evidence |
| --- | --- |
| Export/import | Validate the pinned contract version, port/probe ABI, resource hashes and semantic hash; reject missing or ambiguous mandatory metadata |
| CIRCT lowering | Preserve state, delay semantics, clock/reset domains, source identities and protected timing endpoints |
| Primitive bindings | Compare native behavior with independent sequences and upstream external simulation; capability-gate every model/version |
| Observations | Record actual commits before coalescing; export exact timing and visibility limitations through a versioned adapter |
| Protocols | Qualify four-phase first; native Click is needed for the second MCU variant; dual-rail/QDI follows its own explicit gate |
| Distribution | Test pinned clean consumers on each advertised simulator platform; do not infer macOS support from Windows/Linux evidence |

## Clocked boundaries

Use the upstream [clocked integration contract](https://github.com/BiscutLabs/chisel-async/blob/83d646825da854f93d59f6b2055ecde369e62242/docs/clocked-integration.md). `DecoupledToFourPhase` stores a payload on `in.fire`. `FourPhaseToDecoupled` acknowledges after `out.fire`; observing a request is not acceptance. Their synchronizer and reset behavior is part of the component contract.

Capture receipts are different: they do not introduce a second payload register. The source retains ownership while the actual consumer clock captures on `out.fire`. A stopped consumer clock can leave an operation pending indefinitely. The simulator and analyzer must preserve that distinction instead of inventing a FIFO, a transfer or a deadline failure.

Plain Chisel `Decoupled` has no held-valid/held-data guarantee. Count transfers at the qualified sampling edge where `valid && ready`; an earlier `valid` interval does not establish a stable transaction. Stronger offer-to-accept tracking requires a declared held-offer contract and its checks. See the [graph/event contract](graph-event-contract.md).

## Source contracts and limitations

Import upstream `contract-v3` and `trace-v1` through explicit adapters, not field renaming alone. Integer femtoseconds can be preserved exactly, but a trace lacking scheduler phases or transfer lineage cannot support those analyses retroactively. Publish unsupported or partial visibility.

The library's [timing/export](https://github.com/BiscutLabs/chisel-async/blob/83d646825da854f93d59f6b2055ecde369e62242/docs/timing-and-export.md), [components](https://github.com/BiscutLabs/chisel-async/blob/83d646825da854f93d59f6b2055ecde369e62242/docs/components.md) and [testing](https://github.com/BiscutLabs/chisel-async/blob/83d646825da854f93d59f6b2055ecde369e62242/docs/testing.md) documents are authoritative. Digital delay models do not qualify physical matched delays, analog metastability or silicon QDI assumptions. Those remain [physical implementation](chip-build-plan.md) obligations.
