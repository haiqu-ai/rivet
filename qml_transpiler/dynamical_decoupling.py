"""
Dynamical Decoupling (DD) is a form of quantum error mitigation that aims to protect quantum information from the  influence of external factors such as environmental noise and imperfect control of quantum gates.

The basic idea behind dynamical decoupling is to apply a series of carefully chosen control pulses or gates at specific intervals during the evolution of a quantum system. These control pulses are designed to reverse or "decouple" the system from the undesired influences of noise and errors, effectively preserving the quantum state over time.
"""


import qiskit

def add_dynamical_decoupling(circuit, backend, dd_pulses=None, dd_pulses_count=None, dd_pulse_alignment=None):
    
    """
    Apply Dynamical Decoupling (DD) to a quantum circuit.

    Args:
        circuit (QuantumCircuit): The input quantum circuit to which DD will be applied.
        backend (Backend): The quantum device or simulator to which the circuit is targeted.
        dd_pulses (list of Gate, optional): The DD pulse gates to use. Default is a single XGate.
        dd_pulses_count (int, optional): The number of times to repeat the DD pulse sequence. Default is 2.
        dd_pulse_alignment (bool, optional): Whether to use pulse alignment for DD sequences. If not specified,
            it will attempt to use the backend's pulse alignment configuration.

    Returns:
        QuantumCircuit: The quantum circuit with Dynamical Decoupling applied.
    """
    
    DEFAULT_DD_PULSES = [qiskit.circuit.library.XGate()]
    DEFAULT_DD_PULSES_COUNT = 2
    
    # DD Sequence
    
    if dd_pulses is None:
        dd_pulses = DEFAULT_DD_PULSES
        
    if dd_pulses_count is None:
        dd_pulses_count = DEFAULT_DD_PULSES_COUNT
    
    dd_sequence = dd_pulses * dd_pulses_count
    
    
    # Pulse Alignment
    
    backend_pulse_alignment = None

    if (hasattr(backend, 'configuration') and
        hasattr(backend.configuration(), 'timing_constraints') and
        hasattr(backend.configuration().timing_constraints, 'pulse_alignment')):

        backend_pulse_alignment = backend.configuration().timing_constraints.get('pulse_alignment')
        
    run_pulse_alignment = dd_pulse_alignment or backend_pulse_alignment
    
    
    # Instruction Durations
    
    instruction_durations = qiskit.transpiler.InstructionDurations.from_backend(backend)
    
    
    # DD Pass Manager
        
    dd_pass_manager = qiskit.transpiler.PassManager([
        qiskit.transpiler.passes.ALAPScheduleAnalysis(instruction_durations),
        qiskit.transpiler.passes.PadDynamicalDecoupling(
            durations=instruction_durations,
            dd_sequence=dd_sequence, 
            pulse_alignment=run_pulse_alignment)])
    
    circuit_with_dd = dd_pass_manager.run(circuit)
        
    return circuit_with_dd