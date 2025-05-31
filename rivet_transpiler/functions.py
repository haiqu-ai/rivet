""" Service Functions used for Rivet Transpiler examples and checks. """

import qiskit

import hashlib

import numpy as np

from collections import deque


# 1) Get Litmus Circuit

def get_litmus_circuit(qubits_count, circuit_name=None, registers_count=1):

    """
    Create a Litmus test circuit.

    Args:
        qubits_count (int): The total number of qubits in the circuit.
        circuit_name (str, optional): A name for the circuit.
        registers_count (int, optional): The number of quantum registers in the circuit.

    Returns:
        QuantumCircuit: A Litmus test quantum circuit.
    """

    quantum_registers = []

    for register_index in range(registers_count):

        qubits_per_register = qubits_count // registers_count

        register_name = f"{circuit_name}_{register_index}"

        quantum_register = qiskit.QuantumRegister(qubits_per_register,
                                                  register_name)

        quantum_registers.append(quantum_register)

    litmus_circuit = qiskit.QuantumCircuit(*quantum_registers)

    qubits = list(range(qubits_count))

    # Parameterized RZs

    for qubit in qubits:

        parameter = qiskit.circuit.Parameter(f"{circuit_name}_{qubit}")

        litmus_circuit.rz(parameter, qubit)

    # CX Ladder

    for control_qubit, target_qubit in zip(qubits, qubits[1:]):

        litmus_circuit.cx(control_qubit, target_qubit)

    # Last-to-first CX

    litmus_circuit.cx(qubits[-1], qubits[0])

    litmus_circuit.barrier(label=circuit_name)

    return litmus_circuit


# 2) Get CNOT Circuit

def get_cnot_circuit(qubits_count, circuit_name=None, cnot_qubits=None, registers_count=1):

    """
    Create a CNOT test circuit.

    Args:
        qubits_count (int): The total number of qubits in the circuit.
        circuit_name (str, optional): A name for the circuit.
        cnot_qubits (list of int, optional): The qubits involved in the CNOT gate.
        registers_count (int, optional): The number of quantum registers in the circuit.

    Returns:
        QuantumCircuit: A CNOT test quantum circuit.
    """

    if cnot_qubits is None:

        cnot_qubits = [0, 1]

    quantum_registers = []

    for register_index in range(registers_count):

        qubits_per_register = qubits_count // registers_count

        register_name = f"{circuit_name}_{register_index}"

        quantum_register = qiskit.QuantumRegister(qubits_per_register,
                                                  register_name)

        quantum_registers.append(quantum_register)

    cnot_circuit = qiskit.QuantumCircuit(*quantum_registers)

    qubits = list(range(qubits_count))

    # Parameterized RZs

    for qubit in qubits:

        parameter = qiskit.circuit.Parameter(f"{circuit_name}_{qubit}")

        cnot_circuit.rz(parameter, qubit)

    # CNOT

    cnot_circuit.cx(*cnot_qubits)

    cnot_circuit.barrier(label=circuit_name)

    return cnot_circuit


# 3) Get Sinusoids

