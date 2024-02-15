from collections import Counter

from qiskit import QuantumCircuit
from qiskit.converters import circuit_to_dag

from qml_transpiler import transpile_and_return_metrics


def test_gates_counter():

    circuit = QuantumCircuit(2)

    circuit.h((0, 1))
    circuit.cz(0, 1)
    circuit.x((0, 1))

    circuit.barrier()
    circuit.measure_all()

    dag = circuit_to_dag(circuit)

    dag_nodes = dag.op_nodes(include_directives=False)

    qubit_counts = sorted(node.op.num_qubits for node in dag_nodes)

    gates_counter = dict(Counter(qubit_counts))

    assert gates_counter == {1: 6, 2: 1}


def test_transpile_and_return_metrics(litmus_circuit, backend):

    litmus_circuit.ccx(0, 1, 2)

    transpiled_litmus_circuit, metrics = transpile_and_return_metrics(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    assert transpiled_litmus_circuit is not None
    assert metrics is not None


def test_composite_callback(litmus_circuit, backend):

    callback_check = {'ok': False}

    def custom_callback(**parameters):

        callback_check['ok'] = True

    transpiled_litmus_circuit, metrics = transpile_and_return_metrics(
        litmus_circuit,
        backend,
        callback=custom_callback,
        seed_transpiler=1234)

    assert callback_check['ok'] is True
    assert metrics is not None
