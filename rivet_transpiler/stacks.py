""" Pre-defined transpilation stacks for QML Transpiler. """

import numpy as np

import warnings

from importlib.util import find_spec

import qiskit

from qiskit.qasm2 import dumps
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

from qiskit_aer import AerSimulator

try:
    import bqskit

except ModuleNotFoundError:
    warnings.warn("BQSKit not found", ImportWarning)

try:
    import pytket
    import pytket.extensions.qiskit

except ModuleNotFoundError:
    warnings.warn("Pytket not found", ImportWarning)


# Check Module Function

def check_if_module_is_imported(module_name):

    if find_spec(module_name) is None:

        raise ModuleNotFoundError(f"{module_name} not found - use "
                                  f"'pip install rivet_transpiler[{module_name}]'")


# 1) Get Stack Pass Manager

def get_stack_pass_manager(stack="qiskit", **key_arguments):

    """
    Get a Qiskit transpiler pass manager with passes for specified stack.

    Args:
        stack (str): The selected stack ('qiskit',
                                         'qiskit_qsearch',
                                         'qiskit_qfactor_qsearch',
                                         'qiskit_pytket')
        **key_arguments: Additional keyword arguments for the pass manager.
                         Usually passed from transpile function.
                         Stack-specific argument is 'qsearch_block_size'
                         for stacks that contain QSearch pass.

    Returns:
        PassManager: The Qiskit transpiler pass manager.
    """

    # Stack Implemented Check

    IMPLEMENTED_STACKS = ['qiskit',
                          'qiskit_qsearch',
                          'qiskit_qfactor_qsearch',
                          'qiskit_pytket']

    if stack not in IMPLEMENTED_STACKS:
        raise NotImplementedError(f"Stack '{stack}' not implemented")

    # Parameters

    DEFAULT_OPTIMIZATION_LEVEL = 1

    backend = key_arguments.pop("backend", None)
    qsearch_block_size = key_arguments.pop("qsearch_block_size", None)
    optimization_level = key_arguments.pop("optimization_level", DEFAULT_OPTIMIZATION_LEVEL)

    # Pass Manager

    pass_manager = generate_preset_pass_manager(optimization_level=optimization_level,
                                                backend=backend, **key_arguments)

    if stack == "qiskit_qsearch":

        pass_manager.init.append([
            QSearchPass(backend=backend,
                        qsearch_block_size=qsearch_block_size)])

    if stack == "qiskit_qfactor_qsearch":

        pass_manager.init.append([
            QFactorPass(backend=backend,
                        qsearch_block_size=qsearch_block_size)])

    if stack == "qiskit_pytket":

        pass_manager.init.append([
            PytketPass(backend=backend)])

    return pass_manager


# 2) Model From IBMQ Backend

def model_from_ibmq_backend(backend):

    """
    Create a machine model from an IBMQ backend.

    Args:
        backend: The IBMQ backend.

    Returns:
        MachineModel: The machine model representing the backend.
    """

    # Based on https://github.com/BQSKit/bqskit/blob/main/bqskit/ext/qiskit/models.py

    IBMQ_BASIS_GATES_LIMIT = 10

    # Backend

    if backend is None:
        ibmq_backend = AerSimulator()
    else:
        ibmq_backend = backend

    if isinstance(ibmq_backend, (qiskit.providers.BackendV1,
                                 qiskit.providers.fake_provider.fake_backend.FakeBackend)):

        # print('IBMQ Backend Version 1')

        qubits_count = ibmq_backend.configuration().n_qubits
        basis_gates = ibmq_backend.configuration().basis_gates
        coupling_map = ibmq_backend.configuration().coupling_map

    if isinstance(ibmq_backend, (qiskit.providers.BackendV2,
                                 qiskit.providers.fake_provider.fake_backend.FakeBackendV2)):

        # print('IBMQ Backend Version 2')

        qubits_count = ibmq_backend.target.num_qubits
        basis_gates = ibmq_backend.target.operation_names
        coupling_map = ibmq_backend.target.build_coupling_map()

    # Gate Set

    gate_dict = {'cx': bqskit.ir.gates.CNOTGate(),
                 'cz': bqskit.ir.gates.CZGate(),
                 'u3': bqskit.ir.gates.U3Gate(),
                 'u2': bqskit.ir.gates.U2Gate(),
                 'u1': bqskit.ir.gates.U1Gate(),
                 'rz': bqskit.ir.gates.RZGate(),
                 'sx': bqskit.ir.gates.SXGate(),
                 'x': bqskit.ir.gates.XGate(),
                 'p': bqskit.ir.gates.RZGate()}

    if len(basis_gates) > IBMQ_BASIS_GATES_LIMIT:

        gate_set = {bqskit.ir.gates.CNOTGate(),
                    bqskit.ir.gates.RZGate(),
                    bqskit.ir.gates.SXGate()}
    else:

        gate_set = {gate_dict.get(basis_gate)
                    for basis_gate in basis_gates} - {None}

    # Coupling List

    coupling_list = None

    if coupling_map is not None:

        coupling_list = list({tuple(sorted(edge)) for edge in coupling_map})

    # Mashine Model

    machine_model = bqskit.MachineModel(qubits_count, coupling_list, gate_set)

    return machine_model


