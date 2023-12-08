""" Service Functions used for QML Transpiler examples and checks. """

import qiskit

import numpy as np


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