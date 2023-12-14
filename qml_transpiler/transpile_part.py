"""Partial Transpilation."""

import qiskit

from qml_transpiler.transpiler import transpile
from qml_transpiler.transpiler import get_full_map


def invert_map(qubit_map):
    
    inverted_qubit_map = [qubit_map.index(index) for index, qubit in enumerate(qubit_map)]
    
    return inverted_qubit_map


def get_permutations(transpiled_circuit):
    
    initial_layout = transpiled_circuit.layout.initial_layout
    
    input_map = [initial_layout[qubit] for qubit in transpiled_circuit.qubits]

    output_map = get_full_map(transpiled_circuit)

    in_permutation_pattern = invert_map(input_map)
    out_permutation_pattern = invert_map(output_map)

    in_permutation = qiskit.circuit.library.Permutation(
        num_qubits=transpiled_circuit.num_qubits,
        pattern=in_permutation_pattern)
    
    out_permutation = qiskit.circuit.library.Permutation(
        num_qubits=transpiled_circuit.num_qubits,
        pattern=out_permutation_pattern).inverse()

    return in_permutation, out_permutation


def split_parametrized_circuit(circuit):
    
    dag = qiskit.converters.circuit_to_dag(circuit)
    
    # Parse Layers

    layer_dags = []
    parametrized_layer_flags = []

    for layer_index, layer in enumerate(dag.layers()):

        layer_dag = layer['graph']
        layer_dags.append(layer_dag)

        parametrized_layer_flag = False

        for node in layer_dag.op_nodes():

            if node.op.is_parameterized():
                parametrized_layer_flag = True

        parametrized_layer_flags.append(parametrized_layer_flag)
    
    # Parametrized Layers

    parametrized_layer_indices = [index for index, parametrized_layer_flag 
                                  in enumerate(parametrized_layer_flags)
                                  if parametrized_layer_flag is True]
    # If No Parametrized Gates

    if parametrized_layer_indices == []:

        parametrized_layer_indices = [len(parametrized_layer_flags)]
    
    # Layer DAGs

    first_index = min(parametrized_layer_indices)
    last_index = max(parametrized_layer_indices)
    
    left_layer_dags = layer_dags[:first_index]
    central_layer_dags = layer_dags[first_index:last_index + 1]
    right_layer_dags = layer_dags[last_index + 1:]

    # Compose DAGs

    left_dag = dag.copy_empty_like()
    central_dag = dag.copy_empty_like()
    right_dag = dag.copy_empty_like()

    for left_layer_dag in left_layer_dags:
        left_dag.compose(left_layer_dag)

    for central_layer_dag in central_layer_dags:
        central_dag.compose(central_layer_dag)

    for right_layer_dag in right_layer_dags:
        right_dag.compose(right_layer_dag)
        
    # Circuits Parts

    left_part = qiskit.converters.dag_to_circuit(left_dag)
    central_part = qiskit.converters.dag_to_circuit(central_dag)
    right_part = qiskit.converters.dag_to_circuit(right_dag)
    
    return left_part, central_part, right_part


def bind_and_transpile_part(circuit, parameters, backend=None, *arguments, **key_arguments):
    
    # Circuit Parts
    
    left_part, central_part, right_part = split_parametrized_circuit(circuit)
    
    bound_central_part = central_part.bind_parameters(parameters)
    
    transpiled_central_part = transpile(bound_central_part, backend, *arguments, **key_arguments)
    
    # display("transpiled_central_part:", transpiled_central_part.draw(idle_wires=False, fold=-1))
    
    # Permutations
    
    in_permutation, out_permutation = get_permutations(transpiled_central_part)
    
    transpiled_in_permutation = transpile(in_permutation, backend, layout_method="trivial")
    transpiled_out_permutation = transpile(out_permutation, backend, layout_method="trivial")

    # display("in_permutation:", in_permutation.draw(fold=-1))
    # display("out_permutation:", out_permutation.draw(fold=-1))
    
    # display("in_permutation.decompose():", in_permutation.decompose().draw(fold=-1))
    # display("out_permutation.decompose():", out_permutation.decompose().draw(fold=-1))
    
    # display("transpiled_in_permutation:", transpiled_in_permutation.draw(fold=-1))
    # display("transpiled_out_permutation:", transpiled_out_permutation.draw(fold=-1))
    
    # Resulting Circuit
    
    resulting_circuit = transpiled_central_part.copy()
    
    resulting_circuit.compose(transpiled_in_permutation, inplace=True, front=True)
    resulting_circuit.compose(left_part, inplace=True, front=True)
    resulting_circuit.compose(transpiled_out_permutation, inplace=True)
    resulting_circuit.compose(right_part, inplace=True)
    
    return resulting_circuit