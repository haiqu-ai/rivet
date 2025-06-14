"""Circuit packing module for Rivet Transpiler."""

import numpy as np
import qiskit
from qiskit.transpiler import Target, CouplingMap
from typing import Dict, List, Tuple, Optional, Set
import networkx as nx
import warnings
from collections import defaultdict


def pack_circuits(circuit: qiskit.QuantumCircuit, 
                  num_copies: int, 
                  target: Target) -> Tuple[qiskit.QuantumCircuit, Dict]:
    """
    Pack multiple copies of a circuit onto a single device.
    
    Args:
        circuit: The quantum circuit to replicate
        num_copies: Number of circuit copies to pack
        target: Target device with topology and error information
        
    Returns:
        Tuple containing:
            - Packed quantum circuit ready for execution
            - Mapping dictionary showing physical to logical qubit correspondence
    """
    if num_copies <= 0:
        raise ValueError("Number of copies must be positive")
    
    if circuit.num_clbits > 0:
        raise ValueError("Input circuit should not have classical bits - measurements will be added")
    
    if target is None:
        num_qubits = max(50, circuit.num_qubits * num_copies + 10)
        coupling_edges = [(i, j) for i in range(num_qubits) for j in range(i+1, num_qubits)]
        coupling_map = CouplingMap(coupling_edges)
    else:
        coupling_map = target.build_coupling_map()
    
    G = nx.Graph()
    if coupling_map:
        G.add_edges_from(coupling_map.get_edges())
    else:
        num_qubits = circuit.num_qubits * num_copies + 5
        G.add_edges_from([(i, i+1) for i in range(num_qubits-1)])
    
    error_rates = {}
    if target:
        try:
            for gate_name in ['cx', 'cz']:
                if target.operation_names and gate_name in target.operation_names:
                    for qargs in target.qargs:
                        if len(qargs) == 2:
                            try:
                                props = target.instruction_properties(gate_name, qargs)
                                if props and hasattr(props, 'error') and props.error is not None:
                                    error_rates[qargs] = props.error
                            except:
                                continue
        except (AttributeError, KeyError):
            pass
    
    subgraphs = _find_optimal_subgraphs(G, circuit.num_qubits, num_copies, error_rates)
    
    total_qubits = max(max(sg) for sg in subgraphs) + 1 if subgraphs else circuit.num_qubits * num_copies
    total_clbits = circuit.num_qubits * num_copies
    
    packed_circuit = qiskit.QuantumCircuit(total_qubits, total_clbits)
    
    qubits_map = {}
    
    for copy_idx, subgraph_qubits in enumerate(subgraphs):
        logical_to_physical = {i: q for i, q in enumerate(subgraph_qubits)}
        qubits_map[copy_idx] = logical_to_physical
        
        circuit_copy = circuit.copy()
        
        packed_circuit.compose(
            circuit_copy, 
            qubits=subgraph_qubits,
            inplace=True
        )
        
        clbit_offset = copy_idx * circuit.num_qubits
        for logical_qubit, physical_qubit in logical_to_physical.items():
            packed_circuit.measure(physical_qubit, clbit_offset + logical_qubit)
    
    # Add Layout2qDistance analysis if target is provided
    if target:
        from qiskit.transpiler.passes import Layout2qDistance
        layout_analyzer = Layout2qDistance(target)
        
        for copy_idx, subgraph_qubits in enumerate(subgraphs):
            logical_to_physical = {i: q for i, q in enumerate(subgraph_qubits)}
            layout_score = layout_analyzer.run(logical_to_physical)
            
            # Warn if layout score is too high (indicating poor mapping)
            if layout_score > 2.0:  
                warnings.warn(
                    f"High layout distance ({layout_score:.2f}) for copy {copy_idx}. "
                    "This may indicate suboptimal qubit placement."
                )
    
    # Transpile to native gates if target is provided
    if target:
        from qiskit.transpiler.passes import BasisTranslator
        from qiskit.transpiler.passes import Unroller
        from qiskit.transpiler import PassManager
        
        basis_gates = target.operation_names
        
        pm = PassManager([
            Unroller(basis_gates),
            BasisTranslator(target)
        ])
        
        packed_circuit = pm.run(packed_circuit)
    
    return packed_circuit, qubits_map


