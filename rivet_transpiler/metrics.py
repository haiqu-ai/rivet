""" Functions for calculation of transpilation metrics. """

from collections import Counter

from qiskit.converters import dag_to_circuit

from rivet_transpiler.transpiler import transpile

from rivet_transpiler.functions import get_ibm_cost


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

    # Update Metrics Callback Closure

    def update_metrics_callback(**parameters):
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

        pass_ = parameters.get("pass_")
        time = parameters.get("time")
        dag = parameters.get("dag")
        pass_index = parameters.get("count")
        # property_set = parameters.get('property_set')

        # Derivatives

        pass_name = pass_.name()

        depth = dag.depth()
        width = dag.width()

        circuit = dag_to_circuit(dag)

        # Gates Counter

        dag_nodes = dag.op_nodes(include_directives=False)

        qubit_counts = sorted(node.op.num_qubits for node in dag_nodes)

        gates_counter = dict(Counter(qubit_counts))

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
            "pass_index": pass_index,
            "pass_name": pass_name,
            "pass_type": pass_type,
            "time": time,
            "depth": depth,
            "width": width,
            "ibm_cost": ibm_cost,
            "gates_counter": gates_counter,
        }

        metrics.append(pass_metrics)

    # Arguments Callback

    arguments_callback = key_arguments.get("callback", None)

    if arguments_callback is None:

        key_arguments["callback"] = update_metrics_callback

    else:

        def composite_callback(**parameters):

            arguments_callback(**parameters)
            update_metrics_callback(**parameters)

        key_arguments["callback"] = composite_callback

    # Transpile

    transpiled_circuit = transpile(circuit, backend, **key_arguments)

    return transpiled_circuit, metrics
