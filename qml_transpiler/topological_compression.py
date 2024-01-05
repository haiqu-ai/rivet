"""
Topological Compression selects topologically most important qubits of a backend
to produce limited coupling map - to decrease transpilation and simulation time.

We use flexible measure of node importance - that includes “closeness centrality”
for every node in backend topology graph.

Closeness centrality is efficiently calculated using “rustworkx” graph library function:

https://qiskit.org/ecosystem/rustworkx/dev/apiref/rustworkx.closeness_centrality.html

Flexible measure of node importance can be expanded with other metrics -
for example, neighbors counts or qubit noise levels.

Once importances are calculated - we traverse topology graph using A-star search -
starting from the most important node.

Traversed nodes are added to limited qubit list - which forms a connected subgraph.

Discovered subgraph can be used to limit backend topology - and save time
of further transpilation and simulation.
"""

import warnings

from qiskit.transpiler import CouplingMap

from rustworkx import closeness_centrality

from qml_transpiler.transpiler import transpile


def get_sorting_key(node):

    """
    Specify the sorting key for a node in a coupling graph.

    Args:
        node: A node of a coupling graph.

    Returns:
        importance: The importance value used for sorting the nodes.
    """

    node_index, importance = node

    return importance


def get_used_qubit_indices(circuit):

    """
    Retrieves the indices of the qubits used in the given quantum circuit.

    Parameters:
    - circuit (QuantumCircuit): The quantum circuit for which to determine the used qubit indices.

    Returns:
    list of int: The indices of the qubits used in the circuit.

    Example:
    >>> from qiskit import QuantumCircuit
    >>> circuit = QuantumCircuit(3)
    >>> circuit.h(0)
    >>> circuit.cx(0, 2)
    >>> used_qubit_indices = get_used_qubit_indices(circuit)
    >>> print(used_qubit_indices)
    [0, 2]
    """

    used_qubits = set()

    for instruction in circuit.data:
        for qubit in instruction.qubits:
            used_qubits.add(qubit)

    used_qubit_indices = [circuit.find_bit(qubit).index
                          for qubit in used_qubits]

    return used_qubit_indices


def get_limited_coupling_list(coupling_list, node_indices=None, max_nodes_count=None):

    """
    Retrieves a limited coupling list based on node importances and a maximum number of nodes.

    Parameters:
    - coupling_list (list of Iterables): A list of edges representing the coupling between nodes.
    - node_indices (list or None): Indices of nodes to consider. If None, all nodes are considered.
    - max_nodes_count (int or None): Maximum number of nodes to include in the limited coupling list.
                                     If None, the total number of nodes in the original coupling map is used.

    Returns:
    list of lists: A limited coupling list containing edges connected to the most important nodes.

    Note:
    The importance of a node is determined by its closeness centrality in the coupling map graph.

    Algorithm Overview:
    1. Construct a graph from the given coupling list.
    2. Calculate closeness centrality for each node in the graph.
    3. Select nodes based on importance and limit the graph to these nodes.
    4. Traverse the graph to select a specified number of nodes with the highest importance.
    5. Generate a limited coupling list based on the selected nodes.

    Example:
    >>> coupling_list = [(0, 1), (1, 2), (2, 3), (3, 0)]
    >>> limited_list = get_limited_coupling_list(coupling_list, max_nodes_count=3)
    >>> print(limited_list)
    [[0, 1], [1, 2], [2, 0]]
    """

    # Topology

    coupling_map = CouplingMap(couplinglist=coupling_list)

    graph = coupling_map.graph.copy()

    if max_nodes_count is None:

        max_nodes_count = coupling_map.size()

    if node_indices is None:

        node_indices = list(graph.node_indices())

    # Node Importances

    importances = closeness_centrality(graph)

    # Node Formation

    for node_index in node_indices:

        importance = importances[node_index]

        graph[node_index] = (node_index, importance)

    # Topology Limitation

    for node_index in graph.node_indices():

        if node_index not in node_indices:

            graph.remove_node(node_index)

    # Graph Traversal

    selected_nodes = []

    candidates = {max(graph.nodes(), key=get_sorting_key)}

    while len(selected_nodes) < max_nodes_count and candidates:

        new_node = max(candidates, key=get_sorting_key)

        candidates.remove(new_node)

        node_index, importance = new_node

        neighbours_indices = graph.neighbors(node_index)

        new_candidates = {graph[node_index] for node_index in neighbours_indices
                          if graph[node_index] not in selected_nodes}

        candidates.update(new_candidates)

        selected_nodes.append(new_node)

    # Selected Indices

    selected_indices, *_ = zip(*selected_nodes)

    limited_coupling_list = [list(edge) for edge in coupling_list
                             if all(index in selected_indices
                                    for index in edge)]

    return limited_coupling_list


def transpile_and_compress(circuit, backend, *arguments, **key_arguments):

    """
    Transpiles the input quantum circuit, compresses it by considering the coupling map of the backend,
    and returns the compressed circuit.

    Parameters:
    - circuit (QuantumCircuit): The input quantum circuit to be transpiled and compressed.
    - backend (BaseBackend): The backend to use for transpilation and the associated coupling map for compression.
    - *arguments: Additional positional arguments to pass to the transpile function.
    - **key_arguments: Additional keyword arguments to pass to the transpile function.

    Returns:
    QuantumCircuit: The transpiled and compressed quantum circuit.

    Note:
    The compression involves considering the coupling map of the provided backend and adding unused qubits
    to the coupling map to avoid error-prone situations. Ancillas are also added to the layout to ensure
    correct transpilation.
    """

    # First Transpilation

    transpiled_circuit = transpile(
        circuit,
        backend=backend,
        *arguments, **key_arguments)

    # Coupling List from Backend

    if backend is None:
        coupling_list = None
    else:
        coupling_list = backend.configuration().coupling_map

    # Coupling List from Key Arguments

    arguments_coupling_map = key_arguments.pop("coupling_map", None)

    if arguments_coupling_map is not None:
        coupling_list = [list(pair) for pair in arguments_coupling_map]

    # Coupling List Check

    if coupling_list is None:

        warnings.warn("Provided Backend has no topology - no compression performed")

        return transpiled_circuit

    # Node Indices

    node_indices = get_used_qubit_indices(transpiled_circuit)

    # Limited Coupling List

    limited_coupling_list = get_limited_coupling_list(
        coupling_list,
        node_indices=node_indices,
        max_nodes_count=circuit.num_qubits)

    # Add Ancillas to Coupling Map

    all_qubits = {qubit for pair in coupling_list for qubit in pair}

    used_qubits = {qubit for pair in limited_coupling_list for qubit in pair}

    unused_qubits = all_qubits - used_qubits

    unused_qubit_pairs = [[qubit, qubit] for qubit in unused_qubits]

    compressed_coupling_list = limited_coupling_list + unused_qubit_pairs

    # Second Transpilation

    compressed_circuit = transpile(
        circuit,
        backend=backend,
        coupling_map=compressed_coupling_list,
        *arguments, **key_arguments)

    # Add Ancillas to Layout

    layout = compressed_circuit.layout.final_layout

    for qubit_index, qubit in enumerate(compressed_circuit.qubits):

        if qubit_index not in layout:

            layout[qubit_index] = qubit

    return compressed_circuit
