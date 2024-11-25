The qubit model
======================

The qubit model is in package ``qns.models.qubit``. ``Qubit`` is the class to represent a qubit. One or more qubits (entangled) qubits form a system ``QState``, which uses a complex matrix to denote the current quantum state. It is easy to produce a qubit:

.. code-block:: python

    from qns.models.qubit.qubit import Qubit
    from qns.models.qubit.const import QUBIT_STATE_0

    q0 = Qubit(state=QUBIT_STATE_0, name="q0")
    q1 = Qubit(state=QUBIT_STATE_0, name="q1")

`QUBIT_STATE_0` is the pre-defined matrix for |0>. Some states includes:

- QUBIT_STATE_0 = :math:`\ket{0}`
- QUBIT_STATE_1 = :math:`\ket{1}`
- QUBIT_STATE_P = :math:`\frac{1}{2} (\ket{0}+\ket{1})`
- QUBIT_STATE_N = :math:`\frac{1}{2} (\ket{0}-\ket{1})`
- QUBIT_STATE_R = :math:`\frac{1}{2} (-i \ket{0}+\ket{1})`
- QUBIT_STATE_L = :math:`\frac{1}{2} (\ket{0} - i \ket{1})`

All states are numpy matrix, for example:

.. code-block:: python

    QUBIT_STATE_0 = np.array([[1], [0]], dtype=np.complex128)


Quantum operations
-----------------------

We implement some quantum gates. And those gates can change the qubit's state:

.. code-block:: python

    from qns.models.qubit.gate import H, CNOT

    H(q0) # hadamard gate
    CNOT(q0, q1) # controlled-not gate

    q0.operate(H) # another way to operate Hadamard gate on qubit q0

    # A stochastic operate. This operate will operate I, X, Y, Z gate with the possibility 0.7, 0.1, 0.1, 0.1 respectively.
    # The process usually turns a pure state into a mixed state and is used to represent decoherence
    q0.stochastic_operate([I, X, Y, Z], [0.7, 0.1, 0.1, 0.1])

Those gates includes Pauli I, X, Y, Z gate, HADAMARD gate, T gate, S gate, phase rotate gate, CNOT gate. The detailed functions of those gates can be found at :doc:`qns.models.qubit`. Users can build their own quantum gates as well.

Quantum measurement
-------------------------

It is possible to measure the qubit's state (Pauli Z base measure) using `measure` function:

.. code-block:: python

    print(q0.measure()) # 0 or 1

For not entangled single qubit, Pauli Y measure and Z measure is also available:

.. code-block:: python

    q0.measureX() # X base measure
    q0.measureY() # Y base measure
    q0.measureZ() # Z base measure

Error models
-------------------------

To present errors in storage or transmission, users can build their qubits models by implementing the ``transfer_error_model`` and ``storage_error_model``. The following examples shows a qubit will suffer bit flip error during transmission:

.. code-block:: python

    class QubitWithError(Qubit):
        def transfer_error_model(self, length: float, **kwargs):
            lkm = length / 1000
            standand_lkm = 50.0
            theta = random.random() * lkm / standand_lkm * np.pi / 4
            operation = np.array([[np.cos(theta), - np.sin(theta)], [np.sin(theta), np.cos(theta)]], dtype=np.complex128)
            self.state.state = np.dot(operation, self.state.state)

    qubit = QubitWithError(state=QUBIT_STATE_0)

SimQN also provides some commonly used decoherence models, including dephase model and depolar model for both transmission error and storage error in ``qns.model.qubit.decoherence``. Users can use the ``qns.model.qubit.factory`` to set up the models:

.. code-block:: python

    from qns.models.qubit.decoherence import DepolarStorageErrorModel, DephaseTransferErrorModel
    from qns.models.qubit.factory import QubitFactory

    Qubit = QubitFactory(store_error_model=DepolarStorageErrorModel, transfer_error_model=DephaseTransferErrorModel)
    q1 = Qubit(name="q1")
    q2 = Qubit(name="q2")

SimQN also have error models for operating or measuring on qubits, by implementing the ``operate_error_model`` and ``measure_error_model``:

.. code-block:: python

    from qns.models.qubit.decoherence import DepolarStorageErrorModel, DephaseTransferErrorModel
    from qns.models.qubit.factory import QubitFactory

    Qubit = QubitFactory(operate_decoherence_rate=0.2,
                         measure_decoherence_rate=0.2, measure_error_model=DepolarMeasureErrorModel)
    q0 = Qubit(state=QUBIT_STATE_0, name="q0")
    q0.measure()

The ``operate_decoherence_rate`` and ``measure_decoherence_rate`` is the decoherence rate in `Hz`.

Example of entanglement swapping
----------------------------------------

Finally, we present an example of entanglement swapping:

.. code-block:: python

    from qns.models.qubit.qubit import Qubit
    from qns.models.qubit.gate import H, CNOT, X, Z
    from qns.models.qubit.const import QUBIT_STATE_0

    q0 = Qubit(state=QUBIT_STATE_0, name="q0")
    q1 = Qubit(state=QUBIT_STATE_0, name="q1")

    q2 = Qubit(state=QUBIT_STATE_0, name="q2")
    q3 = Qubit(state=QUBIT_STATE_0, name="q3")

    # entangle q0 and q1
    H(q0)
    CNOT(q0, q1)

    # entangle q2 and q3
    H(q2)
    CNOT(q2, q3)

    # entanglement swapping
    CNOT(q1, q2)
    H(q1)

    # measure q2 and q1
    c0 = q2.measure()
    c1 = q1.measure()

    if c0 == 1 and c1 == 0:
        X(q3)
    elif c0 == 0 and c1 == 1:
        Z(q3)
    elif c0 == 1 and c1 == 1:
        X(q3)
        Z(q3)

    # now q0 and q3 are entangled
    assert(q0.measure() == q3.measure())
