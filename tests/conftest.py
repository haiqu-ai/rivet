import pytest

import qiskit

from qiskit_aer import AerSimulator

from qiskit_ibm_runtime.fake_provider import fake_backend

# from qiskit_ibm_runtime.fake_provider import FakeLimaV2
# from qiskit_ibm_runtime.fake_provider import FakeMontrealV2

from rivet_transpiler import get_litmus_circuit


QUBIT_COUNTS = [5]

BACKENDS = [
    # None,
    AerSimulator,
    # FakeLimaV2,
    # FakeMontrealV2
]

REMOVE_NOISE_MODEL = True


# Fixtures

@pytest.fixture(scope="session", params=BACKENDS)
def backend(request):

    # Backend

    backend = request.param

    if backend is None:

        backend_fixture = None

    elif issubclass(backend, AerSimulator):

        backend_fixture = backend()

    elif issubclass(backend, (qiskit.providers.BackendV1,
                              qiskit.providers.BackendV2,
                              fake_backend.FakeBackend,
                              fake_backend.FakeBackendV2)):

        backend_fixture = AerSimulator.from_backend(backend())

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
