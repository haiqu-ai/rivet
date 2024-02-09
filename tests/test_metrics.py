from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag

from qml_transpiler import get_gates_counter
from qml_transpiler import transpile_and_return_metrics


def test_get_gates_counter():

    circuit = QuantumCircuit(2)

    circuit.h((0, 1))
    circuit.cz(0, 1)
    circuit.x((0, 1))

    circuit.barrier()
    circuit.measure_all()

    dag = circuit_to_dag(circuit)

    gates_counter = get_gates_counter(dag)

    assert gates_counter == {1: 6, 2: 1}


def test_transpile_and_return_metrics(litmus_circuit, backend):

    litmus_circuit.ccx(0, 1, 2)

    transpiled_litmus_circuit, metrics = transpile_and_return_metrics(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    return transpiled_litmus_circuit, metrics
