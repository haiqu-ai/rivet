import pytest

import qiskit

# from qiskit.providers.fake_provider import FakeBackend5QV2
# from qiskit.providers.fake_provider import FakeLimaV2
# from qiskit.providers.fake_provider import FakeGuadalupeV2
# from qiskit.providers.fake_provider import FakeBoeblingenV2
from qiskit.providers.fake_provider import FakeMontrealV2

from qml_transpiler import get_litmus_circuit


QUBIT_COUNTS = [5]

BACKENDS = [
    None,
    qiskit.providers.aer.AerSimulator,
    # FakeBackend5QV2,
    # FakeLimaV2,
    # FakeGuadalupeV2,
    # FakeBoeblingenV2,
    FakeMontrealV2
]

REMOVE_NOISE_MODEL = True


# Fixtures

@pytest.fixture(scope="session", params=BACKENDS)
def backend(request):

    # Backend

    backend = request.param

    if backend is None:

        backend_fixture = None

    elif issubclass(backend, qiskit.providers.aer.AerSimulator):

        backend_fixture = backend()

    elif issubclass(backend, (qiskit.providers.BackendV1,
                              qiskit.providers.BackendV2,
                              qiskit.providers.fake_provider.FakeBackend,
                              qiskit.providers.fake_provider.FakeBackendV2)):

        backend_fixture = qiskit.providers.aer.AerSimulator.from_backend(backend())

    # Noise Model

    if REMOVE_NOISE_MODEL is True and backend is not None:

        backend_fixture.options.noise_model = None

    return backend_fixture


@pytest.fixture(params=QUBIT_COUNTS)
def qubits_count(request):

    qubits_count = request.param

    return qubits_count


@pytest.fixture
def litmus_circuit(qubits_count):

    litmus_circuit = get_litmus_circuit(qubits_count, "Litmus")

    return litmus_circuit


@pytest.fixture
def bound_litmus_circuit(litmus_circuit):

    bound_litmus_circuit = litmus_circuit.copy()

    for index, parameter in enumerate(bound_litmus_circuit.parameters):

        bound_litmus_circuit.assign_parameters(
            {parameter: index},
            inplace=True)

    return bound_litmus_circuit
