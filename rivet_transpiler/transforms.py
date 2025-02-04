""" Rivet transforms. """

import qiskit


def remove_unused_qubits(circuit):

    """
    Remove unused qubits from a Qiskit QuantumCircuit, recreate Registers, Qubits, Instructions,
    and Layouts while preserving the original structure and functionality of the circuit.

    Parameters:
        circuit (qiskit.QuantumCircuit): The input quantum circuit from which unused qubits
                                         are to be removed.
    Returns:
        qiskit.QuantumCircuit: A new QuantumCircuit instance with only the used qubits,
                               updated Registers, Qubits, Instructions and Layouts.
    Functionality:
        - Identify and collect only the Qubits that are used in the Circuit's Instructions.
        - Reconstruct quantum Registers containing only the used Qubits while preserving the Register names.
        - Create a mapping between original Qubits and new Qubits in the updated Registers.
        - Rebuild the Circuit's instructions, replacing old Qubits with new ones based on the mapping.
        - Update the global phase, calibrations, and metadata of the circuit to match the original.
        - Adjust the layouts of the circuit:
            - Modify the Initial Layout, Input Qubit Mapping, and Final Layout to align with the used Qubits.
            - Ensure consistency between the Layouts and the reduced set of Qubits.
        - The updated Circuit retains the same functionality as the original but with improved resource utilization.
    """

    circuit = circuit.copy()

    # Used Qubits

    used_qubits = []

    for qubit in circuit.qubits:
        for instruction in circuit.data:

            if qubit in instruction.qubits:
                used_qubits.append(qubit)
                break

    # Registers

    registers = {register: [] for register in circuit.qregs}

    for qubit in used_qubits:
        locations = circuit.find_bit(qubit)

        for register, index in locations.registers:
            registers[register].append((qubit, index))

    # New Registers

    new_registers = defaultdict(list)
    qubit_mapping = {}

    for register, qubits in registers.items():

        new_register = qiskit.QuantumRegister(
            size=len(qubits),
            name=register.name)

        sorted_qubits = sorted(qubits, key=lambda qubit: qubit[1])

        for new_index, (qubit, index) in enumerate(sorted_qubits):

            new_qubit = qiskit.circuit.Qubit(
                register=new_register,
                index=new_index)

            new_registers[new_register].append(new_qubit)
            qubit_mapping[qubit] = new_qubit

    # New Qubits

    new_qubits = list(qubit_mapping.values())

    # New Instructions

    new_instructions = []

    for instruction in circuit.data:

        new_instruction_qubits = [
            qubit_mapping[qubit]
            for qubit in instruction.qubits]

        new_instruction = instruction.replace(
            operation=instruction.operation,
            qubits=new_instruction_qubits,
            clbits=instruction.clbits)

        new_instructions.append(new_instruction)

    # New Circuit

    new_circuit = qiskit.QuantumCircuit()

    new_circuit.add_register(*new_registers, *circuit.cregs)

    new_circuit.data = new_instructions

    new_circuit.global_phase = circuit.global_phase
    new_circuit.calibrations = circuit.calibrations
    new_circuit.metadata = circuit.metadata

    # Layouts

    layout = circuit.layout

    if layout is not None:

        initial_layout = layout.initial_layout
        input_qubit_mapping = layout.input_qubit_mapping
        final_layout = layout.final_layout

        output_qubit_list = layout._output_qubit_list

        # Used Indices

        used_indices = [index for index, qubit
                        in enumerate(output_qubit_list)
                        if qubit in used_qubits]

        # Used Input Qubits

        sorted_initial_layout = dict(sorted(
            initial_layout.get_physical_bits().items()))

        used_input_qubits = [qubit for index, qubit
                             in sorted_initial_layout.items()
                             if index in used_indices]

        # New Input Qubit Mapping

        shift = 0
        new_input_qubit_mapping = {}

        for qubit, index in input_qubit_mapping.items():

            if qubit in used_input_qubits:
                new_input_qubit_mapping[qubit] = index - shift
            else:
                shift += 1

        # Index Mapping

        index_mapping = {}

        for new_index, qubit in enumerate(used_input_qubits):

            index = initial_layout[qubit]
            index_mapping[index] = new_index

        # New Initial Layout

        new_initial_layout_dict = {}

        for index, qubit in initial_layout.get_physical_bits().items():

            if qubit not in used_input_qubits:
                continue

            new_index = index_mapping[index]
            new_initial_layout_dict[new_index] = qubit

        new_initial_layout = layout.initial_layout.copy()

        new_initial_layout._v2p.clear()
        new_initial_layout._p2v.clear()

        for index, qubit in new_initial_layout_dict.items():

            new_initial_layout._v2p[qubit] = index
            new_initial_layout._p2v[index] = qubit

        # New Final Layout

        if final_layout is None:
            new_final_layout = None

        else:

            new_final_layout_dict = {}

            for index, qubit in final_layout.get_physical_bits().items():

                if qubit not in used_qubits:
                    continue

                new_qubit = qubit_mapping[qubit]
                new_index = index_mapping[index]

                new_final_layout_dict[new_index] = new_qubit

            new_final_layout = qiskit.transpiler.Layout(
                new_final_layout_dict)

        # New Layout

        new_layout = qiskit.transpiler.TranspileLayout(
            initial_layout=new_initial_layout,
            input_qubit_mapping=new_input_qubit_mapping,
            final_layout=new_final_layout,
            _input_qubit_count=len(new_qubits),
            _output_qubit_list=new_qubits)

        new_circuit._layout = new_layout

    return new_circuit