def _find_optimal_subgraphs(G: nx.Graph, 
                           subgraph_size: int, 
                           num_subgraphs: int,
                           error_rates: Dict = None) -> List[List[int]]:
    """
    Find optimal disjoint subgraphs in the device graph.
    
    Args:
        G: Device connectivity graph
        subgraph_size: Number of qubits needed per circuit
        num_subgraphs: Number of subgraphs to find
        error_rates: Dictionary of error rates for edges
        
    Returns:
        List of lists, where each inner list contains the qubits for one subgraph
    """
    if G.number_of_nodes() < subgraph_size * num_subgraphs:
        raise ValueError(f"Device has {G.number_of_nodes()} qubits, but {subgraph_size * num_subgraphs} are needed")
    
    def calculate_crosstalk_score(node, used_nodes):
        """Calculate crosstalk score for a node based on its proximity to used nodes."""
        score = 0
        for used_node in used_nodes:
            # Direct connections (1-hop) have highest crosstalk
            if G.has_edge(node, used_node):
                score -= 10
            # 2-hop connections have moderate crosstalk
            for neighbor in G.neighbors(used_node):
                if G.has_edge(node, neighbor):
                    score -= 5
        return score
    
    def calculate_node_score(node, used_nodes, error_rates):
        """Calculate overall score for a node considering connectivity, errors, and crosstalk."""
        connectivity_score = len(list(G.neighbors(node)))
        
        # Error score from error rates
        error_score = 0
        if error_rates:
            for neighbor in G.neighbors(node):
                edge_key1 = (node, neighbor)
                edge_key2 = (neighbor, node)
                edge_key = edge_key1 if edge_key1 in error_rates else edge_key2
                if edge_key in error_rates:
                    error_score += error_rates[edge_key]
        
        # Crosstalk score
        crosstalk_score = calculate_crosstalk_score(node, used_nodes)
        
        # Combine scores with weights
        return (connectivity_score * 2 -  # Weight connectivity more heavily
                (error_score * 10 if error_rates else 0) +  # Error rates are critical
                crosstalk_score)  # Crosstalk penalty
    
    node_scores = {}
    used_nodes = set()
    
    # Calculate initial scores for all nodes
    for node in G.nodes():
        node_scores[node] = calculate_node_score(node, used_nodes, error_rates)
    
    subgraphs = []
    
    for _ in range(num_subgraphs):
        # Find best starting node
        start_node = max(node_scores.keys(), key=lambda n: node_scores[n])
        if start_node in used_nodes:
            raise ValueError("Not enough nodes available for all subgraphs")
            
        subgraph = [start_node]
        used_nodes.add(start_node)
        
        # Update scores for remaining nodes
        for node in G.nodes():
            if node not in used_nodes:
                node_scores[node] = calculate_node_score(node, used_nodes, error_rates)
        
        # Grow subgraph
        while len(subgraph) < subgraph_size:
            best_node = None
            best_score = float('-inf')
            
            # First try to find connected nodes
            for node in subgraph:
                for neighbor in G.neighbors(node):
                    if neighbor not in used_nodes and neighbor not in subgraph:
                        score = node_scores[neighbor]
                        if score > best_score:
                            best_score = score
                            best_node = neighbor
            
            # If no connected nodes found, take best available node
            if best_node is None:
                for node in G.nodes():
                    if node not in used_nodes and node not in subgraph:
                        score = node_scores[node]
                        if score > best_score:
                            best_score = score
                            best_node = node
            
            if best_node is None:
                raise ValueError(f"Could not find enough qubits for subgraph {len(subgraphs)+1}")
            
            subgraph.append(best_node)
            used_nodes.add(best_node)
            
            # Update scores for remaining nodes
            for node in G.nodes():
                if node not in used_nodes:
                    node_scores[node] = calculate_node_score(node, used_nodes, error_rates)
        
        subgraphs.append(subgraph)
    
    return subgraphs


