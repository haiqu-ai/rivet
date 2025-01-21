import qiskit

from rivet_transpiler import get_full_map
from rivet_transpiler import remove_unused_qubits

from tests.integration import run_circuits_to_compare
from tests.integration import check_delta


def test_remove_unused_qubits_full_map(litmus_circuit, backend):

    transpiled_litmus_circuit = qiskit.transpile(
        litmus_circuit,
        backend,
        seed_transpiler=1234)

    optimized_circuit = remove_unused_qubits(transpiled_litmus_circuit)
    
    full_map = get_full_map(optimized_circuit)

    if optimized_circuit.layout is not None:
        final_index_layout = optimized_circuit.layout.final_index_layout()
    else:
        final_index_layout = full_map
    
    assert full_map == final_index_layout


def test_remove_unused_qubits_compare(litmus_circuit, backend):

    test_circuit = qiskit.QuantumCircuit(
        litmus_circuit.num_qubits)

    test_circuit.x(0)
    test_circuit.compose(litmus_circuit, inplace=True)

    test_circuit.measure_all()

    transpiled_circuit = qiskit.transpile(
        test_circuit,
        backend,
        seed_transpiler=1234)

    optimized_circuit = remove_unused_qubits(test_circuit)

    circuits_to_compare = {
        'transpiled': transpiled_circuit,
        'optimized': optimized_circuit}

    results = run_circuits_to_compare(
        circuits_to_compare,
        backend,
        shots_count=1024)

    assert check_delta(results, 0.1), ("Delta Check shows that "
                                       "counts between transpilation types "
                                       "differ by more then 10%")
