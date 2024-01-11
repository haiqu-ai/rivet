import pytest

import qiskit

from qiskit.providers.fake_provider import FakeBackend5QV2

from qml_transpiler import transpile
from qml_transpiler import transpile_left
from qml_transpiler import transpile_right
from qml_transpiler import transpile_chain
from qml_transpiler import transpile_and_compress

from qml_transpiler import get_full_map
from qml_transpiler import get_litmus_circuit


# Test Transpile Functions

def test_transpile(litmus_circuit, backend):

    transpiled_litmus_circuit = transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    return transpiled_litmus_circuit


def test_transpile_and_return_options(litmus_circuit, backend):

    transpiled_litmus_circuit, transpile_options = transpile(
        litmus_circuit,
        backend,
        return_options=True,
        seed_transpiler=1234)

    return transpiled_litmus_circuit, transpile_options


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


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_transpile_and_compress(litmus_circuit, backend):

    compressed_litmus_circuit = transpile_and_compress(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    return compressed_litmus_circuit


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_transpile_and_compress_coupling_map(litmus_circuit, backend):

    # Coupling Map

    if backend is None:
        coupling_map = None
    else:
        coupling_map = backend.configuration().coupling_map

    # Coupling List

    if coupling_map is None:
        coupling_list = None
    else:
        coupling_list = [list(pair) for pair in coupling_map]

    # Transpile and Compress

    compressed_litmus_circuit = transpile_and_compress(
        litmus_circuit,
        backend,
        coupling_map=coupling_list,
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

    fixed_litmus_circuit = get_litmus_circuit(qubits_count=3)

    backend = FakeBackend5QV2()

    transpiled_litmus_circuit = transpile(
        fixed_litmus_circuit,
        backend,
        seed_transpiler=1234)

    full_map = get_full_map(transpiled_litmus_circuit)

    assert full_map == [1, 3, 2, 0, 4]