def unpack_results(counts: Dict, 
                  num_copies: int, 
                  qubits_map: Dict) -> Dict[int, Dict]:
    """
    Unpack results from a packed circuit execution.
    
    Args:
        counts: Dictionary of bitstring results from executing the packed circuit
        num_copies: Number of original circuits packed
        qubits_map: Dictionary mapping physical qubits to logical qubits
        
    Returns:
        Dictionary of unpacked results, with one entry per circuit copy
    """
    if not counts:
        return {i: {} for i in range(num_copies)}
    
    if not qubits_map or 0 not in qubits_map:
        raise ValueError("Invalid qubits_map provided")
    
    unpacked_results = {i: defaultdict(int) for i in range(num_copies)}
    
    qubits_per_copy = len(qubits_map[0])
    
    for bitstring, count in counts.items():
        for copy_idx in range(num_copies):
            if copy_idx not in qubits_map:
                continue
                
            logical_to_physical = qubits_map[copy_idx]
            
            # Classical bits are ordered as: copy0_qubit0, copy0_qubit1, ..., copy1_qubit0, copy1_qubit1, ...
            start_bit = copy_idx * qubits_per_copy
            end_bit = start_bit + qubits_per_copy
            
            if end_bit <= len(bitstring):
                copy_bitstring = bitstring[start_bit:end_bit]
                unpacked_results[copy_idx][copy_bitstring] += count
    
    return {copy_idx: dict(results) for copy_idx, results in unpacked_results.items()}


def analyze_packing_efficiency(original_circuit: qiskit.QuantumCircuit, 
                             packed_circuit: qiskit.QuantumCircuit,
                             num_copies: int,
                             target: Target = None) -> Dict:
    """
    Analyze the efficiency of circuit packing.
    
    Args:
        original_circuit: Original single circuit
        packed_circuit: Packed circuit with multiple copies
        num_copies: Number of copies packed
        target: Target device information
        
    Returns:
        Dictionary with efficiency metrics
    """
    metrics = {
        'qubit_utilization': packed_circuit.num_qubits / (target.num_qubits if target else 100),
        'packing_ratio': num_copies,
        'original_qubits': original_circuit.num_qubits,
        'packed_qubits': packed_circuit.num_qubits,
        'qubit_efficiency': (original_circuit.num_qubits * num_copies) / packed_circuit.num_qubits,
        'depth_original': original_circuit.depth(),
        'depth_packed': packed_circuit.depth(),
        'gate_count_original': len(original_circuit.data),
        'gate_count_packed': len(packed_circuit.data),
        'theoretical_speedup': num_copies,
    }
    
    total_separate_qubits = original_circuit.num_qubits * num_copies
    actual_qubits = packed_circuit.num_qubits
    metrics['space_savings'] = 1.0 - (actual_qubits / total_separate_qubits) if total_separate_qubits > 0 else 0
    
    return metrics


# Integration with existing Rivet functionality
def pack_and_transpile_chain(circuits: List[qiskit.QuantumCircuit], 
                           num_copies: int,
                           target: Target,
                           **transpile_kwargs) -> Tuple[qiskit.QuantumCircuit, List[Dict]]:
    """
    Pack multiple different circuits and transpile them as a chain.
    
    Args:
        circuits: List of circuits to pack
        num_copies: Number of copies per circuit
        target: Target device
        **transpile_kwargs: Additional transpilation arguments
        
    Returns:
        Tuple of (final_packed_circuit, list_of_qubits_maps)
    """
    packed_circuits = []
    all_qubits_maps = []
    
    for circuit in circuits:
        packed, qubits_map = pack_circuits(circuit, num_copies, target)
        packed_circuits.append(packed)
        all_qubits_maps.append(qubits_map)
    
    # Use Rivet's transpile_chain for optimal stitching
    from rivet_transpiler.transpiler import transpile_chain
    
    final_circuit = transpile_chain(
        packed_circuits,
        backend=None,
        **transpile_kwargs
    )
    
    return final_circuit, all_qubits_maps