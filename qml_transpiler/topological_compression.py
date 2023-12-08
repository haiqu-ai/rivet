"""
Topological Compression selects topologically most important qubits of a backend – to produce limited coupling map – to decrease transpilation and simulation time.

We use flexible measure of node importance – that includes “closeness centrality” for every node in backend topology graph.

Closeness centrality is efficiently calculated using “rustworkx” graph library function:

https://qiskit.org/ecosystem/rustworkx/dev/apiref/rustworkx.closeness_centrality.html

Flexible measure of node importance can be expanded with other metrics – for example, neighbors counts or qubit noise levels.
 
Once importances are calculated – we traverse topology graph using A-star search – starting from the most important node.

Traversed nodes are added to limited qubit list – which forms a connected subgraph.

Discovered subgraph can be used to limit backend topology – and save time of further transpilation and simulation.
"""

from rustworkx import closeness_centrality


def _get_sorting_key(node):
    
    """
    Specify the sorting key for a node in a coupling graph.

    Args:
        node: A node of a coupling graph.

    Returns:
        importance: The importance value used for sorting the nodes.
    """
    
    node_index, importance = node
    
    return importance


def _get_selected_coupling_list(coupling_map, selected_indices):
    
    """
    Get a selected coupling list based on a coupling map and selected indices.

    Args:
        coupling_map: A coupling map describing qubit connectivity.
        selected_indices: A list of node indices to select from.

    Returns:
        selected_coupling_list: A list of selected edges.
    """
    
    coupling_list = list(coupling_map)

    selected_coupling_list = [list(edge) for edge in coupling_list
                              if all(index in selected_indices
                                 for index in edge)]
    
    return selected_coupling_list
    
    

def get_limited_coupling_list(coupling_map, node_indices=None, max_nodes_count=None):
    
    """
    Get a limited coupling list based on a coupling map and specified node indices.

    Args:
        coupling_map: A coupling map describing qubit connectivity.
        node_indices: A list of node indices to consider. If not specified, all nodes are considered.
        max_nodes_count: The maximum number of nodes to include in the limited coupling list. If not specified,
                        it defaults to the total number of nodes in the coupling map.

    Returns:
        limited_coupling_list: A list of edges selected by importance and limited by the node indices and count.
    """
    
    # Initialization
    
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

    candidates = {max(graph.nodes(), key=_get_sorting_key)}

    while len(selected_nodes) < max_nodes_count and candidates:

        new_node = max(candidates, key=_get_sorting_key)

        candidates.remove(new_node)

        node_index, importance = new_node

        neighbours_indices = graph.neighbors(node_index)

        new_candidates = {graph[node_index] for node_index in neighbours_indices
                          if graph[node_index] not in selected_nodes}

        candidates.update(new_candidates)
        
        selected_nodes.append(new_node)
    
    
    # Selected Indices
        
    selected_indices, *_ = zip(*selected_nodes)
    
    limited_coupling_list = _get_selected_coupling_list(
        coupling_map, selected_indices
    )
    
    return limited_coupling_list