def get_sinusoids(qubits_count,
                  frequencies_count=None,
                  frequencies=None, amplitudes=None,
                  min_amplitude=1, max_amplitude=3):

    """
    Generate sinusoidal waveforms for qubit operations.

    Args:
        qubits_count (int): The total number of qubits.
        frequencies_count (int, optional): The number of different frequencies to use.
        frequencies (array-like, optional): Specific frequencies to use.
        amplitudes (array-like, optional): Specific amplitudes for each frequency.
        min_amplitude (float, optional): Minimum amplitude value.
        max_amplitude (float, optional): Maximum amplitude value.

    Returns:
        array: An array of normalized sinusoidal waveforms.
    """

    samples_count = 2 ** qubits_count

    time_samples = np.linspace(0, 2 * np.pi, samples_count)

    if frequencies is None:

        frequencies = np.random.uniform(low=1,
                                        high=samples_count // 2,
                                        size=(frequencies_count,)).astype(int)
    if amplitudes is None:

        frequencies_count = len(frequencies)

        amplitudes = np.random.uniform(low=min_amplitude,
                                       high=max_amplitude,
                                       size=(frequencies_count,))

    sinusoids = np.zeros(samples_count)

    for amplitude, frequency in zip(amplitudes, frequencies):

        sinusoid = amplitude * np.sin(frequency * time_samples)

        sinusoids = sinusoids + sinusoid

    normalized_sinusoids = sinusoids / np.sqrt(np.sum(sinusoids ** 2))

    # print("frequencies:", frequencies)
    # print("amplitudes:", amplitudes)
    # print("sinusoids:", sinusoids)
    # print("normalized_sinusoids:", normalized_sinusoids)

    return normalized_sinusoids


# 4) Get IBM Cost

def get_ibm_cost(qiskit_circuit,
                 depth_penalty_factor=0.995,
                 one_qubit_gate_fidelity=0.9996,
                 two_qubit_gate_fidelity=0.99):

    """
    Calculate the IBM Cost for a Qiskit circuit.

    IBM Cost definition: https://arxiv.org/abs/2008.08571 (1)
    Fidelities:          https://arxiv.org/abs/2202.14025 (Table I)
    Fidelity Values:     https://github.com/ArlineQ/arline_quantum/blob/master/arline_quantum/hardware/ibm.py

    Args:
        qiskit_circuit (QuantumCircuit): The input Qiskit quantum circuit.
        depth_penalty_factor (float, optional): A factor for depth penalty.
        one_qubit_gate_fidelity (float, optional): Fidelity of one-qubit gates.
        two_qubit_gate_fidelity (float, optional): Fidelity of two-qubit gates.

    Returns:
        float: The calculated IBM Cost.
    """

    # IBM Cost: https://arxiv.org/abs/2008.08571 (1)
    # Fidelity Values: https://arxiv.org/abs/2202.14025
    # Fidelity Values: https://github.com/ArlineQ/arline_quantum/blob/master/arline_quantum/hardware/ibm.py

    # Circuit

    remove_barriers_pass = qiskit.transpiler.passes.RemoveBarriers()

    circuit = remove_barriers_pass(qiskit_circuit)

    circuit.remove_final_measurements()

    # Fidelities

    fidelity_product = 1

    for instruction in circuit.data:

        qubit_count = instruction.operation.num_qubits

        if qubit_count == 1:
            fidelity_product *= one_qubit_gate_fidelity

        elif qubit_count == 2:
            fidelity_product *= two_qubit_gate_fidelity

        else:
            raise ValueError(f"More then 2-qubit {instruction.operation}")

    # IBM Cost - https://arxiv.org/abs/2008.08571 (1)

    ibm_cost = depth_penalty_factor ** circuit.depth() * fidelity_product

    return ibm_cost


# 5) Hashing