# 3) QSearch

# 3.1) Run QSearch Synthesis

def run_qsearch_synthesis(bqskit_circuit, machine_model, block_size):

    """
    Run QSearch synthesis for a BQSKit circuit.

    Args:
        bqskit_circuit: The input BQSKit circuit.
        machine_model: BQSKit Machine Model.
        block_size (int): The block size for QSearch synthesis.

    Returns:
        bqskit.Circuit: The synthesized BQSKit circuit.
    """

    # Minimal Compilation Task
    # compilation_task = bqskit.compiler.CompilationTask(bqskit_circuit,
    #                                                    [bqskit.passes.QSearchSynthesisPass()])

    compilation_task = bqskit.compiler.CompilationTask(bqskit_circuit, [
        bqskit.passes.SetModelPass(model=machine_model),
        bqskit.passes.QuickPartitioner(block_size=block_size),
        bqskit.passes.ForEachBlockPass([
            bqskit.passes.QSearchSynthesisPass(),
            bqskit.passes.ScanningGateRemovalPass()
        ]),
        bqskit.passes.UnfoldPass()
    ])

    with bqskit.compiler.Compiler() as compiler:
        synthesized_circuit = compiler.compile(compilation_task)

    # print("bqskit_circuit.gate_counts:", bqskit_circuit.gate_counts)
    # print("synthesized_circuit.gate_counts:", synthesized_circuit.gate_counts)

    return synthesized_circuit


# 3.2) QSearch Pass

class QSearchPass(qiskit.transpiler.basepasses.TransformationPass):

    """
    Qiskit transpiler pass for running QSearch synthesis.

    Args:
        backend: The IBMQ backend.
        qsearch_block_size: The block size for QSearch synthesis (default is 2).
    """

    def __init__(self, backend, qsearch_block_size=None):

        check_if_module_is_imported('bqskit')

        if qsearch_block_size is None:
            qsearch_block_size = 2

        super().__init__()

        self.machine_model = model_from_ibmq_backend(backend)
        self.qsearch_block_size = qsearch_block_size

    def run(self, dag):

        # print("Running QSearchPass")

        qiskit_circuit = qiskit.converters.dag_to_circuit(dag)

        qiskit_qasm = dumps(qiskit_circuit)

        bqskit_qasm_converter = bqskit.ir.lang.qasm2.OPENQASM2Language()

        bqskit_circuit = bqskit_qasm_converter.decode(qiskit_qasm)

        synthesized_circuit = run_qsearch_synthesis(bqskit_circuit,
                                                    self.machine_model,
                                                    self.qsearch_block_size)

        synthesized_qasm = bqskit_qasm_converter.encode(synthesized_circuit)

        new_qiskit_circuit = qiskit.QuantumCircuit.from_qasm_str(synthesized_qasm)

        new_dag = qiskit.converters.circuit_to_dag(new_qiskit_circuit)

        return new_dag


# 4) QFactor

# 4.1) QFactor Pass

