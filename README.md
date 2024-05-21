<!-- Badges for GitHub -->
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202-blue.svg?style=flat-square)](https://opensource.org/license/apache-2-0/)
[![Documentation](https://img.shields.io/github/actions/workflow/status/haiqu-ai/rivet/.github%2Fworkflows%2Fdocumentation.yml?logo=sphinx&style=flat-square
)](https://haiqu-ai.github.io/rivet)

<p align="center">
<picture>
  <img src="https://raw.githubusercontent.com/haiqu-ai/rivet/main/docs/source/_static/logos/rivet.png" width="60%">
</picture>
</p>

# Transpilation

Quantum Transpilation is the transformation of a given abstract quantum circuit with the aim of:
- Matching the topology, native gate set, errors and other properties of a specific quantum device
- Optimizing the circuit for execution

Even at small scales, transpilation can become a **key bottleneck** in many complex quantum computing workflows, such as those in Error Mitigation or Quantum Machine Learning, where modular circuits are iteratively updated and transpiled or many instances of largely similar circuits are run. Rivet allows users to design and implement **fast automated modular transpilation** routines with the transpilation stack of their choice (via **Stack Selection**), providing tools such as caching and re-use and detailed control over transpilation passes. Despite its advanced functionality, Rivet is easy to use and includes features such as performance tracking and debugging.


## Introduction to the Rivet Transpiler

The Rivet Transpiler allows users to design and implement fast automated modular transpilation routines with the transpilation stack of their choice. The goal is to allow users complete control over the process, allowing for greater flexibility and large reductions in transpilation time.

Despite its advanced functionality, Rivet Transpiler is easy to use and includes convenience features, such as performance tracking and debugging.

<p align="center">
<picture>
  <img src="https://raw.githubusercontent.com/haiqu-ai/rivet/main/docs/images/transpilation_time.png" width="60%" />
  <figcaption>
    <i>
    Figure 1: This plot visualizes the difference in transpilation time between Rivet and a standard transpiler, where a massive advantage is seen through Rivet’s implementation. The example is presented for shadow tomography for a state generated by the litmus circuit. Check <a href=https://github.com/haiqu-ai/rivet/blob/main/examples/shadows/shadow_state_tomography.ipynb)">Shadow State Tomography</a>  for more details. 
    </i>
  </figcaption>
</picture>
</p>

<p align="center">
<picture>
  <img src="https://raw.githubusercontent.com/haiqu-ai/rivet/main/docs/images/transpilation_time2.png" width="60%" />
  <figcaption>
    <i>
    Figure 2: This plot visualizes the difference between the same algorithm being transpiled with Rivet (with topology constraint) and standard transpiler which adds ancilla qubits. The standard transpiler’s addition of ancilla qubits subsequently brings substantial increases in compute time. Using Topological Compression, the Rivet transpiler ensures the minimum number of qubits is used, making for fast and efficient computation.
    </i>
  </figcaption>
</picture>
</p>

**Subcircuit Transpilation and Stitching:** Rivet allows circuits to be subdivided, and the parts transpiled separately and maintain the correct relation to the other subparts (qubit indices, mapping between logical and physical qubits, etc.). The pre-transpiled subcircuits can be cached and later consistently stitched together with other circuits (e.g. multiple basis changes) for execution, allowing drastic saving of computational resources.

**Flexible Stack Selection:** Users can transpile their entire circuit, or parts of a circuit, via one or a combination of transpilation passes from different stacks of their preference. This allows one to choose the optimal transpiling strategy for the given use case and circuit architecture. Supported stacks include:
- Qiskit
- BQSKit
- Pytket

**Granular Transpilation Control:** Rivet gives the User a high level of insight into, and control over the transpilation process, including the – typically invisible to the user – use of quantum resources, such as auxiliary qubits used in various transpilation passes, which can be constrained via the Qubit-Constrained Transpilation function. Combined with a debugging interface it allows to optimize the classical and quantum compute involved in the execution and shorten the development loop, especially in research and prototyping.

More details about these core features, as well as other useful tools, can be found in the Tutorials section below.


## Rivet's Functions

The package provides a family of functions for efficient transpilation of quantum circuits.

- Function `transpile` - transpilation function featuring:
    - Different transpilation stacks:
        * [Qiskit:](https://github.com/Qiskit/qiskit#readme) Quantum SDK
        * [BQSKit:](https://github.com/BQSKit/bqskit#readme) Berkeley Quantum Synthesis Toolkit
        * [Pytket:](https://github.com/CQCL/pytket#readme) Python interface for Quantinuum TKET compiler
    - Custom PassManager
    - Dynamical decoupling
    - Transpiler options
- Function `transpile_chain` - consistently transpile and "stitch" a chain of quantum circuits
- Function `transpile_right` - transpile an additional circuit to the right part of the existing circuit
- Function `transpile_left` - transpile an additional circuit to the left part of the existing circuit. Collectively these functions allow for users to transpile and stitch pieces of circuits.
- Function `transpile_and_compress` - transpile and constrain the use of auxiliary qubits in all the transpilation passes of a circuit considering a coupling map of the selected backend

## Installation

To install Rivet Transpiler, please clone the repository:

```bash
git clone https://github.com/haiqu-ai/rivet.git
```

Go to the repository folder and install a local package using pip:

```bash
pip install .
```

To install the transpiler with all supported stacks:

```bash
pip install .[stacks]
```

To install only BQSKit or only Pytket support:

```bash
pip install .[bqskit]
pip install .[pytket]
```

## Documentation

For more details about the Rivet Transpiler, please check the [reference documentation](https://haiqu-ai.github.io/rivet).


## Tutorials

An overview of transpilation, as well as other features Rivet offers like Hashing are outlined in the links below. Shadow State Tomography and Fourier Adders are examples of complex processes that could benefit from Rivet’s Subcircuit Transpilation and Stitching. 

- [Transpilation Overview, Stages, Functions](examples/examples.ipynb)
- [Shadow State Tomography](examples/shadows/shadow_state_tomography.ipynb)
- [Fourier Adder](examples/fourier_adder/fourier_adder.ipynb)
- [Qubit-Constrained Transpilation](examples/qubit_constrained_transpilation/qubit_constrained_transpilation.ipynb)
- [Hashing](examples/hashing/hashing.ipynb)
- [Circuit Stitching](examples/circuit_stitching/circuit_stitching.ipynb)
- [Quantum Circuit Synthesis](examples/circuit_synthesis/circuit_synthesis.ipynb)


## Basic Example

<br>
    <a>
    <img src="docs/images/layout.png">
    </a>
<br>

Transpilation includes placement of *virtual qubits* of a circuit to *physical qubits* of the quantum device or simulator. Additionally, SWAP gates can be included to route qubits around the backend topology.

Here we present a simple quantum circuit with 3 qubits before and after transpilation (using the function `transpile_chain` which transpiles a chain of virtual circuits keeping qubits consistent).

### BEFORE transpilation

```python
from qiskit import QuantumCircuit

from qiskit_ibm_runtime.fake_provider import FakeLimaV2

from rivet_transpiler import transpile_chain

backend = FakeLimaV2()

circuit = QuantumCircuit(3)

circuit.cx(0, 1)
circuit.cx(1, 2)
circuit.cx(0, 2)

circuit.barrier()

circuit.draw()
```

```bash
q_0: ──■─────────■──
     ┌─┴─┐       │
q_1: ┤ X ├──■────┼──
     └───┘┌─┴─┐┌─┴─┐
q_2: ─────┤ X ├┤ X ├
          └───┘└───┘
```

### AFTER transpilation

```python
CHAIN = [circuit] * 3

transpiled_circuit = transpile_chain(
    CHAIN,
    backend,
    seed_transpiler=1234
)

transpiled_circuit.draw(fold=-1)
```

```bash
                              ┌───┐           ░ ┌───┐                          ░      ┌───┐          ┌───┐               ┌───┐ ░
      q_1 -> 0 ──■─────────■──┤ X ├──■────────░─┤ X ├─────────────────■────────░───■──┤ X ├──■───────┤ X ├───────────────┤ X ├─░─
               ┌─┴─┐     ┌─┴─┐└─┬─┘┌─┴─┐      ░ └─┬─┘┌───┐     ┌───┐┌─┴─┐┌───┐ ░ ┌─┴─┐└─┬─┘┌─┴─┐┌───┐└─┬─┘┌───┐     ┌───┐└─┬─┘ ░
      q_2 -> 1 ┤ X ├──■──┤ X ├──■──┤ X ├──■───░───■──┤ X ├──■──┤ X ├┤ X ├┤ X ├─░─┤ X ├──■──┤ X ├┤ X ├──■──┤ X ├──■──┤ X ├──■───░─
               └───┘┌─┴─┐└───┘     └───┘┌─┴─┐ ░      └─┬─┘┌─┴─┐└─┬─┘└───┘└─┬─┘ ░ └───┘     └───┘└─┬─┘     └─┬─┘┌─┴─┐└─┬─┘      ░
      q_0 -> 2 ─────┤ X ├───────────────┤ X ├─░────────■──┤ X ├──■─────────■───░──────────────────■─────────■──┤ X ├──■────────░─
                    └───┘               └───┘ ░           └───┘                ░                               └───┘           ░
ancilla_0 -> 3 ────────────────────────────────────────────────────────────────░───────────────────────────────────────────────░─
                                                                               ░                                               ░
ancilla_1 -> 4 ────────────────────────────────────────────────────────────────░───────────────────────────────────────────────░─
                                                                               ░                                               ░
```

## References

We would like to thank:

* [Qiskit](https://github.com/Qiskit/qiskit) Quantum SDK
* [BQSKit](https://github.com/BQSKit/bqskit) Berkeley Quantum Synthesis Toolkit
* [Pytket](https://github.com/CQCL/pytket) Python inteface for Quantinuum TKET compiler


## Contributors

* Mykhailo Ohorodnikov
* Yuriy Pryyma
* Vlad Bohun
* Vova Sergeyev
* Mariana Krasnytska


## Contacts

Haiqu Inc. [info@haiqu.ai](mailto:info@haiqu.ai)
