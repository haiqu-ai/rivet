""" Transpile functions. """

import qiskit

import functools

from qml_transpiler.stacks import get_stack_pass_manager


# 1) Transpile

@functools.wraps(qiskit.transpile)
def transpile(*arguments, **key_arguments):
    
    """
    Transpile a quantum circuit with optional stack-specific optimizations.

    Args:
        *arguments: Positional arguments for qiskit.transpile.
        **key_arguments: Keyword arguments for qiskit.transpile.

    Returns:
        QuantumCircuit: The transpiled quantum circuit.
    """

    transpiled_circuit, transpiler_options = transpile_and_return_options(*arguments, **key_arguments)
    
    return transpiled_circuit


# 2) Transpile and Return Options

def transpile_and_return_options(circuit, backend=None, *arguments, **key_arguments):
    
    """
    Transpile a quantum circuit and return transpiler options.

    Args:
        circuit (QuantumCircuit): The input quantum circuit.
        backend: The target backend for transpilation.
        *arguments: Positional arguments for qiskit.transpile.
        **key_arguments: Keyword arguments for qiskit.transpile.

    Returns:
        QuantumCircuit: The transpiled quantum circuit.
        dict: A dictionary containing transpiler options:
              - full map,
              - original circuit,
              - transpile arguments.
    """
    
    # Options
    
    transpiler_options = key_arguments.get('transpiler_options', dict())
    
    options_backend = transpiler_options.get('backend')
    options_arguments = transpiler_options.get('arguments', ())

    
    # Arguments
    
    run_backend = backend or options_backend
    
    run_arguments = arguments or options_arguments
    
    run_key_arguments = {**transpiler_options, **key_arguments}
    
    run_key_arguments['backend'] = run_backend
    
    
    # Dynamical Decoupling Arguments
    
    dd_pulses = run_key_arguments.pop('dd_pulses', None)
    dd_pulses_count = run_key_arguments.pop('dd_pulses_count', None)
    dd_pulse_alignment = run_key_arguments.pop('dd_pulse_alignment', None)
    dynamical_decoupling = run_key_arguments.pop('dynamical_decoupling', None)

    
    # Stack
    
    stack_pass_manager = None
    
    arguments_stack = key_arguments.get('stack')    
    options_stack = transpiler_options.get('stack')
    
    stack = arguments_stack or options_stack
    
    if stack is not None:
        
        stack_pass_manager = get_stack_pass_manager(**run_key_arguments)
        
        
    # Pass Manager
    
    arguments_pass_manager = key_arguments.get('pass_manager')
    options_pass_manager = transpiler_options.get('pass_manager')
    
    pass_manager = arguments_pass_manager or options_pass_manager or stack_pass_manager
    
    
    # Transpile
    
    if pass_manager is None:
        
        transpiled_circuit = qiskit.transpile(circuit, *run_arguments, **run_key_arguments)
        
    else:
        transpiled_circuit = pass_manager.run(circuit)
        
        
    # Dynamical Decoupling
    
    if dynamical_decoupling is True:
        
        transpiled_circuit = add_dynamical_decoupling(transpiled_circuit, run_backend,
                                                      dd_pulses, dd_pulses_count, dd_pulse_alignment)

    # Transpiler Options
    
    options = run_key_arguments.copy()
    
    full_map = get_full_map(transpiled_circuit)
    
    options['full_map'] = full_map
    options['arguments'] = run_arguments
    options['original_circuit'] = circuit

    return transpiled_circuit, options


# 3) Transpile Chain

def transpile_chain(circuits, backend=None, *arguments, **key_arguments):
    
    """
    Transpile a chain of quantum circuits one-by-one.

    Args:
        circuits (list of QuantumCircuit): List of input quantum circuits.
        backend: The target backend for transpilation.
        *arguments: Positional arguments for qiskit.transpile.
        **key_arguments: Keyword arguments for qiskit.transpile.

    Returns:
        QuantumCircuit: The transpiled chain circuit.
    """
    
    full_map = None
    chain_circuit = None
    
    # Chain
    
    for circuit in circuits:
        
        if full_map is not None:
        
            initial_layout = full_map[:circuit.num_qubits]

            key_arguments['initial_layout'] = initial_layout
        
        transpiled_circuit, transpiler_options = transpile_and_return_options(
            circuit,
            backend,
            *arguments, **key_arguments)
        
        if chain_circuit is None:
            chain_circuit = transpiled_circuit
            
        else:
            chain_circuit.compose(transpiled_circuit, inplace=True)
        
        full_map = transpiler_options['full_map']
        
    return chain_circuit


