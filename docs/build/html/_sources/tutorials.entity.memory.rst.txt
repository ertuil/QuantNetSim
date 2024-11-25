Quantum memory: the device to store qubits
==============================================

Quantum memory has two modes: the synchronous and asynchronous mode. In synchronous model, it can not describe the time delay in writing and reading qubits. Users may use ``write`` and ``read`` functions to operate the memory directly. However, in asynchronous mode, quantum memory works as an independent entity. Quantum nodes uses events to control the memories and get the results.

Synchronous mode
----------------------------------

Quantum memory is an entity that can store qubits. It can be equipped to a quantum nodes:

.. code-block:: python

    from qns.entity.node.node import QNode
    from qns.entity.memory.memory import QuantumMemory

    n1 = QNode("n1") # a quantum node named "n1"
    m = QuantumMemory("m1")
    n1.add_memory(m)

``read`` and ``write`` methods are used to store and get a qubit. The ``read`` methods will use the qubit's name or reference as the keyword to search the qubit.

.. code-block:: python

    q1 = Qubit()
    m.write(q1)
    q2 = m.read(q1)

The memory can have a limited size. ``is_full`` function returns whether the memory is full:

.. code-block:: python

    from qns.entity.node.node import QNode
    from qns.entity.memory.memory import QuantumMemory

    n1 = QNode("n1") # a quantum node named "n1"
    m2 = QuantumMemory("m2", capacity = 10) # a memory can store 10 qubits
    n1.add_memory(m2)

    m2.is_full() # check if the memory is full

Asynchronous mode
----------------------------------

In this mode, quantum nodes (or applications) needs to use ``MemoryWriteRequestEvent`` and ``MemoryReadRequestEvent`` events to send requests to the quantum memories and collect the results by listening to ``MemoryWriteResponseEvent`` and ``MemoryReadResponseEvent`` events. In this way, users can model the time delay in reading and writing quantum memories. In asynchronous mode, the quantum memories have an additional input parameter called ``delay`` to set the read/write time delay. ``delay`` can be a float or a ``DelayModel``.

Here, we give an example of asynchronous mode. The quantum node first install a ``MemoryResponseApp`` application to handle the read/write result. During the simulation, the node generates ``MemoryWriteRequestEvent`` to save a qubit and use ``MemoryReadRequestEvent`` to get the qubit one second later.

.. code-block:: python

    class MemoryResponseApp(Application):
        def __init__(self):
            super().__init__()
            self.add_handler(self.MemoryReadhandler, [MemoryReadResponseEvent], [])
            self.add_handler(self.MemoryWritehandler, [MemoryWriteResponseEvent], [])

        def MemoryReadhandler(self, node, event: Event) -> Optional[bool]:
            result = event.result # the saving qubit
            print("self._simulator.tc.sec: {}".format(self._simulator.tc))
            print("result: {}".format(result))
            assert (self._simulator.tc.sec == 1.5)
            assert (result is not None)

        def MemoryWritehandler(self, node, event: Event) -> Optional[bool]:
            result = event.result # if the qubit is saved successfully
            print("self._simulator.tc.sec: {}".format(self._simulator.tc))
            print("result: {}".format(result))
            assert (self._simulator.tc.sec == 0.5)
            assert (result)

    n1 = QNode("n1")
    app = MemoryReadResponseApp()
    n1.add_apps(app)

    m = QuantumMemory("m1", delay=0.5)
    n1.add_memory(m)

    s = Simulator(0, 10, 1000)
    n1.install(s)

    q1 = Qubit(name="q1")
    write_request = MemoryWriteRequestEvent(memory=m, qubit=q1, t=s.time(sec=0), by=n1)
    read_request = MemoryReadRequestEvent(memory=m, key="q1", t=s.time(sec=1), by=n1)
    s.add_event(write_request)
    s.add_event(read_request)
    s.run()


Error models in a quantum memory
----------------------------------

Also, storage error can be introduced during storage a qubit. The error is handled in function ``storage_error_model``, which takes the storage time and other parameters as the input. Those parameters shows the memory attributions (such as the coherence time), and they can be set using ``decoherence_rate`` and ``store_error_model_args``. ``decoherence_rate`` is the decoherence rate, while ``store_error_model_args`` is a directory that contains other parameters for the error model

.. code-block:: python

    from qns.entity.memory.memory import QuantumMemory
    from qns.models.epr import WernerStateEntanglement

    class ErrorEntanglement(WernerStateEntanglement):
        def storage_error_model(self, t: float, **kwargs):
            # storage error will reduce the fidelity 
            t_coh = kwargs.get("t_coh", 1)
            self.w = self.w * np.exp(- t / t_coh)

    # memory error attributions: coherence time is 1 second
    m3 = QuantumMemory("m3", capacity = 10, decoherence_rate=0.2, store_error_model_args = {"t_coh": 1})

    # generate an entanglement and store it
    epr1 = ErrorEntanglement(name="epr1")
    m3.write(epr1)

    # after a while, the fidelity will drop
    epr2 = m3.read("epr1")
