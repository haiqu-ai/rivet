import pytest

import qiskit

from rivet_transpiler import transpile


# Stacks

STACKS = [
    "qiskit",
    "qiskit_qsearch",
    "qiskit_qfactor_qsearch",
    "qiskit_pytket"
]

QSEARCH_BLOCK_SIZE = 2


@pytest.mark.parametrize("stack", STACKS)
def test_stack(bound_litmus_circuit, backend, stack):

    transpiled_litmus_circuit = transpile(
        bound_litmus_circuit,
        backend,
        stack=stack,
        qsearch_block_size=QSEARCH_BLOCK_SIZE,
        seed_transpiler=1234)

    assert transpiled_litmus_circuit is not None


def test_stack_not_implemented():

    circuit = qiskit.QuantumCircuit(3)

    with pytest.raises(NotImplementedError):

        transpiled_circuit = transpile(
            circuit,
            backend=None,
            stack="not_implemented_stack")

        return transpiled_circuit