class QFactorPass(qiskit.transpiler.basepasses.TransformationPass):

    """
    Qiskit transpiler pass for running QFactor synthesis.

    Args:
        backend: The IBM Quantum Experience backend.
        qsearch_block_size: The block size for QSearch synthesis (default is 2).
    """

    def __init__(self, backend, qsearch_block_size=None):

        check_if_module_is_imported('bqskit')

        if qsearch_block_size is None:
            qsearch_block_size = 2

        super().__init__()

        self.machine_model = model_from_ibmq_backend(backend)
        self.qsearch_block_size = qsearch_block_size

    def run(self, dag):

        # print("Running QFactorPass")

        qiskit_circuit = qiskit.converters.dag_to_circuit(dag)

        qiskit_qasm = dumps(qiskit_circuit)

        bqskit_qasm_converter = bqskit.ir.lang.qasm2.OPENQASM2Language()

        bqskit_circuit = bqskit_qasm_converter.decode(qiskit_qasm)

        # Ansatz

        qubits_count = bqskit_circuit.num_qudits

        qubit_pairs = np.transpose(np.triu_indices(qubits_count, 1))

        ansatz_circuit = bqskit.ir.circuit.Circuit(qubits_count)

        for qubit_pair in qubit_pairs:

            ansatz_circuit.append_gate(bqskit.ir.gates.VariableUnitaryGate(num_qudits=2),
                                       location=qubit_pair)

        # QFactor Optimization

        target = bqskit_circuit.get_unitary()

        instantiated_circuit = ansatz_circuit.copy()

        instantiated_circuit.instantiate(
            target=target,
            method='qfactor',
            diff_tol_a=1e-12,   # Stopping criteria for distance change
            diff_tol_r=1e-6,    # Relative criteria for distance change
            dist_tol=1e-12,     # Stopping criteria for distance
            max_iters=100000,   # Maximum number of iterations
            min_iters=1000,     # Minimum number of iterations
            slowdown_factor=0,  # Larger numbers slowdown optimization to avoid local minima
        )

        # QSearch Synthesis

        synthesized_circuit = run_qsearch_synthesis(instantiated_circuit,
                                                    self.machine_model,
                                                    self.qsearch_block_size)

        synthesized_qasm = bqskit_qasm_converter.encode(synthesized_circuit)

        new_qiskit_circuit = qiskit.QuantumCircuit.from_qasm_str(synthesized_qasm)

        new_dag = qiskit.converters.circuit_to_dag(new_qiskit_circuit)

        return new_dag


# 5) Pytket

# 5.1)Pytket Pass

class PytketPass(qiskit.transpiler.basepasses.TransformationPass):

    """
    Qiskit transpiler pass for running Pytket compilation.

    Reference: https://github.com/CQCL/tket/blob/main/pytket/pytket/backends/backend.py

    Args:
        pytket_backend: The Pytket backend.
    """

    def __init__(self, backend=None):

        check_if_module_is_imported('pytket')

        # Noise Model

        if backend is None:
            noise_model = None

        elif hasattr(backend, 'noise_model'):
            noise_model = backend.noise_model

        elif hasattr(backend, 'options'):
            noise_model = backend.options.noise_model

        # Aer Backend

        pytket_backend = pytket.extensions.qiskit.AerBackend(
            noise_model=noise_model)

        super().__init__()

        self.pytket_backend = pytket_backend

    def run(self, dag):

        # print("Running PytketPass")

        qiskit_circuit = qiskit.converters.dag_to_circuit(dag)

        pytket_circuit = pytket.extensions.qiskit.qiskit_to_tk(qiskit_circuit)

        # Compilation

        compilation_pass = self.pytket_backend.default_compilation_pass(optimisation_level=2)

        compilation_pass.apply(pytket_circuit)

        # Rebase

        IBMQ_GATES = {pytket.OpType.CX,
                      pytket.OpType.Rz,
                      pytket.OpType.SX,
                      pytket.OpType.X}

        rebase_pass = pytket.passes.SequencePass([
            pytket.passes.FullPeepholeOptimise(),
            pytket.passes.auto_rebase_pass(gateset=IBMQ_GATES)
        ])

        rebase_pass.apply(pytket_circuit)

        transpiled_qiskit_circuit = pytket.extensions.qiskit.tk_to_qiskit(pytket_circuit)

        new_dag = qiskit.converters.circuit_to_dag(transpiled_qiskit_circuit)

        return new_dag
