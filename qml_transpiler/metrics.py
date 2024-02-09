""" Functions for calculation of transpilation metrics. """

from qiskit.converters import dag_to_circuit

from qml_transpiler.transpiler import transpile

from qml_transpiler.functions import get_ibm_cost


def get_gates_counter(dag):

    """
    Counts the occurrences of gates based on their qubit count in a directed acyclic graph (DAG) of a quantum circuit.

    This function iterates through the operation nodes of a DAG, excluding directives like barriers, and counts
    how many times gates of different qubit counts occur. It returns a dictionary where keys are the qubit counts
    and values are the counts of gates operating on that many qubits.

    Parameters:
    - dag (DAGCircuit): The directed acyclic graph (DAG) representation of a quantum circuit.

    Returns:
    - dict: A dictionary with keys representing the number of qubits a gate acts on and values representing
      the count of such gates in the circuit. The dictionary is sorted by the number of qubits.

    Example:
    If the DAG has three 1-qubit gates and two 2-qubit gates, the function will return {1: 3, 2: 2}.
    """

    gates_counter = dict()

    for node in dag.op_nodes(include_directives=False):

        qubits_count = node.op.num_qubits

        if qubits_count in gates_counter:

            gates_counter[qubits_count] += 1

        else:

            gates_counter[qubits_count] = 1

    sorted_gates_counter = dict(sorted(gates_counter.items()))

    return sorted_gates_counter


def transpile_and_return_metrics(circuit, backend=None, **key_arguments):

    """
    Transpiles a given quantum circuit for a specified backend and collects metrics during the transpilation process.

    This function transpiles the input quantum circuit to be optimized for a given backend, if specified,
    and utilizes a callback function to collect metrics about each pass during the transpilation process.
    These metrics include pass index, pass name, pass type (Analysis or Transformation), execution time,
    circuit depth and width, IBM cost estimation, and a gates counter.

    Parameters:
    - circuit (QuantumCircuit): The quantum circuit to transpile.
    - backend (Backend, optional): The backend for which to optimize the transpilation. If None, a generic
      optimization is performed without specific backend optimization.
    - **key_arguments: Additional keyword arguments to be passed to the `transpile` function.

    Returns:
    - QuantumCircuit: The transpiled quantum circuit.
    - list: A list of dictionaries, with each dictionary containing metrics for a specific pass during the
      transpilation process. Each dictionary includes the following keys: 'pass_index', 'pass_name',
      'pass_type', 'time', 'depth', 'width', 'ibm_cost', and 'gates_counter'.

    The function internally defines a `pass_callback` closure that is invoked after each pass during
    transpilation, where it collects and appends the metrics for each pass to a list. The `transpile`
    function from Qiskit is then called with the provided arguments, along with the `callback` keyword
    argument set to the `pass_callback` function. Finally, the transpiled circuit and the list of collected
    metrics are returned.
    """

    metrics = list()

    # Pass Callback Closure

    def pass_callback(**parameters):

        """
        Callback function to collect metrics after each pass during transpilation.

        This function is internally defined and utilized as a callback during the transpilation process.
        It collects metrics such as pass name, execution time, circuit depth and width, and IBM cost
        estimation, among others, and appends them to an external list.

        Parameters:
        - **parameters: A dictionary of parameters provided by the transpiler after each pass. This includes
          the current pass object, execution time, the DAG after the pass, pass index, and a property set.
        """

        # Parameters

        pass_ = parameters.get('pass_')
        time = parameters.get('time')
        dag = parameters.get('dag')
        pass_index = parameters.get('count')
        # property_set = parameters.get('property_set')

        # Derivatives

        pass_name = pass_.name()

        depth = dag.depth()
        width = dag.width()

        gates_counter = get_gates_counter(dag)

        circuit = dag_to_circuit(dag)

        # Pass Type

        pass_type = ""

        if pass_.is_analysis_pass:
            pass_type = "Analysis"
        if pass_.is_transformation_pass:
            pass_type = "Transformation"

        # IBM Cost

        try:
            ibm_cost = get_ibm_cost(circuit)

        except ValueError:

            ibm_cost = 0

            # warning_message = (f"IBM Cost Calculation error at Pass: {pass_name}\n"
            #                    f"{error.args[0]}")

            # warnings.warn(warning_message, UserWarning)

        # Pass Metrics

        pass_metrics = {
            'pass_index': pass_index,
            'pass_name': pass_name,
            'pass_type': pass_type,
            'time': time,
            'depth': depth,
            'width': width,
            'ibm_cost': ibm_cost,
            'gates_counter': gates_counter
        }

        metrics.append(pass_metrics)

    key_arguments['callback'] = pass_callback

    # Transpile

    transpiled_circuit = transpile(circuit, backend, **key_arguments)

    return transpiled_circuit, metrics
