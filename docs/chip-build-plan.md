# Physical implementation boundary — step 4

ASIC and FPGA implementation remain a separate product responsibility from simulation. The original four-step plan placed this after Chiselator; physical exploration has since started in the MCU repository. This document records the interface and qualification backlog, not a duplicate physical implementation plan or a ban on parallel work.

## Product order and physical gates

chisel-async supplies components, RISCay-MCU supplies the application, and Chiselator supplies native simulation. All three work without physical synthesis, a PDK or fabrication. Physical tools consume qualified exports plus target-specific implementations and constraints. See [current status](integration-status.md).

The MCU documents GF180 development and a completed BD routing result at an older revision. Routing completion does not establish electrical/timing/SI closure or fabrication readiness, and older area/results do not qualify current RTL. Exact dimensions, route revisions and open issues belong in its [routability record](https://github.com/BiscutLabs/RISCay-MCU/blob/870124a93c5e9ed86f2ca52a45c4f24bdb8851d6/docs/gf180-routability.md) and [area ledger](https://github.com/BiscutLabs/RISCay-MCU/blob/870124a93c5e9ed86f2ca52a45c4f24bdb8851d6/docs/area-ledger.md).

## Synthesis decision

Do not write a new synthesizer as a prerequisite for the simulator. ASIC implementation can integrate existing synthesis/place-and-route tools with explicit preservation, primitive mapping and timing contracts. The MCU owns its selected flow and versions. Yosys is not a Chiselator runtime/build dependency; this does not prohibit its use in a separately qualified physical flow.

**Vivado is the chosen FPGA tool.** Its adapter must distinguish functional FPGA emulation from a qualified physical asynchronous implementation. Preserve or deliberately replace async primitives under a documented target contract; verify any replacement against channel/effect tests. Fabric routing, feedback, latch behavior and matched delays need target-specific evidence. An FPGA demonstration is not an ASIC timing proof.

## Tool adapters and artifacts

Importers may add immutable target overlays to the public logical graph: cell/net mappings, resource use, timing endpoints and report provenance. Keep physical pins and simulator channels distinct; require explicit many-to-many mappings. Each overlay identifies tool version, target, design hash and constraint/report hashes. Missing mappings are visible. Read-only importers use the [plugin API](plugin-api.md); launching synthesis or modifying a design is a separate job capability outside the initial analysis API.

Retain behavioral, simulation and target implementation views under versioned primitive contracts. Export timing endpoints, clock/reset ownership and preservation requirements. Physical implementation cannot retroactively change the functional simulation contract without versioning and new comparisons.

## Tests and evidence

| Suite | Required physical evidence |
| --- | --- |
| PHY-01 Views and preservation | Primitive mapping, state/feedback/delay preservation, endpoint provenance and functional comparison after mapping |
| PHY-02 Timing | Characterized cells, bundled-data setup/hold/return/reset constraints, corners and independent timing review; explicit analog limitations |
| PHY-03 Memory and boot | Actual memory macros/FPGA resources, initialization, boot images, clock/reset and read/write behavior |
| PHY-04 Test and layout | Debug/manufacturing test, power/reset, constraints, DRC/LVS or target implementation checks |
| PHY-05 Handoff | Reproducible pinned builds, licenses, complete artifacts, hashes and reviewed tool/constraint exceptions |
| PHY-06 Board and silicon | Measured interfaces, power, reset, timing and application behavior over the claimed operating range |

P1 means a target feasibility probe; P2 means implementation closure; P3 means board/silicon qualification. These physical gate names are separate from MVP feature priorities. Owners and exact exit criteria live with the target project. Passing Chiselator's behavioral tests does not pass these gates, and these gates do not block a functional simulator release.
