# Chiselator

Chiselator is the planned simulator for an open-source chip development stack. It will compile supported Chisel and SystemVerilog through CIRCT, with first-class clocked, asynchronous and hybrid execution. Rust owns the runtime and application; C++ integrates CIRCT/LLVM behind a versioned C interface. CPU execution comes first; GPU backends and ACT integration are optional, separately qualified paths.

**Current status:** [chisel-async](https://github.com/BiscutLabs/chisel-async) and [RISCay-MCU](https://github.com/BiscutLabs/RISCay-MCU) are built in their own repositories. Chiselator has architecture documents and draft analysis schemas/fixtures, but no implemented simulator, plugin host or analyzer. The [integration baseline](docs/integration-status.md) records inspected revisions and remaining acceptance work.

1. **chisel-async:** reusable protocols, components, primitive/timing contracts and independent tests.
2. **RISCay-MCU:** an RV32E application corpus with four-phase and native Click variants, including clocked service boundaries.
3. **Chiselator:** compile and simulate the established corpus, then provide extensible graph and transaction analysis.
4. **Physical implementation:** a separate ASIC/FPGA workflow and qualification boundary. MCU physical development already exists upstream; simulation requires no physical build, PDK or synthesis tool.

## Read the design

- [Documentation map](docs/README.md) and [software architecture](docs/software-architecture.md).
- [Five semantic specifications](docs/specs/README.md), [MVP features](docs/mvp-feature-list.md) and [scientific test plan](docs/test-plan.md).
- [Plugin API](docs/plugin-api.md): process lifecycle, version negotiation, artifact access and results.
- [Graph/event schemas and transaction tracking](docs/graph-event-contract.md): clocked/async boundaries, fork/join, reset and persistent effects.
- [Algorithm research and diagrams](docs/flow-analysis-algorithms.md): streaming decoding, causal latency, feedback/wait analysis and graph layout.

Native simulator releases are planned for Windows x86-64, Linux x86-64 and macOS arm64. Built-in simulation will not need an installed Rust/C++ compiler. Chisel elaboration still requires its JVM toolchain. These are release requirements, not current compatibility claims.

## Check the draft contracts

See [schema validation](docs/schemas/README.md) for the dependency and commands. These checks validate documentation examples and selected semantic invariants; they do not execute RTL or qualify simulator accuracy.

Project code is licensed under [Apache-2.0](LICENSE). Dependencies retain their own licenses.
