"""
QED-C Benchmark Integration for Circuit Packing

This example shows how to evaluate circuit packing performance using
standardized quantum application benchmarks from the QED-C suite.
"""

import numpy as np
import matplotlib.pyplot as plt
from time import time
from collections import defaultdict
import json

from qiskit import QuantumCircuit
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeMontrealV2, FakeManhattanV2

from rivet_transpiler.circuit_packing import (
    pack_circuits, unpack_results, analyze_packing_efficiency
)


class SimpleBenchmarkCircuits:
    """
    Simple benchmark circuits for demonstration.
    These simulate the structure of QED-C benchmarks.
    """
    
    @staticmethod
    def bernstein_vazirani(num_qubits: int, secret_string: str = None):
        """Create a Bernstein-Vazirani circuit."""
        if secret_string is None:
            secret_string = '1' * (num_qubits - 1)
        
        circuit = QuantumCircuit(num_qubits)
        
        circuit.x(num_qubits - 1)
        
        for i in range(num_qubits):
            circuit.h(i)
            
        for i, bit in enumerate(secret_string):
            if bit == '1':
                circuit.cx(i, num_qubits - 1)
        
        for i in range(num_qubits - 1):
            circuit.h(i)
        
        return circuit
    
    @staticmethod
    def deutsch_jozsa(num_qubits: int, balanced: bool = True):
        """Create a Deutsch-Jozsa circuit."""
        circuit = QuantumCircuit(num_qubits)
        
        circuit.x(num_qubits - 1)
        
        for i in range(num_qubits):
            circuit.h(i)
        
        if balanced:
            for i in range(num_qubits // 2):
                circuit.cx(i, num_qubits - 1)
        
        for i in range(num_qubits - 1):
            circuit.h(i)
        
        return circuit
    
    @staticmethod
    def quantum_fourier_transform(num_qubits: int):
        """Create a QFT circuit."""
        circuit = QuantumCircuit(num_qubits)
        
        for i in range(num_qubits):
            circuit.h(i)
            for j in range(i + 1, num_qubits):
                circuit.cp(np.pi / 2**(j - i), i, j)
        
        for i in range(num_qubits // 2):
            circuit.swap(i, num_qubits - 1 - i)
        
        return circuit
    
    @staticmethod
    def grovers_search(num_qubits: int, marked_item: int = 0):
        """Create a simplified Grover's search circuit."""
        circuit = QuantumCircuit(num_qubits)
        
        for i in range(num_qubits):
            circuit.h(i)
        
        if marked_item > 0:
            binary_rep = format(marked_item, f'0{num_qubits}b')
            for i, bit in enumerate(binary_rep):
                if bit == '0':
                    circuit.x(i)
            
            if num_qubits == 2:
                circuit.cz(0, 1)
            elif num_qubits == 3:
                circuit.ccx(0, 1, 2)
                circuit.z(2)
                circuit.ccx(0, 1, 2)
            
            for i, bit in enumerate(binary_rep):
                if bit == '0':
                    circuit.x(i)
        
        for i in range(num_qubits):
            circuit.h(i)
            circuit.x(i)
        
        if num_qubits == 2:
            circuit.cz(0, 1)
        elif num_qubits == 3:
            circuit.ccx(0, 1, 2)
            circuit.z(2)
            circuit.ccx(0, 1, 2)
        
        for i in range(num_qubits):
            circuit.x(i)
            circuit.h(i)
        
        return circuit


def calculate_fidelity(ideal_counts, actual_counts):
    """Calculate fidelity between ideal and actual measurement results."""
    if not ideal_counts or not actual_counts:
        return 0.0
    
    # Normalize to probabilities
    ideal_total = sum(ideal_counts.values())
    actual_total = sum(actual_counts.values())
    
    if ideal_total == 0 or actual_total == 0:
        return 0.0
    
    ideal_probs = {k: v/ideal_total for k, v in ideal_counts.items()}
    actual_probs = {k: v/actual_total for k, v in actual_counts.items()}
    
    # Calculate fidelity using overlap
    all_states = set(ideal_probs.keys()) | set(actual_probs.keys())
    fidelity = 0.0
    for state in all_states:
        p_ideal = ideal_probs.get(state, 0)
        p_actual = actual_probs.get(state, 0)
        fidelity += np.sqrt(p_ideal * p_actual)
    
    return fidelity**2


def run_benchmark_suite():
    """Run comprehensive benchmark suite with circuit packing."""
    
    # Setup
    backend = AerSimulator()
    targets = {
        'Montreal': FakeMontrealV2().target,
        'Manhattan': FakeManhattanV2().target
    }
    
    # Benchmark configurations
    benchmarks = {
        'Bernstein-Vazirani': SimpleBenchmarkCircuits.bernstein_vazirani,
        'Deutsch-Jozsa': SimpleBenchmarkCircuits.deutsch_jozsa,
        'QFT': SimpleBenchmarkCircuits.quantum_fourier_transform,
        'Grovers': SimpleBenchmarkCircuits.grovers_search
    }
    
    qubit_ranges = {
        'Bernstein-Vazirani': range(3, 8),
        'Deutsch-Jozsa': range(3, 8),
        'QFT': range(3, 6),
        'Grovers': range(3, 6)
    }
    
    copy_counts = [2, 4, 6, 8]
    shots = 1000
    
    # Results storage
    results = defaultdict(dict)
    
    print("Starting QED-C Style Circuit Packing Benchmark")
    print("=" * 60)
    
    for benchmark_name, benchmark_func in benchmarks.items():
        print(f"\n Benchmarking: {benchmark_name}")
        
        for num_qubits in qubit_ranges[benchmark_name]:
            print(f" Testing {num_qubits} qubits...")
            
            if benchmark_name == 'Grovers':
                circuit = benchmark_func(num_qubits, marked_item=1)
            else:
                circuit = benchmark_func(num_qubits)
            
            for target_name, target in targets.items():
                print(f"    Target: {target_name}")
                
                for num_copies in copy_counts:
                    key = f"{benchmark_name}_{num_qubits}q_{target_name}_{num_copies}copies"
                    
                    try:
                        # Traditional approach
                        start_time = time()
                        traditional_results = []
                        
                        for _ in range(num_copies):
                            circuit_with_measure = circuit.copy()
                            circuit_with_measure.measure_all()
                            
                            job = backend.run(circuit_with_measure, shots=shots)
                            counts = job.result().get_counts()
                            traditional_results.append(counts)
                        
                        traditional_time = time() - start_time
                        
                        # Packed approach
                        start_time = time()
                        
                        packed_circuit, qubits_map = pack_circuits(circuit, num_copies, target)
                        
                        job = backend.run(packed_circuit, shots=shots)
                        packed_counts = job.result().get_counts()
                        
                        unpacked_results = unpack_results(packed_counts, num_copies, qubits_map)
                        packed_results = [unpacked_results[i] for i in range(num_copies)]
                        
                        packed_time = time() - start_time
                        
                        # Calculate metrics
                        speedup = traditional_time / packed_time if packed_time > 0 else float('inf')
                        
                        # Calculate fidelities
                        fidelities = []
                        for i in range(num_copies):
                            fidelity = calculate_fidelity(traditional_results[i], packed_results[i])
                            fidelities.append(fidelity)
                        
                        avg_fidelity = np.mean(fidelities)
                        
                        # Efficiency metrics
                        efficiency = analyze_packing_efficiency(circuit, packed_circuit, num_copies, target)
                        
                        # Store results
                        results[key] = {
                            'benchmark': benchmark_name,
                            'num_qubits': num_qubits,
                            'target': target_name,
                            'num_copies': num_copies,
                            'traditional_time': traditional_time,
                            'packed_time': packed_time,
                            'speedup': speedup,
                            'fidelities': fidelities,
                            'avg_fidelity': avg_fidelity,
                            'efficiency': efficiency
                        }
                        
                        print(f"      ✓ {num_copies} copies: {speedup:.2f}x speedup, {avg_fidelity:.3f} fidelity")
                        
                    except Exception as e:
                        print(f"      {num_copies} copies: Error - {e}")
                        results[key] = {'error': str(e)}
    
    return dict(results)


def visualize_results(results):
    """Create comprehensive visualizations of benchmark results."""
    
    # Filter successful results
    successful_results = {k: v for k, v in results.items() if 'error' not in v}
    
    if not successful_results:
        print("No successful results to visualize")
        return
    
    # Prepare data
    speedups = []
    fidelities = []
    benchmarks = []
    copy_counts = []
    
    for key, result in successful_results.items():
        speedups.append(result['speedup'])
        fidelities.append(result['avg_fidelity'])
        benchmarks.append(result['benchmark'])
        copy_counts.append(result['num_copies'])
    
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('Circuit Packing Performance - QED-C Style Benchmarks', fontsize=16)
    
    ax1 = axes[0, 0]
    benchmark_types = list(set(benchmarks))
    for bench in benchmark_types:
        bench_speedups = [speedups[i] for i, b in enumerate(benchmarks) if b == bench]
        bench_copies = [copy_counts[i] for i, b in enumerate(benchmarks) if b == bench]
        ax1.scatter(bench_copies, bench_speedups, label=bench, alpha=0.7, s=50)
    
    ax1.set_xlabel('Number of Copies')
    ax1.set_ylabel('Speedup Factor')
    ax1.set_title('Speedup by Benchmark Type')
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2 = axes[0, 1]
    for bench in benchmark_types:
        bench_fidelities = [fidelities[i] for i, b in enumerate(benchmarks) if b == bench]
        bench_copies = [copy_counts[i] for i, b in enumerate(benchmarks) if b == bench]
        ax2.scatter(bench_copies, bench_fidelities, label=bench, alpha=0.7, s=50)
    
    ax2.set_xlabel('Number of Copies')
    ax2.set_ylabel('Average Fidelity')
    ax2.set_title('Fidelity by Benchmark Type')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 1.1)
    
    ax3 = axes[1, 0]
    colors = plt.cm.viridis(np.linspace(0, 1, len(benchmark_types)))
    for i, bench in enumerate(benchmark_types):
        bench_speedups = [speedups[j] for j, b in enumerate(benchmarks) if b == bench]
        bench_fidelities = [fidelities[j] for j, b in enumerate(benchmarks) if b == bench]
        ax3.scatter(bench_speedups, bench_fidelities, label=bench, color=colors[i], alpha=0.7, s=50)
    
    ax3.set_xlabel('Speedup Factor')
    ax3.set_ylabel('Fidelity')
    ax3.set_title('Speedup vs Fidelity Trade-off')
    ax3.legend()
    ax3.grid(True, alpha=0.3)
    
    unique_copies = sorted(set(copy_counts))
    avg_speedups = []
    avg_fidelities = []
    
    for copies in unique_copies:
        copy_speedups = [speedups[i] for i, c in enumerate(copy_counts) if c == copies]
        copy_fidelities = [fidelities[i] for i, c in enumerate(copy_counts) if c == copies]
        avg_speedups.append(np.mean(copy_speedups))
        avg_fidelities.append(np.mean(copy_fidelities))

    ax4 = axes[1, 1]
    ax4_twin = ax4.twinx()
    line1 = ax4.plot(unique_copies, avg_speedups, 'b-o', label='Average Speedup')
    line2 = ax4_twin.plot(unique_copies, avg_fidelities, 'r-s', label='Average Fidelity')
    
    ax4.set_xlabel('Number of Copies')
    ax4.set_ylabel('Average Speedup', color='b')
    ax4_twin.set_ylabel('Average Fidelity', color='r')
    ax4.set_title('Performance vs Number of Copies')
    ax4.grid(True, alpha=0.3)
    
    # Combine legends
    lines = line1 + line2
    labels = [l.get_label() for l in lines]
    ax4.legend(lines, labels, loc='center right')
    
    plt.tight_layout()
    plt.show()
    
    return fig


def generate_summary_report(results):
    """Generate a summary report of benchmark results."""
    
    successful_results = {k: v for k, v in results.items() if 'error' not in v}
    failed_results = {k: v for k, v in results.items() if 'error' in v}
    
    print("\n" + "=" * 60)
    print("BENCHMARK SUMMARY REPORT")
    print("=" * 60)
    
    print(f"Total Tests: {len(results)}")
    print(f"Successful: {len(successful_results)}")
    print(f"Failed: {len(failed_results)}")
    print(f"Success Rate: {len(successful_results)/len(results)*100:.1f}%")
    
    if successful_results:
        # Calculate statistics
        speedups = [r['speedup'] for r in successful_results.values()]
        fidelities = [r['avg_fidelity'] for r in successful_results.values()]
        
        print(f"\nPerformance Statistics:")
        print(f"  Average Speedup: {np.mean(speedups):.2f}x")
        print(f"  Best Speedup: {max(speedups):.2f}x")
        print(f"  Average Fidelity: {np.mean(fidelities):.3f}")
        print(f"  Worst Fidelity: {min(fidelities):.3f}")
        
        # Best performing tests
        performance_scores = [(s * f, k) for k, r in successful_results.items() 
                            for s, f in [(r['speedup'], r['avg_fidelity'])]]
        performance_scores.sort(reverse=True)
        
        print(f"\nTop 5 Performing Tests:")
        for i, (score, test_name) in enumerate(performance_scores[:5], 1):
            result = successful_results[test_name]
            print(f"  {i}. {test_name}")
            print(f"     Speedup: {result['speedup']:.2f}x, Fidelity: {result['avg_fidelity']:.3f}")
    
    if failed_results:
        print(f"\nFailed Tests:")
        for test_name, result in failed_results.items():
            print(f"  {test_name}: {result['error']}")
    
    return {
        'total_tests': len(results),
        'successful_tests': len(successful_results),
        'failed_tests': len(failed_results),
        'success_rate': len(successful_results)/len(results) if results else 0,
        'avg_speedup': np.mean([r['speedup'] for r in successful_results.values()]) if successful_results else 0,
        'avg_fidelity': np.mean([r['avg_fidelity'] for r in successful_results.values()]) if successful_results else 0,
        'best_speedup': max([r['speedup'] for r in successful_results.values()]) if successful_results else 0,
        'worst_fidelity': min([r['avg_fidelity'] for r in successful_results.values()]) if successful_results else 0
    }


def main():
    """Main function for running the benchmark suite."""
    
    print("QED-C Style Circuit Packing Benchmark Suite")
    print("=" * 50)
    
    # Run benchmarks
    results = run_benchmark_suite()
    
    # Generate visualizations
    visualize_results(results)
    
    # Generate summary report
    summary = generate_summary_report(results)
    
    # Save results
    output_file = 'qedc_style_benchmark_results.json'
    with open(output_file, 'w') as f:
        def convert_for_json(obj):
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, dict):
                return {k: convert_for_json(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_for_json(item) for item in obj]
            else:
                return obj
        
        json_results = convert_for_json(results)
        json.dump({'results': json_results, 'summary': summary}, f, indent=2)
    
    print(f"\n✓ Results saved to {output_file}")
    
    return results
