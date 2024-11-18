import pytest

import qiskit

from qiskit_ibm_runtime.fake_provider import FakeLimaV2

from rivet_transpiler import transpile
from rivet_transpiler import transpile_left
from rivet_transpiler import transpile_right
from rivet_transpiler import transpile_chain
from rivet_transpiler import transpile_and_compress

from rivet_transpiler import get_full_map
from rivet_transpiler import get_litmus_circuit
from rivet_transpiler import get_used_qubit_indices


# Test Transpile Functions

def test_transpile(litmus_circuit, backend):

    transpiled_litmus_circuit = transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    assert transpiled_litmus_circuit


def test_transpile_and_return_options(litmus_circuit, backend):

    transpiled_litmus_circuit, transpile_options = transpile(
        litmus_circuit,
        backend,
        return_options=True,
        seed_transpiler=1234)

    assert transpiled_litmus_circuit, transpile_options


def test_transpile_chain(litmus_circuit, backend):

    CHAIN = [litmus_circuit] * 3

    transpiled_chain_circuit = transpile_chain(
        circuits=CHAIN,
        backend=backend,
        seed_transpiler=1234)

    assert transpiled_chain_circuit


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

    assert transpiled_right_circuit


def test_transpile_right_target(litmus_circuit, backend):

    target = backend.target if backend else None

    transpiled_litmus_circuit = qiskit.transpile(
        litmus_circuit,
        target=target,
        seed_transpiler=1234)

    transpiled_right_circuit = transpile_right(
        central_circuit=transpiled_litmus_circuit,
        right_circuit=litmus_circuit,
        target=target,
        seed_transpiler=1234)

    litmus_qubits_count = len(
        get_used_qubit_indices(
            litmus_circuit))

    transpiled_right_qubits_count = len(
        get_used_qubit_indices(
            transpiled_right_circuit))

    assert litmus_qubits_count == transpiled_right_qubits_count


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

    assert transpiled_left_circuit


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_transpile_and_compress(litmus_circuit, backend):

    compressed_litmus_circuit = transpile_and_compress(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    assert compressed_litmus_circuit


@pytest.mark.filterwarnings("ignore::UserWarning")
def test_transpile_and_compress_coupling_map(litmus_circuit, backend):

    # Coupling Map

    if (backend is None or
       backend.configuration().coupling_map is None):
        coupling_map = None

    else:
        coupling_list = backend.configuration().coupling_map
        coupling_map = qiskit.transpiler.CouplingMap(
            couplinglist=coupling_list)

    # Transpile and Compress

    compressed_litmus_circuit = transpile_and_compress(
        litmus_circuit,
        backend,
        coupling_map=coupling_map,
        seed_transpiler=1234)

    assert compressed_litmus_circuit


# Test Full Map

def test_full_map(litmus_circuit, backend):

    transpiled_litmus_circuit = transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    full_map = get_full_map(transpiled_litmus_circuit, verbose=True)

    assert full_map


def test_full_map_value():

    fixed_litmus_circuit = get_litmus_circuit(qubits_count=3)

    backend = FakeLimaV2()

    transpiled_litmus_circuit = transpile(
        fixed_litmus_circuit,
        backend,
        seed_transpiler=1234)

    full_map = get_full_map(transpiled_litmus_circuit)

    assert full_map == [0, 2, 1, 3, 4]
