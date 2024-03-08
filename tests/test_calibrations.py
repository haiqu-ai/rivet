import pytest

import qiskit

from rivet_transpiler.calibrations import get_standard_calibrations
from rivet_transpiler.calibrations import get_target_from_calibrations

from rivet_transpiler.calibrations import LUCY_SCHEME
from rivet_transpiler.calibrations import ASPEN_M3_SCHEME
from rivet_transpiler.calibrations import get_aspen_m3_coordinates


EXAMPLE_LUCY_CALIBRATIONS = {

    'one_qubit': {'0': {'T1': 24.886750393070763,
                        'T2': 26.07078283012027,
                        'fRB': 0.9990355252411796,
                        'fRO': 0.9375,
                        'qubit': 0.0}},

    'two_qubit': {'0-1': {'coupling': {'control_qubit': 0.0, 'target_qubit': 1.0},
                          'fCX': 0.9215009652706455}}}

EXAMPLE_ASPEN_M3_CALIBRATIONS = {

    '1Q': {'0': {'fActiveReset': 0.973,
                 'fRO': 0.958,
                 'f1QRB': 0.9974637859811621,
                 'f1QRB_std_err': 4.907876922611825e-05,
                 'f1Q_simultaneous_RB': 0.9945241714466339,
                 'f1Q_simultaneous_RB_std_err': 0.00016101838459584627,
                 'T1': 1.0019627401991471e-05,
                 'T2': 1.8156447816365015e-05}},

    '2Q': {'0-1': {'fCZ': 0.9358053909432413,
                   'fCZ_std_err': 0.014037116464329336,
                   'fCPHASE': 0.9510506260276034,
                   'fCPHASE_std_err': 0.010576800940028584,
                   'fXY': 0.9755869557146251,
                   'fXY_std_err': 0.006168694499118298}}}

CALIBRATIONS = {
    "Lucy": [EXAMPLE_LUCY_CALIBRATIONS, LUCY_SCHEME],
    "Aspen-M-3": [EXAMPLE_ASPEN_M3_CALIBRATIONS, ASPEN_M3_SCHEME]
}


@pytest.mark.parametrize("calibrations, scheme",
                         CALIBRATIONS.values(),
                         ids=CALIBRATIONS.keys())
def test_target_to_calibrations(calibrations, scheme):

    # Standard Calibrations

    standard_calibrations = get_standard_calibrations(
        calibrations=calibrations,
        scheme=scheme)

    # Instructions

    x_instruction = qiskit.circuit.instruction.Instruction(
        name="x",
        num_qubits=1,
        num_clbits=0,
        params=[])

    cx_instruction = qiskit.circuit.instruction.Instruction(
        name="cx",
        num_qubits=2,
        num_clbits=0,
        params=[])

    measure_instruction = qiskit.circuit.instruction.Instruction(
        name="measure",
        num_qubits=1,
        num_clbits=1,
        params=[])

    instructions = [x_instruction,
                    cx_instruction,
                    measure_instruction]
    # Target

    target = get_target_from_calibrations(
        calibrations=standard_calibrations,
        target_instructions=instructions)

    assert target is not None


def test_get_aspen_m3_coordinates():

    aspen_m3_coordinates = get_aspen_m3_coordinates()

    assert aspen_m3_coordinates
