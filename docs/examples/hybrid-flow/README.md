# Hybrid capture-receipt fixture

Hand-authored synthetic example, October 20, 2026. No simulator or MCU produced these values. The model and nonexistent plugin-package hashes are explicit all-zero placeholders; input file hashes are actual content hashes. The plugin manifest describes nonexistent example executables and must not be installed as a real plugin.

The graph connects an async producer through a **zero-payload-storage receipt** to a clocked consumer. `c:async` follows the conservative four-phase held-return contract. `c:clocked` uses sampled ready/valid. The window is `[0,20 ns)`; all initial channels are known idle, reset epoch is zero and no records are lost.

| Evidence record | Time | Meaning |
| --- | --- | --- |
| e1 | 2 ns | Async request offers A; source holds payload |
| e2/e3/e4 | 4/8/12 ns | Actual consumer clock edges 1/2/3 |
| e5 | 12 ns | Clocked fire creates atomic transaction B |
| e6 | 12 ns | Receipt explicitly links A to B, with e1/e5 causes |
| e7 | 12 ns, delta 1 | Async acknowledgement accepts A |
| e8 | 12 ns, delta 2 | Consumer capture effect, independently identified |
| e9 | 16 ns | Consumer clock edge 4 |
| e10 | 16 ns, delta 1 | Return to idle completes A |

For the illustrative raw waveform, request returns low at 13 ns. That is explanatory fixture information, not an additional normalized event. The normalized record set cannot itself prove raw four-phase transitions or data hold. A future decoder fixture must include and validate those signal observations separately.

Expected async acceptance latency is **10 ns**, recovery **4 ns**, completion latency **14 ns**, and acceptance rate **1 / 20,000,000 fs = 50 million transactions/second** for this one-token synthetic window. This rate is circuit traffic, not simulator throughput. The clocked sampled token has no known offer time before fire; its offer latency is unavailable. Both channels accept one token, but they describe one linked operation, not two independent source operations.

The [expected result](expected-result.json) stores integer rational values, including the unavailable metric reason. The [timeline](../../images/hybrid-timeline.svg) and [interval chart](../../images/hybrid-metrics.svg) are reproducible illustrations. [Validation instructions](../../schemas/README.md) distinguish selected contract checks from future production decoder qualification.

Further release fixtures must independently cover reverse clocked-to-async storage, FIFO ordering, native Click parity, fork/join, arbitration, reset and POR-owned effects, gated clocks, incomplete windows and unknown phase imports. This single example does not qualify those cases.

The bundle now uses draft artifact version `0.2.0`. Its capture explicitly sets `probes: null`, so occupancy, per-edge classes and waits remain unavailable. Transaction timing and expected arithmetic are unchanged; hashes were deliberately refreshed for the migrated bytes. The [pipeline fixtures](../pipeline-bottleneck/README.md) add normalized probe examples without qualifying upstream capture.
