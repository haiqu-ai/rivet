"""
Module containing functions to build and compare test circuits for integration tests.
"""

import qiskit

from qiskit_aer import AerSimulator

from rivet_transpiler import transpile
from rivet_transpiler import transpile_left
from rivet_transpiler import transpile_right
from rivet_transpiler import transpile_chain

from rivet_transpiler import get_full_map

import warnings

try:
    from IPython.display import display

except ModuleNotFoundError:
    warnings.warn("IPython.display not found", ImportWarning)


# Build Circuit Functions

def build_combined_circuit(circuit_parts, backend, *arguments, **key_arguments):

    qubits_count = circuit_parts[0].num_qubits

    # Compose

    combined_circuit = qiskit.QuantumCircuit(qubits_count)

    for circuit_part in circuit_parts:

        combined_circuit.compose(circuit_part, inplace=True)

    # combined_litmus_circuit.measure_active()

    # Transpile

    transpiled_combined_circuit = transpile(
        combined_circuit,
        backend,
        *arguments, **key_arguments
    )

    return transpiled_combined_circuit


def build_blocks_circuit(circuit_parts, backend, *arguments, **key_arguments):

    # Transpile

    transpiled_circuit_parts = []

    for circuit_part in circuit_parts:

        transpiled_circuit_part = transpile(
            circuit_part,
            backend,
            *arguments, **key_arguments
        )

        transpiled_circuit_parts.append(transpiled_circuit_part)

        full_map = get_full_map(transpiled_circuit_part)

        initial_layout = full_map[:circuit_part.num_qubits]

        key_arguments['initial_layout'] = initial_layout

    # Compose

    blocks_circuit = None

    for transpiled_circuit_part in transpiled_circuit_parts:

        if blocks_circuit is None:
            blocks_circuit = transpiled_circuit_part

        else:
            blocks_circuit.compose(transpiled_circuit_part, inplace=True)

    return blocks_circuit


def build_right_circuit(circuit_parts, backend, *arguments, **key_arguments):

    # Transpile

    central_circuit = transpile(
        circuit_parts[0],
        backend,
        *arguments, **key_arguments
    )

    for right_circuit in circuit_parts[1:]:

        transpiled_right_circuit = transpile_right(
            central_circuit=central_circuit,
            right_circuit=right_circuit,
            backend=backend,
            *arguments, **key_arguments
        )

        central_circuit = transpiled_right_circuit

    return transpiled_right_circuit


def build_left_circuit(circuit_parts, backend, *arguments, **key_arguments):

    reversed_circuit_parts = list(reversed(circuit_parts))

    # Transpile

    central_circuit = transpile(
        reversed_circuit_parts[0],
        backend,
        *arguments, **key_arguments
    )

    for left_circuit in reversed_circuit_parts[1:]:

        transpiled_left_circuit = transpile_left(
            central_circuit=central_circuit,
            left_circuit=left_circuit,
            backend=backend,
            *arguments, **key_arguments
        )

        central_circuit = transpiled_left_circuit

    return transpiled_left_circuit


# Comparison Functions

def get_circuits_to_compare(circuit_parts, backend, *arguments, **key_arguments):

    # Build Circuits

    combined_circuit = build_combined_circuit(circuit_parts, backend, *arguments, **key_arguments)
    blocks_circuit = build_blocks_circuit(circuit_parts, backend, *arguments, **key_arguments)
    chain_circuit = transpile_chain(circuit_parts, backend, *arguments, **key_arguments)

    right_circuit = build_right_circuit(circuit_parts, backend, *arguments, **key_arguments)
    left_circuit = build_left_circuit(circuit_parts, backend, *arguments, **key_arguments)

    circuits_to_compare = {
        "Combined": combined_circuit,
        "Blocks": blocks_circuit,
        "Chain": chain_circuit,
        "Right": right_circuit,
        "Left": left_circuit,
    }

    return circuits_to_compare


def run_circuits_to_compare(circuits_to_compare, backend, shots_count):

    results = {}

    for circuit_name, circuit in circuits_to_compare.items():

        # Assign Parameters

        for index, parameter in enumerate(circuit.parameters):

            circuit.assign_parameters({parameter: index}, inplace=True)

        # Backend

        if backend is None:
            run_backend = AerSimulator()
            run_circuit = transpile(circuit, run_backend)
        else:
            run_backend = backend
            run_circuit = circuit

        # Run

        job = run_backend.run(run_circuit, shots=shots_count)

        counts = job.result().get_counts()

        results[circuit_name] = counts

    return results


def plot_results_to_compare(results,
                            print_counts=True,
                            display_plots=False):
    # Counts

    if print_counts is True:

        for circuit_name, counts in results.items():

            print(f"{circuit_name:<8} {counts}")

    # Plots

    if display_plots is True:

        for circuit_name, counts in results.items():

            display(qiskit.visualization.plot_histogram(
                counts,
                figsize=(7, 2),
                bar_labels=False,
                sort='value_desc',
                title=circuit_name
            ))


def check_delta(results, delta_treshold=0.1):

    # Total Counts

    total_counts = {}

    for circuit_name, counts in results.items():

        for state, count in counts.items():

            if state in total_counts:
                total_counts[state] += count

            else:
                total_counts[state] = count

    # Average Counts

    circuits_count = len(results)

    average_counts = {state: count / circuits_count
                      for state, count in total_counts.items()}

    # Deltas

    check_pass_flags = []

    for circuit_name, counts in results.items():

        total_delta = 0
        total_counts = 0

        for state, count in counts.items():

            average_count = average_counts[state]

            delta = abs(count - average_count)

            total_delta += delta
            total_counts += count

        # Check Passed

        check_pass_flag = total_delta < delta_treshold * total_counts

        check_pass_flags.append(check_pass_flag)

    # All Passed

    all_checks_passed = all(check_pass_flags)

    return all_checks_passed
