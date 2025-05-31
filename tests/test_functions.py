import pytest

import qiskit

from rivet_transpiler import get_ibm_cost

from rivet_transpiler import get_litmus_circuit
from rivet_transpiler import get_cnot_circuit
from rivet_transpiler import get_sinusoids

from rivet_transpiler import get_circuit_hash


def test_get_ibm_cost_value():

    litmus_circuit = get_litmus_circuit(qubits_count=3)

    ibm_cost = get_ibm_cost(litmus_circuit)

    rounded_ibm_cost = round(ibm_cost, 4)

    assert rounded_ibm_cost == 0.9499


def test_get_ibm_cost_toffoli():

    toffoli_circuit = qiskit.QuantumCircuit(3)

    toffoli_circuit.ccx(0, 1, 2)

    with pytest.raises(ValueError):

        ibm_cost = get_ibm_cost(toffoli_circuit)

        return ibm_cost


def test_cnot_circuit(qubits_count):

    get_cnot_circuit(qubits_count=qubits_count)


def test_get_sinusoids(qubits_count):

    get_sinusoids(qubits_count=qubits_count, frequencies_count=1)

    get_sinusoids(qubits_count=qubits_count, frequencies=[1])

    get_sinusoids(qubits_count=qubits_count, frequencies_count=2, amplitudes=[1, 2])

    get_sinusoids(qubits_count=qubits_count, frequencies=[1, 2], amplitudes=[10, 20])


# Test Get Circuit Hash

def test_get_circuit_hash(litmus_circuit):

    get_circuit_hash(litmus_circuit)


def test_get_circuit_hash_instructions_order():

    # XH Circuit

    xh_circuit = qiskit.QuantumCircuit(2)

    xh_circuit.x(0)
    xh_circuit.h(1)

    xh_circuit_hash = get_circuit_hash(xh_circuit)

    # HX Circuit

    hx_circuit = qiskit.QuantumCircuit(2)

    hx_circuit.h(1)
    hx_circuit.x(0)

    hx_circuit_hash = get_circuit_hash(hx_circuit)

    assert xh_circuit_hash == hx_circuit_hash


def bind_parameters_with_offset(circuit, offset=0):

    bound_circuit = circuit.copy()

    for index, parameter in enumerate(bound_circuit.parameters):

        bound_circuit.assign_parameters(
            {parameter: index + offset},
            inplace=True)

    return bound_circuit


def test_get_circuit_hash_parameters(litmus_circuit):

    # Bound Circuits

    bound_circuit = bind_parameters_with_offset(litmus_circuit, offset=0)
    bound_circuit_same_parameters = bind_parameters_with_offset(litmus_circuit, offset=0)
    bound_circuit_other_parameters = bind_parameters_with_offset(litmus_circuit, offset=1)

    # Hashes

    circuit_hash = get_circuit_hash(bound_circuit)
    circuit_same_parameters_hash = get_circuit_hash(bound_circuit_same_parameters)
    circuit_other_parameters_hash = get_circuit_hash(bound_circuit_other_parameters)

    assert circuit_hash == circuit_same_parameters_hash
    assert circuit_hash != circuit_other_parameters_hash


def test_get_circuit_hash_structures(qubits_count):

    cnot_circuit = get_cnot_circuit(qubits_count, "CNOT")
    litmus_circuit = get_litmus_circuit(qubits_count, "Litmus")
    litmus_circuit_same = get_litmus_circuit(qubits_count, "Litmus_Same")

    # Hashes

    cnot_circuit_hash = get_circuit_hash(cnot_circuit)
    litmus_circuit_hash = get_circuit_hash(litmus_circuit)
    litmus_circuit_same_hash = get_circuit_hash(litmus_circuit_same)

    assert litmus_circuit_hash == litmus_circuit_same_hash
    assert litmus_circuit_hash != cnot_circuit_hash


def test_get_circuit_hash_hxxh():

    # Circuits

    hx_circuit = qiskit.QuantumCircuit(2)
    hx_circuit.h(1)
    hx_circuit.x(1)

    xh_circuit = qiskit.QuantumCircuit(2)
    xh_circuit.x(1)
    xh_circuit.h(1)

    # Hashes

    hx_circuit_hash = get_circuit_hash(hx_circuit)
    xh_circuit_hash = get_circuit_hash(xh_circuit)

    assert hx_circuit_hash != xh_circuit_hash


def test_get_circuit_hash_ixxi():

    ix_circuit = qiskit.QuantumCircuit(2)
    xi_circuit = qiskit.QuantumCircuit(2)

    ix_circuit.x(1)
    xi_circuit.x(0)

    ix_gate = ix_circuit.to_gate()
    xi_gate = xi_circuit.to_gate()

    ix_gate.name = "IX Gate"
    xi_gate.name = "XI Gate"

    # Composite Circuits

    composite_circuit_ix = qiskit.QuantumCircuit(3)
    composite_circuit_xi = qiskit.QuantumCircuit(3)

    composite_circuit_ix.compose(ix_gate, qubits=[0, 1], inplace=True)
    composite_circuit_xi.compose(xi_gate, qubits=[1, 2], inplace=True)

    # Hashes

    ix_circuit_hash = get_circuit_hash(composite_circuit_ix)
    xi_circuit_hash = get_circuit_hash(composite_circuit_xi)

    assert ix_circuit_hash == xi_circuit_hash


def test_qml_transpile_preserves_layout_and_optimizes():
    import qiskit
    from rivet_transpiler import qml_transpile, get_litmus_circuit
    from qiskit_ibm_runtime.fake_provider import FakeLimaV2

    # Create a parameterized, transpiled circuit
    circuit = get_litmus_circuit(3, "Litmus")
    backend = FakeLimaV2()
    transpiled = qiskit.transpile(circuit, backend, optimization_level=1)
    layout_before = transpiled.layout

    # Prepare parameter values
    param_dict = {p: 0.5 for p in transpiled.parameters}

    # Run qml_transpile
    optimized = qml_transpile(transpiled, param_dict)

    # Check all parameters are bound
    assert not optimized.parameters
    # Check layout is preserved
    assert hasattr(optimized, 'layout') and optimized.layout == layout_before
    # Check circuit is smaller than naive bind (gate count or depth)
    try:
        naive = transpiled.bind_parameters(param_dict)
    except AttributeError:
        naive = transpiled.assign_parameters(param_dict, inplace=False)
    assert optimized.size() <= naive.size()
    assert optimized.depth() <= naive.depth()