# 4) Transpile Right

def transpile_right(central_circuit, right_circuit,
                    backend=None, *arguments, **key_arguments):
    
    """
    Transpile a right quantum circuit and combine it with already transpiled central circuit.

    Args:
        central_circuit (QuantumCircuit): The central quantum circuit.
        right_circuit (QuantumCircuit): The right quantum circuit to transpile and add.
        backend: The target backend for transpilation.
        *arguments: Positional arguments for qiskit.transpile.
        **key_arguments: Keyword arguments for qiskit.transpile.

    Returns:
        QuantumCircuit: The resulting quantum circuit.
    """
    
    # Transpile and Compose
    
    full_map = get_full_map(central_circuit)

    key_arguments['initial_layout'] = full_map[:right_circuit.num_qubits]
    
    transpiled_right_circuit, transpiler_options = transpile_and_return_options(
        right_circuit,
        backend,
        *arguments, **key_arguments
    )
    
    resulting_circuit = central_circuit.compose(transpiled_right_circuit)
    
    
    # No Layout
    
    if transpiled_right_circuit.layout is None:
        
        return resulting_circuit
    
    if central_circuit.layout is None:
        
        resulting_circuit._layout = transpiled_right_circuit.layout
        
        return resulting_circuit
    
    
    # Central Routing
    
    if central_circuit.layout.final_layout is None:
    
        central_routing = list(range(central_circuit.num_qubits))
        
    else:        
        central_routing = [central_circuit.layout.final_layout[qubit]
                           for qubit in central_circuit.qubits]
    
    # Right Routing
    
    if transpiled_right_circuit.layout.final_layout is None:  

        right_routing = central_routing.copy()
    
    else:   
        right_routing = [transpiled_right_circuit.layout.final_layout[qubit] 
                         for qubit in transpiled_right_circuit.qubits]
        
    # Final Routing
    
    final_routing = [right_routing[qubit] for qubit in central_routing]   
    
    
    # Layouts
    
    final_layout = qiskit.transpiler.Layout.from_intlist(final_routing, *resulting_circuit.qregs)
    
    transpile_layout = qiskit.transpiler.TranspileLayout(
        input_qubit_mapping=central_circuit.layout.input_qubit_mapping,
        initial_layout=central_circuit.layout.initial_layout,
        final_layout=final_layout
    )

    resulting_circuit._layout = transpile_layout
    
    # Printouts
    
    # print("central_routing:", central_routing)
    # print("right_routing:", right_routing)
    # print("final_routing:", final_routing)
    # print("final_layout:", final_layout)
    
    return resulting_circuit


# 5) Transpile Left

