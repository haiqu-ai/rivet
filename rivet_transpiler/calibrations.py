""" Functions and Constants used for conversion of AWS Calibrations to Qiskit Target. """

import qiskit


LUCY_ARN = "arn:aws:braket:eu-west-2::device/qpu/oqc/Lucy"

LUCY_NATIVE_GATES = ['ecr', 'i', 'rz', 'sx', 'x']

LUCY_SCHEME = {
    "one_qubit_section_name": "one_qubit",
    "two_qubit_section_name": "two_qubit",

    "gate_fidelity_name": "fRB",
    "readout_fidelity_name": "fRO",

    "two_qubit_fidelities": {"fCX": "cx"},

    "t1_name": "T1",
    "t2_name": "T2",

    "t1_time_unit": 10 ** -6,
    "t2_time_unit": 10 ** -6,

    "duration_1q_seconds": 50 * 10 ** -9,
    "duration_2q_seconds": 1000 * 10 ** -9,
    "qubit_frequency_hz": None
}

LUCY_COORDINATES = [[0, 0], [0, 1.5], [0, 3], [1.5, 3],
                    [3, 3], [3, 1.5], [3, 0], [1.5, 0]]


ASPEN_M3_ARN = "arn:aws:braket:us-west-1::device/qpu/rigetti/Aspen-M-3"

ASPEN_M3_NATIVE_GATES = ['rx', 'rz', 'cz', 'cphaseshift', 'xy']

ASPEN_M3_SCHEME = {
    "one_qubit_section_name": "1Q",
    "two_qubit_section_name": "2Q",

    "gate_fidelity_name": "f1QRB",
    "readout_fidelity_name": "fRO",
    "two_qubit_fidelities": {"fCZ": "cz",
                             "fCPHASE": "cphase",
                             "fXY": "xy"},
    "t1_name": "T1",
    "t2_name": "T2",

    "t1_time_unit": 1,
    "t2_time_unit": 1,

    "duration_1q_seconds": 40 * 10 ** -9,
    "duration_2q_seconds": 240 * 10 ** -9,
    "qubit_frequency_hz": None
}


def get_standard_calibrations(calibrations, scheme):

    # Scheme

    one_qubit_section_name = scheme.get("one_qubit_section_name")
    two_qubit_section_name = scheme.get("two_qubit_section_name")

    gate_fidelity_name = scheme.get("gate_fidelity_name")
    readout_fidelity_name = scheme.get("readout_fidelity_name")

    two_qubit_fidelities = scheme.get("two_qubit_fidelities")

    t1_name = scheme.get("t1_name")
    t2_name = scheme.get("t2_name")

    t1_time_unit = scheme.get("t1_time_unit")
    t2_time_unit = scheme.get("t2_time_unit")

    duration_1q_seconds = scheme.get("duration_1q_seconds")
    duration_2q_seconds = scheme.get("duration_2q_seconds")
    qubit_frequency_hz = scheme.get("qubit_frequency_hz")

    # Standard Calibrations

    standard_calibrations = {
        "one_qubit_gate_fidelities": dict(),
        "two_qubit_gate_fidelities": dict(),
        "readout_fidelities": dict(),

        "t1_seconds": dict(),
        "t2_seconds": dict(),

        "duration_1q_seconds": duration_1q_seconds,
        "duration_2q_seconds": duration_2q_seconds,
        "qubit_frequency_hz": qubit_frequency_hz
    }

    # 1-Qubit Calibrations

    one_qubit_calibrations = calibrations[one_qubit_section_name]

    for qubit_string, calibration in one_qubit_calibrations.items():

        qubit = int(qubit_string)

        # Times

        t1_seconds = calibration[t1_name] * t1_time_unit
        t2_seconds = calibration[t2_name] * t2_time_unit

        # Out Calibration

        gate_fidelity = calibration[gate_fidelity_name]
        readout_fidelity = calibration[readout_fidelity_name]

        standard_calibrations["one_qubit_gate_fidelities"][qubit] = gate_fidelity
        standard_calibrations["readout_fidelities"][qubit] = readout_fidelity

        standard_calibrations["t1_seconds"][qubit] = t1_seconds
        standard_calibrations["t2_seconds"][qubit] = t2_seconds

    # 2-Qubit Calibrations

    two_qubit_calibrations = calibrations[two_qubit_section_name]

    for qubits_string, calibration in two_qubit_calibrations.items():

        qubits = tuple(map(int, qubits_string.split('-')))

        # Fidelities

        fidelities = dict()

        for fidelity_name, instruction_name in two_qubit_fidelities.items():

            fidelity = calibration.get(fidelity_name)

            if fidelity is not None:

                fidelities[instruction_name] = fidelity

        standard_calibrations["two_qubit_gate_fidelities"][qubits] = fidelities

    return standard_calibrations


