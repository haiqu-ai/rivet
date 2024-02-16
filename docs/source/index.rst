Rivet Transpiler Documentation
==============================

Welcome to Haiqu documentation!

This is the right place where you can find more about Haiqu's state-of-the-art
quantum software platform.

Rivet Transpiler package provides a family of functions for efficient transpilation
of quantum circuits. See `API Reference` section for more details.


Installation
------------

To install Rivet Transpiler, please clone the repository:

.. code-block:: bash

   git clone https://github.com/haiqu-ai/rivet.git

To install the transpiler with all supported stacks:

.. code-block:: bash

   pip install .[stacks]

To install only BQSKit or only Pytket support:

.. code-block:: bash

   pip install .[bqskit]
   pip install .[pytket]


Basic example
-------------------
.. image:: ../images/layout.png
  :width: 400

Transpilation includes placement of *virtual qubits* of a circuit to *physical qubits*
of the quantum device or simulator. Additionally, SWAP gates can be included to route qubits around the backend topology.

Here is a simple example of the quantum circuit with 3 qubits before and after transpilation. Function `transpile_chain` transpiles a chain of virtual circuits keeping qubits consistent.

BEFORE transpilation: 

.. code-block:: python

   import qiskit
   from qiskit.providers.fake_provider import FakeLimaV2
   from rivet_transpiler import transpile_chain

   backend = FakeLimaV2()

   circuit = qiskit.QuantumCircuit(3)

   circuit.cx(0, 1)
   circuit.cx(1, 2)
   circuit.cx(0, 2)

   circuit.barrier()

   circuit.draw()

.. code-block:: bash

   q_0: ──■─────────■──
        ┌─┴─┐       │
   q_1: ┤ X ├──■────┼──
        └───┘┌─┴─┐┌─┴─┐
   q_2: ─────┤ X ├┤ X ├
             └───┘└───┘

AFTER transpilation:

.. code-block:: python

   CHAIN = [circuit] * 3

   transpiled_circuit = transpile_chain(
      CHAIN,
      backend,
      seed_transpiler=1234
   )
   transpiled_circuit.draw(fold=-1)

.. code-block:: bash

                                 ┌───┐           ░ ┌───┐                          ░      ┌───┐          ┌───┐               ┌───┐ ░
         q_1 -> 0 ──■─────────■──┤ X ├──■────────░─┤ X ├─────────────────■────────░───■──┤ X ├──■───────┤ X ├───────────────┤ X ├─░─
                  ┌─┴─┐     ┌─┴─┐└─┬─┘┌─┴─┐      ░ └─┬─┘┌───┐     ┌───┐┌─┴─┐┌───┐ ░ ┌─┴─┐└─┬─┘┌─┴─┐┌───┐└─┬─┘┌───┐     ┌───┐└─┬─┘ ░
         q_2 -> 1 ┤ X ├──■──┤ X ├──■──┤ X ├──■───░───■──┤ X ├──■──┤ X ├┤ X ├┤ X ├─░─┤ X ├──■──┤ X ├┤ X ├──■──┤ X ├──■──┤ X ├──■───░─
                  └───┘┌─┴─┐└───┘     └───┘┌─┴─┐ ░      └─┬─┘┌─┴─┐└─┬─┘└───┘└─┬─┘ ░ └───┘     └───┘└─┬─┘     └─┬─┘┌─┴─┐└─┬─┘      ░
         q_0 -> 2 ─────┤ X ├───────────────┤ X ├─░────────■──┤ X ├──■─────────■───░──────────────────■─────────■──┤ X ├──■────────░─
                       └───┘               └───┘ ░           └───┘                ░                               └───┘           ░
   ancilla_0 -> 3 ────────────────────────────────────────────────────────────────░───────────────────────────────────────────────░─
                                                                                  ░                                               ░
   ancilla_1 -> 4 ────────────────────────────────────────────────────────────────░───────────────────────────────────────────────░─
                                                                                  ░                                               ░

Contacts
-------------------

Haiqu, info@haiqu.ai, +1 650 788 6011


.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: Get Started

   examples_overview.ipynb
   examples_examples.ipynb


.. toctree::
   :maxdepth: 1
   :hidden:
   :caption: API Reference

   api
