import pytest

import qiskit

from qiskit.providers.fake_provider import FakeBackend5QV2

from qml_transpiler import transpile
from qml_transpiler import transpile_left
from qml_transpiler import transpile_right
from qml_transpiler import transpile_chain
from qml_transpiler import transpile_and_compress

from qml_transpiler import get_full_map
from qml_transpiler import get_ibm_cost

from qml_transpiler import get_litmus_circuit
from qml_transpiler import get_cnot_circuit
from qml_transpiler import get_sinusoids


# Test Transpile Functions

def test_transpile(litmus_circuit, backend):

    transpiled_litmus_circuit = transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    return transpiled_litmus_circuit


def test_transpile_chain(litmus_circuit, backend):

    CHAIN = [litmus_circuit] * 2

    transpiled_chain_circuit = transpile_chain(
        circuits=CHAIN,
        backend=backend,
        seed_transpiler=1234)

    return transpiled_chain_circuit


def test_transpile_right(litmus_circuit, backend):

    transpiled_litmus_circuit = qiskit.transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    transpiled_right_circuit = transpile_right(
        central_circuit=transpiled_litmus_circuit,
        right_circuit=litmus_circuit,
        backend=backend,
        seed_transpiler=1234)

    return transpiled_right_circuit


def test_transpile_left(litmus_circuit, backend):

    transpiled_litmus_circuit = qiskit.transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    transpiled_left_circuit = transpile_left(
        central_circuit=transpiled_litmus_circuit,
        left_circuit=litmus_circuit,
        backend=backend,
        seed_transpiler=1234)

    return transpiled_left_circuit


def test_transpile_and_compress(litmus_circuit, backend):

    compressed_litmus_circuit = transpile_and_compress(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    return compressed_litmus_circuit


# Test Full Map

def test_full_map(litmus_circuit, backend):

    transpiled_litmus_circuit = transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    get_full_map(transpiled_litmus_circuit, verbose=True)


def test_full_map_value():

    litmus_circuit = get_litmus_circuit(qubits_count=3)

    backend = FakeBackend5QV2()

    transpiled_litmus_circuit = transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    full_map = get_full_map(transpiled_litmus_circuit)

    assert full_map == [1, 3, 2, 0, 4]


# Test Service Functions

def test_get_ibm_cost_value():

    litmus_circuit = get_litmus_circuit(qubits_count=3)

    ibm_cost = get_ibm_cost(litmus_circuit)

    rounded_ibm_cost = round(ibm_cost, 4)

    assert rounded_ibm_cost == 0.9499


def test_get_ibm_cost_toffoli():

    toffoli_circuit = qiskit.QuantumCircuit(3)

    toffoli_circuit.toffoli(0, 1, 2)

    with pytest.raises(ValueError):

        ibm_cost = get_ibm_cost(toffoli_circuit)

        return ibm_cost


def test_cnot_circuit():

    get_cnot_circuit(qubits_count=3)


def test_get_sinusoids():

    get_sinusoids(qubits_count=3, frequencies_count=1)

    get_sinusoids(qubits_count=3, frequencies=[1])

    get_sinusoids(qubits_count=3, frequencies_count=2, amplitudes=[1, 2])

    get_sinusoids(qubits_count=3, frequencies=[1, 2], amplitudes=[10, 20])
