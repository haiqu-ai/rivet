import qiskit

from rivet_transpiler import get_sinusoids
from tests.integration import (
    check_delta,
    get_circuits_to_compare,
    plot_results_to_compare,
    run_circuits_to_compare,
)

# Parameters

AE_QFT_QUBIT_COUNT = 5

OPTIMIZATION_LEVEL = 3

SHOTS_COUNT = 1000
SEED_TRANSPILER = 1234

LAYOUT_METHOD = None
ROUTING_METHOD = None

# Possible Layout Methods
# ‘trivial’, ‘dense’, ‘noise_adaptive’, ‘sabre’

# Possible Routing Methods
# ‘basic’, ‘lookahead’, ‘stochastic’, ‘sabre’, ‘none’


# Test Integration


def test_transpilation_types_litmus(litmus_circuit, backend):

    QUBITS_COUNT = litmus_circuit.num_qubits

    qubits = list(range(QUBITS_COUNT))

    # Initial State Part

    initial_state_circuit = qiskit.QuantumCircuit(QUBITS_COUNT)

    initial_state_circuit.x(0)
    initial_state_circuit.barrier()

    # Measurement Part

    measurement_circuit = qiskit.QuantumCircuit(QUBITS_COUNT, QUBITS_COUNT)
    measurement_circuit.measure(qubits, qubits)

    # Circuit Parts

    CIRCUIT_PARTS = [
        initial_state_circuit,
        litmus_circuit,
        litmus_circuit,
        measurement_circuit,
    ]

    # Compare Transpilation Types

    circuits_to_compare = get_circuits_to_compare(
        circuit_parts=CIRCUIT_PARTS,
        backend=backend,
        layout_method=LAYOUT_METHOD,
        routing_method=ROUTING_METHOD,
        seed_transpiler=SEED_TRANSPILER,
        optimization_level=OPTIMIZATION_LEVEL,
    )

    results = run_circuits_to_compare(
        circuits_to_compare=circuits_to_compare,
        backend=backend,
        shots_count=SHOTS_COUNT,
    )

    plot_results_to_compare(results)

    assert check_delta(results, 0.1), (
        "Delta Check shows that "
        "counts between transpilation types "
        "differ by more then 10%"
    )


def test_transpilation_types_ae_and_qft(litmus_circuit, backend):

    QUBITS_COUNT = AE_QFT_QUBIT_COUNT

    qubits = list(range(QUBITS_COUNT))

    # Sinusoids

    sinusoids_data = get_sinusoids(QUBITS_COUNT, frequencies=[1, 3], amplitudes=[10, 5])

    # AE Part

    amplitude_embedding = qiskit.circuit.library.StatePreparation(sinusoids_data)

    ae_circuit = qiskit.QuantumCircuit(QUBITS_COUNT)
    ae_circuit.append(amplitude_embedding, qargs=qubits)
    ae_circuit.barrier()

    # QFT Part

    qft = qiskit.circuit.library.QFT(num_qubits=QUBITS_COUNT)

    qft_circuit = qiskit.QuantumCircuit(QUBITS_COUNT)
    qft_circuit.append(qft, qargs=qubits)
    qft_circuit.barrier()

    # Measurement Part

    measurement_circuit = qiskit.QuantumCircuit(QUBITS_COUNT, QUBITS_COUNT)
    measurement_circuit.measure(qubits, qubits)

    # Circuit Parts

    CIRCUIT_PARTS = [ae_circuit, qft_circuit, measurement_circuit]

    # Compare Transpilation Types

    circuits_to_compare = get_circuits_to_compare(
        circuit_parts=CIRCUIT_PARTS,
        backend=backend,
        layout_method=LAYOUT_METHOD,
        routing_method=ROUTING_METHOD,
        seed_transpiler=SEED_TRANSPILER,
        optimization_level=OPTIMIZATION_LEVEL,
    )

    results = run_circuits_to_compare(
        circuits_to_compare=circuits_to_compare,
        backend=backend,
        shots_count=SHOTS_COUNT,
    )

    # plot_results_to_compare(results)

    assert check_delta(results, 0.2), (
        "Delta Check shows that "
        "counts between transpilation types "
        "differ by more then 20%"
    )
