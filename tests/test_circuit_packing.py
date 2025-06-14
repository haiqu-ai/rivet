import pytest
import numpy as np
from collections import defaultdict

import qiskit
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
from qiskit.transpiler import Target
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeLimaV2, FakeMontrealV2

from rivet_transpiler.circuit_packing import (
    pack_circuits, unpack_results, analyze_packing_efficiency,
    pack_and_transpile_chain
)
from rivet_transpiler import get_litmus_circuit


class TestCircuitPacking:
    
    @pytest.fixture
    def simple_circuit(self):
        """Create a simple test circuit."""
        circuit = QuantumCircuit(3)
        circuit.h(0)
        circuit.cx(0, 1)
        circuit.cx(1, 2)
        circuit.rz(np.pi/4, 2)
        return circuit
    
    @pytest.fixture
    def target_device(self):
        """Create a mock target device."""
        backend = FakeMontrealV2()
        return backend.target
    
    def test_pack_circuits_basic(self, simple_circuit, target_device):
        """Test basic circuit packing functionality."""
        num_copies = 3
        
        packed_circuit, qubits_map = pack_circuits(
            simple_circuit, num_copies, target_device
        )

        assert packed_circuit.num_qubits >= simple_circuit.num_qubits * num_copies
        assert packed_circuit.num_clbits == simple_circuit.num_qubits * num_copies
        assert len(qubits_map) == num_copies
        
        for copy_idx in range(num_copies):
            assert copy_idx in qubits_map
            assert len(qubits_map[copy_idx]) == simple_circuit.num_qubits
    
    def test_pack_circuits_no_overlap(self, simple_circuit, target_device):
        """Test that packed circuits use non-overlapping qubits."""
        num_copies = 4
        
        packed_circuit, qubits_map = pack_circuits(
            simple_circuit, num_copies, target_device
        )
        
        all_used_qubits = set()
        for copy_idx in range(num_copies):
            copy_qubits = set(qubits_map[copy_idx].values())
            
            # Check no overlap with previously used qubits
            assert len(copy_qubits.intersection(all_used_qubits)) == 0
            all_used_qubits.update(copy_qubits)
    
    def test_unpack_results_basic(self):
        """Test basic result unpacking."""
        num_copies = 2
        qubits_per_copy = 3
        
        # Create mock packed results
        # Classical bits are ordered as: copy0_q0, copy0_q1, copy0_q2, copy1_q0, copy1_q1, copy1_q2
        mock_counts = {
            '000001': 100,  # Copy 0: '000', Copy 1: '001'
            '101010': 200,  # Copy 0: '101', Copy 1: '010'
            '111111': 150,  # Copy 0: '111', Copy 1: '111'
        }
        
        qubits_map = {
            0: {0: 0, 1: 1, 2: 2},  # First copy uses qubits 0,1,2
            1: {0: 3, 1: 4, 2: 5}   # Second copy uses qubits 3,4,5
        }
        
        unpacked = unpack_results(mock_counts, num_copies, qubits_map)
        
        # Check structure
        assert len(unpacked) == num_copies
        assert 0 in unpacked and 1 in unpacked
        
        # Check individual results
        expected_copy0 = {'000': 100, '101': 200, '111': 150}
        expected_copy1 = {'001': 100, '010': 200, '111': 150}
        
        assert unpacked[0] == expected_copy0
        assert unpacked[1] == expected_copy1
    
    def test_packing_with_different_targets(self, simple_circuit):
        """Test packing with different target devices."""
        targets = [
            None,  # No target
            FakeLimaV2().target,  # Small device
            FakeMontrealV2().target  # Larger device
        ]
        
        num_copies = 2
        
        for target in targets:
            try:
                packed_circuit, qubits_map = pack_circuits(
                    simple_circuit, num_copies, target
                )
                
                # Basic checks
                assert packed_circuit is not None
                assert len(qubits_map) == num_copies
                
            except ValueError as e:
                # Allow failures for devices too small
                if "Device has" in str(e) and "qubits, but" in str(e):
                    continue
                else:
                    raise
    
    def test_analyze_packing_efficiency(self, simple_circuit, target_device):
        """Test packing efficiency analysis."""
        num_copies = 3
        
        packed_circuit, _ = pack_circuits(simple_circuit, num_copies, target_device)
        
        metrics = analyze_packing_efficiency(
            simple_circuit, packed_circuit, num_copies, target_device
        )
        
        # Check that metrics are computed
        required_metrics = [
            'qubit_utilization', 'packing_ratio', 'original_qubits',
            'packed_qubits', 'qubit_efficiency', 'theoretical_speedup'
        ]
        
        for metric in required_metrics:
            assert metric in metrics
            assert isinstance(metrics[metric], (int, float))
        
        # Check logical relationships
        assert metrics['packing_ratio'] == num_copies
        assert metrics['original_qubits'] == simple_circuit.num_qubits
        assert metrics['theoretical_speedup'] == num_copies
    
    def test_pack_too_many_copies(self, simple_circuit):
        """Test error handling when requesting too many copies."""
        # Create a small target device
        small_target = FakeLimaV2().target  # 5 qubits
        
        # Try to pack too many copies
        with pytest.raises(ValueError, match="Device has"):
            pack_circuits(simple_circuit, 10, small_target)
    
    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        circuit = QuantumCircuit(2)
        target = FakeMontrealV2().target
        
        # Test negative copies
        with pytest.raises(ValueError, match="Number of copies must be positive"):
            pack_circuits(circuit, -1, target)
        
        # Test zero copies
        with pytest.raises(ValueError, match="Number of copies must be positive"):
            pack_circuits(circuit, 0, target)
        
        # Test circuit with classical bits
        circuit_with_clbits = QuantumCircuit(2, 2)
        with pytest.raises(ValueError, match="should not have classical bits"):
            pack_circuits(circuit_with_clbits, 2, target)
    
    def test_integration_with_litmus_circuit(self, target_device):
        """Test packing with Rivet's litmus circuits."""
        litmus = get_litmus_circuit(4, "TestLitmus")
        
        # Bind parameters to make it concrete
        bound_litmus = litmus.copy()
        for i, param in enumerate(litmus.parameters):
            bound_litmus.assign_parameters({param: i * 0.1}, inplace=True)
        
        num_copies = 2
        packed_circuit, qubits_map = pack_circuits(
            bound_litmus, num_copies, target_device
        )
        
        assert packed_circuit.num_qubits >= bound_litmus.num_qubits * num_copies
        assert len(qubits_map) == num_copies
    
    def test_pack_and_transpile_chain(self, simple_circuit, target_device):
        """Test packing multiple different circuits in a chain."""
        circuit2 = QuantumCircuit(2)
        circuit2.ry(np.pi/3, 0)
        circuit2.cx(0, 1)
        
        circuits = [simple_circuit, circuit2]
        num_copies = 2
        
        final_circuit, qubits_maps = pack_and_transpile_chain(
            circuits, num_copies, target_device
        )
        
        assert len(qubits_maps) == len(circuits)
        assert final_circuit is not None
        assert final_circuit.num_clbits > 0  # Should have measurements
