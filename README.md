[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202-blue.svg?style=flat-square)](https://opensource.org/license/apache-2-0/)
[![Documentation](https://img.shields.io/github/actions/workflow/status/haiqu-ai/rivet/.github%2Fworkflows%2Fdocumentation.yml?logo=sphinx&style=flat-square
)](https://haiqu-ai.github.io/rivet)

<p align="center">
<picture>
  <img src="https://raw.githubusercontent.com/haiqu-ai/rivet/main/docs/source/_static/logos/rivet.png" width="60%">
</picture>
</p>



# Rivet Transpiler

The package provides a family of functions for efficient transpilation of quantum circuits.

## Transpile Functions

`transpile` - custom transpilation with possibility of using:

- Pre-defined [Transpilation Stacks](#transpilation-stacks)
- Custom [PassManager](https://docs.quantum.ibm.com/api/qiskit/passmanager)
- Dynamical decoupling
- Transpiler options

`transpile_chain` - consistently transpile and "stitch" a [chain](#minimal-example) of quantum circuits.

`transpile_right` - transpile an additional circuit to the [right part](#shadow-state-tomography) of the existing circuit.

`transpile_left` - transpile an additional circuit to the [left part](#fourier-adder) of the existing circuit.

`transpile_and_compress` - transpile and ["topologically compress"](#topological-compression) a circuit considering a coupling map of the selected backend.


## Transpilation Stacks

Transpilation stacks include below frameworks:

* [Qiskit:](https://github.com/Qiskit/qiskit#readme) Quantum SDK
* [BQSKit:](https://github.com/BQSKit/bqskit#readme) Berkeley Quantum Synthesis Toolkit
* [Pytket:](https://github.com/CQCL/pytket#readme) Python inteface for Quantinuum TKET compiler

Following pre-defined transpilation stacks are available:

```python
"qiskit"
"qiskit_qsearch"
"qiskit_qfactor_qsearch"
"qiskit_pytket"
```


## Installation

Clone the repository:

```bash
git clone https://gitlab.com/haiqu-ai/qml-transpiler.git
```

Go to the repository folder and install a local package using pip:

```bash
pip install .
```

To install pre-defined stacks support:

```bash
pip install .[stacks]
```

To install only BQSKit or only Pytket stack support:

```bash
pip install .[bqskit]
pip install .[pytket]
```

## Basic Example

Transpilation includes placement of *virtual qubits* of a circuit to *physical qubits* of quantum device or simulator.
<br>
    <a>
    <img src="docs/images/layout.png">
    </a>
<br>
Additionally, SWAP gates can be included to route qubits around backend topology.

Here we present a simple quantum circuit with 3 qubits.

```python
import qiskit

from qiskit.providers.fake_provider import FakeLimaV2

from qml_transpiler import transpile_chain

backend = FakeLimaV2()

circuit = qiskit.QuantumCircuit(3)

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

We use `transpile_chain` function to transpile a chain of virtual circuits keeping qubits consistent:

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

## Tutorials

### Examples

[examples.ipynb](examples/examples.ipynb)

    - Transpilation Overview, Stages, Functions
    - Litmus Circuit, Backend
    - Qiskit Transpiler, Pass Manager
    - Circuit Stitching, Full Map
    - Transpile Chain, Right, Left, Compress
    - Transpilation Stacks, QSearch, Synthesis
    - Circuit Hash
    - IBM Cost

### Shadow State Tomography

Efficient Tomography circuits transpilation with `transpile_right` function:

[shadow_state_tomography.ipynb](examples/shadows/shadow_state_tomography.ipynb)

<a>
<img src="docs/images/su2.png">
</a>

### Fourier Adder

Efficient QFT transpilation with `transpile_left` function:

[fourier_adder.ipynb](examples/fourier_adder/fourier_adder.ipynb)

<a>
<img src="docs/images/fourier_adder.png">
</a>
<br>
<a>
<img src="docs/images/fourier_adder_states.png" width=150>
<img src="docs/images/fourier_adder_states_noisy.png" width=150>
<img src="docs/images/fourier_adder_states_full.png" width=150>
</a>

### Topological Compression

Select topologically most important qubits of a backend – and then transpiles circuit using limited coupling map – to decrease transpilation and simulation time:

[topological_compression.ipynb](examples/topological_compression/topological_compression.ipynb)

<a>
<img src="docs/images/topological_compression.png" width=250>
</a>

### Hashing

[hashing.ipynb](examples/hashing/hashing.ipynb)


## Documentation

For more details about the Rivet Transpiler, please check the documentation:

* Deployed to [GitHub Pages](https://haiqu-ai.github.io/rivet)
* Deployed to [GitLab Pages](https://mohor.gitlab.io/haiqu/)
* Local [Documents folder](docs/qml_transpiler)


## Testing

Install [pytest](https://docs.pytest.org/) testing support:

```bash
pip install .[testing]
```

Then run [tests script](tests/run_tests.py):

```bash
python tests/run_tests.py
```


## References

We would like to thank:

* [Qiskit](https://github.com/Qiskit/qiskit) Quantum SDK
* [BQSKit](https://github.com/BQSKit/bqskit) Berkeley Quantum Synthesis Toolkit
* [Pytket](https://github.com/CQCL/pytket) Python inteface for Quantinuum TKET compiler


## Contributors

<div align="center">
  <table style="border-collapse: collapse;">
    <tr>
      <td align="center">
        <img src="docs/images/contributors/mykhailo_ohorodnikov.jpg" alt="Mykhailo Ohorodnikov" width="100" height="100" style="border-radius: 50%;"><br>
        Mykhailo Ohorodnikov
      </td>
      <td align="center">
        <img src="docs/images/contributors/yuriy_pryyma.jpg" alt="Yuriy Pryyma" width="100" height="100" style="border-radius: 50%;"><br>
        Yuriy Pryyma
      </td>
      <td align="center">
        <img src="docs/images/contributors/vlad_bohun.jpg" alt="Vlad Bohun" width="100" height="100" style="border-radius: 50%;"><br>
        Vlad Bohun
      </td>
    </tr>
    <tr>
      <td align="center">
        <img src="docs/images/contributors/vova_sergeyev.jpg" alt="Vova Sergeyev" width="100" height="100" style="border-radius: 50%;"><br>
        Vova Sergeyev
      </td>
      <td align="center">
        <img src="docs/images/contributors/mariana_krasnytska.jpg" alt="Mariana Krasnytska" width="100" height="100" style="border-radius: 50%;"><br>
        Mariana Krasnytska
      </td>
      <td align="center">
      </td>
    </tr>
  </table>
</div>


## Contacts

Haiqu Inc. [info@haiqu.ai](mailto:info@haiqu.ai)