def get_circuit_hash(circuit, decomposition_level=None):

    """
    Calculate hash for Qiskit quantum circuit.

    This function computes a SHA256 hash value that represents a given quantum circuit.
    It traverses circuit DAG, iterates over instructions, including the quantum operations and their parameters,
    and combines them to generate a hash value.
    Optionally, the traversal can be limited to a specified decomposition level.
    Hash is calculated only for "leaf" nodes, which can not be decomposed further.
    The resulting hash can be used to uniquely identify a specific circuit structure.

    Following attributes are used to calculate hash for every operation:
    - qubit and bit indices,
    - operation name,
    - operation parameters.

    Qiskit ParameterExpression values are skipped - circuits with different Parameters will have identical hash.

    Inspired by Qiskit "soft_compare" gate function:
    https://github.com/Qiskit/qiskit/blob/main/qiskit/circuit/instruction.py#L227

    Parameters:
    - circuit (QuantumCircuit): The quantum circuit for which to compute the hash.
    - decomposition_level (int, optional): Maximum level of decomposition for circuit instructions.
      If "None" (default), the deepest decomposition is done.

    Returns:
    - int: An integer representing the computed hash value.

    Example:
    >>> my_circuit = QuantumCircuit(2)
    >>> my_circuit.h(0)
    >>> my_circuit.cx(0, 1)
    >>> hash_value = get_circuit_hash(my_circuit)
    >>> print(hash_value)
    "62559021281660068776592236282478300669138546894602824343710100835365445539986"
    """

    hash_object = hashlib.sha256(b'')

    # Circuit Traversal

    initial_level = 0
    initial_qubit_base = list(range(circuit.num_qubits))
    initial_bit_base = list(range(circuit.num_clbits))

    initial_record = (initial_level,
                      initial_qubit_base,
                      initial_bit_base,
                      circuit)

    stack = deque([initial_record])

    while stack:

        current_record = stack.pop()

        level, qubit_base, bit_base, current_circuit = current_record

        current_dag = qiskit.converters.circuit_to_dag(current_circuit)

        for node in current_dag.topological_op_nodes():

            # Relative Indices

            relative_qubits = [current_circuit.find_bit(qubit).index
                               for qubit in node.qargs]

            relative_bits = [current_circuit.find_bit(bit).index
                             for bit in node.cargs]

            # Absolute Indices

            absolute_qubits = [qubit_base[qubit] for qubit in relative_qubits]
            absolute_bits = [bit_base[bit] for bit in relative_bits]

            # Sub Circuit

            operation = node.op

            sub_circuit = operation.definition

            if level == decomposition_level or sub_circuit is None:

                # Calculate Hash of Leaf Node

                # Collect Values

                values = [absolute_qubits,
                          absolute_bits,
                          operation.name]

                # Collect Parameters

                for parameter in operation.params:

                    if isinstance(parameter, qiskit.circuit.parameter.ParameterExpression):

                        parameter = None

                    values.append(parameter)

                # Update Hash

                for value in values:

                    encoded_value = repr(value).encode('utf-8')

                    hash_object.update(encoded_value)

            else:

                # Add new Record to the Stack

                new_record = (level + 1,
                              absolute_qubits, absolute_bits,
                              sub_circuit)

                stack.append(new_record)

    # Digest Hash

    hash_bytes = hash_object.digest()

    hash_value = int.from_bytes(hash_bytes, byteorder='little')

    return hash_value


def qml_transpile(circuit, parameter_values):
    """
    Bind parameters and locally re-optimize a transpiled circuit for QML workflows.

    Args:
        circuit (QuantumCircuit): A transpiled, parameterized Qiskit circuit.
        parameter_values (dict): Dictionary mapping Parameter objects or names to values.

    Returns:
        QuantumCircuit: A fully bound, locally re-optimized circuit.
    """
    import qiskit
    from qiskit.transpiler.passes import Optimize1qGatesDecomposition, CommutativeCancellation
    from qiskit.transpiler import PassManager

    # 1. Bind parameters (use assign_parameters for compatibility)
    try:
        bound_circuit = circuit.bind_parameters(parameter_values)
    except AttributeError:
        bound_circuit = circuit.assign_parameters(parameter_values, inplace=False)

    # 2. Local re-optimization (safe for already routed circuits)
    pm = PassManager([
        Optimize1qGatesDecomposition(basis=['u3','u2','u1','rz','rx','ry','sx','x','y','z','h']),
        CommutativeCancellation(),
    ])
    optimized_circuit = pm.run(bound_circuit)

    # 3. Preserve layout if present
    if hasattr(circuit, 'layout') and circuit.layout is not None:
        optimized_circuit._layout = circuit.layout
    if hasattr(circuit, 'calibrations') and circuit.calibrations:
        optimized_circuit.calibrations = circuit.calibrations.copy()

    return optimized_circuit