def get_target_from_calibrations(calibrations, target_instructions):

    # Calibrations

    one_qubit_gate_fidelities = calibrations.get("one_qubit_gate_fidelities")
    two_qubit_gate_fidelities = calibrations.get("two_qubit_gate_fidelities")

    readout_fidelities = calibrations.get("readout_fidelities")

    t1_seconds = calibrations.get("t1_seconds")
    t2_seconds = calibrations.get("t2_seconds")

    duration_1q_seconds = calibrations.get("duration_1q_seconds")
    duration_2q_seconds = calibrations.get("duration_2q_seconds")
    qubit_frequency_hz = calibrations.get("qubit_frequency_hz")

    # 1-Qubit Gate Properties

    one_qubit_gate_properties = dict()

    for qubit, gate_fidelity in one_qubit_gate_fidelities.items():

        gate_error = 1 - gate_fidelity

        gate_property = qiskit.transpiler.target.InstructionProperties(
            duration=duration_1q_seconds,
            error=gate_error)

        one_qubit_gate_properties[(qubit,)] = gate_property

    # 2-Qubit Gate Properties

    two_qubit_gate_properties = dict()

    for qubits, gate_fidelity in two_qubit_gate_fidelities.items():

        if isinstance(gate_fidelity, dict):
            gate_fidelity = sum(gate_fidelity.values()) / len(gate_fidelity)

        gate_error = 1 - gate_fidelity

        gate_property = qiskit.transpiler.target.InstructionProperties(
            duration=duration_2q_seconds,
            error=gate_error)

        two_qubit_gate_properties[qubits] = gate_property

    # Measure Properties

    measure_properties = dict()

    for qubit, readout_fidelity in readout_fidelities.items():

        readout_error = 1 - readout_fidelity

        measure_property = qiskit.transpiler.target.InstructionProperties(
            duration=duration_1q_seconds,
            error=readout_error)

        measure_properties[(qubit,)] = measure_property

    # Qubit Properties

    full_qubits_count = max(t1_seconds) + 1

    empty_qubit_property = qiskit.providers.QubitProperties()

    qubit_properties = [empty_qubit_property] * full_qubits_count

    for qubit, t1_seconds_value in t1_seconds.items():

        t2_seconds_value = t2_seconds[qubit]

        qubit_property = qiskit.providers.QubitProperties(
            t1=t1_seconds_value,
            t2=t2_seconds_value,
            frequency=qubit_frequency_hz)

        qubit_properties[qubit] = qubit_property

    # Target

    target = qiskit.transpiler.target.Target()

    for instruction in target_instructions:

        if instruction.name == "measure":

            properties = measure_properties

        elif instruction.num_qubits == 1:

            properties = one_qubit_gate_properties

        elif instruction.num_qubits == 2:

            properties = two_qubit_gate_properties

        target.add_instruction(
            instruction=instruction,
            properties=properties)

    target.qubit_properties = qubit_properties

    return target


def get_aspen_m3_coordinates(rows_count=2,
                             columns_count=5,
                             skip_qubits=[136],
                             row_index_offset=100,
                             column_index_offset=10,
                             row_coordinate_offset=5,
                             column_coordinate_offset=5):

    RING_COORDINATES = [[2, 3], [3, 2],
                        [3, 1], [2, 0],
                        [1, 0], [0, 1],
                        [0, 2], [1, 3]]

    qubit_indices_count = 0
    qubit_indices_count += row_index_offset * (rows_count - 1)
    qubit_indices_count += column_index_offset * (columns_count - 1)
    qubit_indices_count += len(RING_COORDINATES)

    coordinates = [[0, 0]] * qubit_indices_count

    for row in range(rows_count):

        for column in range(columns_count):

            for qubit_index, coordinate in enumerate(RING_COORDINATES):

                qubit = qubit_index + column_index_offset * column + row_index_offset * row

                if qubit in skip_qubits:
                    continue

                x, y = coordinate

                qubit_x = x + column_coordinate_offset * column
                qubit_y = y + row_coordinate_offset * row

                coordinates[qubit] = [qubit_y, qubit_x]

    return coordinates
