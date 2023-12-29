import pytest

import qiskit

from qiskit.providers import aer

# from qiskit.providers.fake_provider import FakeBackend5QV2
# from qiskit.providers.fake_provider import FakeLimaV2
# from qiskit.providers.fake_provider import FakeGuadalupeV2
# from qiskit.providers.fake_provider import FakeBoeblingenV2
from qiskit.providers.fake_provider import FakeMontrealV2

from qml_transpiler import get_litmus_circuit


QUBIT_COUNTS = [5]

BACKENDS = [
    aer.AerSimulator,
    # FakeBackend5QV2,
    # FakeLimaV2,
    # FakeGuadalupeV2,
    # FakeBoeblingenV2,
    FakeMontrealV2
]


# Fixtures

@pytest.fixture(scope="session", params=BACKENDS)
def backend(request):

    if request.param is None:

        return None

    backend = request.param()

    if not isinstance(backend, qiskit.providers.aer.AerSimulator):

        backend = qiskit.providers.aer.AerSimulator.from_backend(backend)

    backend.options.noise_model = None

    return backend


@pytest.fixture(params=QUBIT_COUNTS)
def litmus_circuit(request):

    qubit_count = request.param

    litmus_circuit = get_litmus_circuit(qubit_count, "Litmus")

    return litmus_circuit


@pytest.fixture
def bound_litmus_circuit(litmus_circuit):

    bound_litmus_circuit = litmus_circuit.copy()

    for index, parameter in enumerate(bound_litmus_circuit.parameters):

        bound_litmus_circuit.assign_parameters(
            {parameter: index},
            inplace=True)

    return bound_litmus_circuit
