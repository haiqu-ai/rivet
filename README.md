# QML Transpiler

QML Transpiler package provides a family of transpile functions that wraps Qiskit's `transpile` method, allowing you to transpile a quantum circuit with additional options.

## Clone

```bash
https://gitlab.com/mohor/haiqu.git
```

## Installation

You can install this package using pip:

```bash
pip install .
```

## Usage

Basic transpilation:

```python
from qiskit.providers.aer import AerSimulator
from qiskit.providers.fake_provider import FakeBackend5QV2

from qml_transpiler import transpile
from qml_transpiler import get_litmus_circuit

FAKE_BACKEND = FakeBackend5QV2()

backend = AerSimulator.from_backend(FAKE_BACKEND)

litmus_circuit = get_litmus_circuit(3, "Litmus")

transpiled_litmus_circuit = transpile(
    litmus_circuit, 
    backend,
    # optimization_level=3,
    # initial_layout=[1, 2, 3],
    seed_transpiler=1234,
)

transpiled_litmus_circuit.draw()
```
```
 ancilla_0 -> 0 ────────────────────────────────────────────────────
                ┌─────────────────┐          ┌───┐          ┌───┐ ░ 
Litmus_0_2 -> 1 ┤ U(0,0,Litmus_2) ├───────■──┤ X ├──■───────┤ X ├─░─
                ├─────────────────┤     ┌─┴─┐└─┬─┘┌─┴─┐┌───┐└─┬─┘ ░ 
Litmus_0_0 -> 2 ┤ U(0,0,Litmus_0) ├──■──┤ X ├──■──┤ X ├┤ X ├──■───░─
                ├─────────────────┤┌─┴─┐└───┘     └───┘└─┬─┘      ░ 
Litmus_0_1 -> 3 ┤ U(0,0,Litmus_1) ├┤ X ├─────────────────■────────░─
                └─────────────────┘└───┘                          ░ 
 ancilla_1 -> 4 ────────────────────────────────────────────────────
```

Final allocation of virtual qubits in transpiler circuit:

```python
from qml_transpiler import get_full_map

get_full_map(transpiled_litmus_circuit)
```
```
[1, 3, 2, 0, 4]
```

More usage examples at:

[/examples/examples.ipynb](/examples/examples.ipynb)


## Documentation

Detailed package structure and function descriptions can be found at:

[/docs/qml_transpiler/index.html](/docs/qml_transpiler/index.html)

## Transpilation Stacks

Pre-defined transpilation stacks are available:

```bash
pip install .[stacks]
```

Or install only necessary stacks:

* BQSKit stack:

    ```bash
    pip install .[bqskit]
    ```

* Pytket stack:

    ```bash
    pip install .[pytket]
    ```

## Testing

Install:

```bash
pip install .[testing]
```

Then run `tests/run_tests.py`