def transpile_left(central_circuit, left_circuit,
                   backend=None, *arguments, **key_arguments):
    
    """
    Transpile a left quantum circuit and combine it with already transpiled central circuit.

    Args:
        central_circuit (QuantumCircuit): The central quantum circuit.
        left_circuit (QuantumCircuit): The left quantum circuit to transpile and add.
        backend: The target backend for transpilation.
        *arguments: Positional arguments for qiskit.transpile.
        **key_arguments: Keyword arguments for qiskit.transpile.

    Returns:
        QuantumCircuit: The resulting quantum circuit.
    """
    
    # Left Initial Layout
    
    if central_circuit.layout is None:
        
        left_initial_layout = list(range(left_circuit.num_qubits))
        
    else:
    
        initial_layout = central_circuit.layout.initial_layout
        input_qubit_mapping = central_circuit.layout.input_qubit_mapping

        initial_map = [initial_layout[qubit] for qubit in input_qubit_mapping]
        
        left_initial_layout = initial_map[:left_circuit.num_qubits]
        
    
    # Transpile and Compose
    
    key_arguments['initial_layout'] = left_initial_layout
    
    inverted_left_circuit = left_circuit.inverse()
    
    transpiled_inverted_left_circuit, transpiler_options = transpile_and_return_options(
        inverted_left_circuit,
        backend,
        *arguments, **key_arguments
    )
    
    transpiled_left_circuit = transpiled_inverted_left_circuit.inverse()
    
    transpiled_left_circuit._layout = transpiled_inverted_left_circuit.layout

    resulting_circuit = central_circuit.compose(transpiled_left_circuit,
                                                front=True)
    
    # No Layout
    
    if transpiled_left_circuit.layout is None:
        
        return resulting_circuit
    
    
    # Left Routing
    
    if transpiled_left_circuit.layout.final_layout is None:
    
        left_routing = list(range(transpiled_left_circuit.num_qubits))

    else:        
        left_routing = [transpiled_left_circuit.layout.final_layout[qubit]
                        for qubit in transpiled_left_circuit.qubits]
    
    # Central Routing
    
    if (central_circuit.layout is None or
        central_circuit.layout.final_layout is None):
        
        central_routing = left_routing.copy()
    
    else:
        central_routing = [central_circuit.layout.final_layout[qubit] 
                           for qubit in central_circuit.qubits]
        
    # Final Routing
    
    final_routing = [central_routing[qubit] for qubit in left_routing]   
    
    # Final Layout
    
    final_layout = qiskit.transpiler.Layout.from_intlist(final_routing, *resulting_circuit.qregs)
    
    
    # Initial Layout
    
    input_qubit_mapping = transpiled_left_circuit.layout.input_qubit_mapping
    
    initial_map = get_full_map(transpiled_left_circuit)

    initial_layout = transpiled_left_circuit.layout.initial_layout.copy()

    for virtual, physical in zip(input_qubit_mapping, initial_map):

        initial_layout[virtual] = physical


    # Transpile Layout
    
    transpile_layout = qiskit.transpiler.TranspileLayout(
        input_qubit_mapping=input_qubit_mapping,
        initial_layout=initial_layout,
        final_layout=final_layout
    )

    resulting_circuit._layout = transpile_layout
    
    # Printouts
    
    # print("left_routing:", left_routing)
    # print("central_routing:", central_routing)
    # print("final_routing:", final_routing)
    # print("final_layout:", final_layout)
    
    return resulting_circuit


# 6) Get Full Map

def get_full_map(transpiled_circuit, verbose=False):
    
    """
    Get the final allocation of virtual qubits in a transpiled quantum circuit.

    Args:
        transpiled_circuit (QuantumCircuit): The transpiled quantum circuit.
        verbose (bool): Whether to print the full map calculation stages.

    Returns:
        list: The full map of qubits.
    """
    
    # No Layout
    
    if transpiled_circuit.layout is None:
        
        full_map = list(range(transpiled_circuit.num_qubits))
        
        return full_map
    
    # Zero Map
    
    input_qubit_mapping = transpiled_circuit.layout.input_qubit_mapping
    initial_layout = transpiled_circuit.layout.initial_layout
    final_layout = transpiled_circuit.layout.final_layout
 
    zero_map = dict(zip(input_qubit_mapping,
                        transpiled_circuit.qubits))

    # After Layout Map

    after_layout_map = [()] * transpiled_circuit.num_qubits
    
    for physical, in_virtual in initial_layout.get_physical_bits().items():

        out_virtual = zero_map[in_virtual]

        after_layout_map[physical] = (in_virtual, out_virtual)
    
    
    # After Routing Map
    
    after_routing_map = after_layout_map.copy()
    
    if final_layout is not None:
        
        for from_row, qubit in enumerate(transpiled_circuit.qubits):
            
            to_row = final_layout[qubit]
            
            from_in, from_out = after_layout_map[from_row]
            to_in, to_out = after_layout_map[to_row]
            
            after_routing_map[to_row] = (to_in, from_out)
            
    # Full Map
    
    full_map = []
    
    for out_qubit in transpiled_circuit.qubits:
    
        for physical, virtuals in enumerate(after_routing_map):
            
            in_virtual, out_virtual = virtuals

            if out_virtual is out_qubit:

                full_map.append(physical)
                
    # Printout
    
    if verbose is True:
        
        print("zero_map:", zero_map)
        print("after_layout_map:", after_layout_map)
        print("after_routing_map:", after_routing_map)
        print("full_map:", full_map)
        print("transpiled_circuit.layout:", transpiled_circuit.layout)

    return full_map