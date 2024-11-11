Topology generator
======================

Build quantum network topology
-------------------------------

SimQN provides a interface (``qns.network.topology.topo.Topology``) for topology generators. All topology has the following initiate variables:

- ``nodes_number``: the number of nodes in the network
- ``nodes_apps``: a list of applications that will be added to all nodes
- ``qchannel_args``: the common attribution directory of quantum channels. Its key is the initiate variable's name of ``QuantumChannel``, for example: :code:`{"delay": 0.3, "bandwidth": 10}`.
- ``qchannel_args``: the common attribution directory of classic channels. Its key is the initiate variable's name of ``ClassicChannel``, for example: :code:`{"delay": 0.3, "bandwidth": 10}`.
- ``memory_args``: a list of the common attributions directory of the quantum memories. Its key is the initiate variable's name of ``QuantumMemory``, for example: :code:`[{"capacity": 10}, {"capacity": 10, "store_error_model_args": {"t_coh": 1}}]`


Topology generators may have more parameters. The following example shows how to use the random topology generator, and it has an optional parameter ``lines_number``:

.. code-block:: python

    from qns.network.topology import RandomTopology
    from qns.network.network import QuantumNetwork

    topo = RandomTopology(
        nodes_number=5,
        lines_number=10,
        qchannel_args={"delay": 0.05},
        cchannel_args={"delay": 0.05},
        memory_args=[{"capacity": 50}],
        nodes_apps=[EntanglementDistributionApp(init_fidelity=0.99)])

    # build the network
    net = QuantumNetwork(topo=topo)

SimQn provides several topology generators:

- ``BasicTopology`` generates several quantum nodes but no quantum channels. All nodes are not connected with each other.
- ``LineTopology`` connects all nodes to from a line topology. 
- ``GridTopology`` forms a square grid topology. ``nodes_number`` should be a perfect square number.
- ``TreeTopology`` generates a tree topology. It has an additional parameter ``children_number``. Each parent node will connect to  ``children_number`` child nodes.
- ``RandomTopology`` generates a connected random topology based on the spanning tree. It has an additional parameter ``lines_number`` indicating the number of quantum channels.
- ``WaxmanTopology`` is another random topology generator based on the Waxman's algorithm. It has three additional parameters, ``size``, ``alpha``, and ``bete``. The topology is in a :math:`size*size` area. Both ``alpha`` and ``bete`` are parameters of the Waxman's algorithm.

Users can build their own topology by inheriting the ``Topology`` class and implement the ``build`` method.


Build classic topology
--------------------------

SimQN is able to generate classic topologies as well. The classic topology is indicated by the variable ``classic_topo``. It is an ``Enum`` with the following options:

- ``ClassicTopology.All``, all nodes are connected directly by a classic channels
- ``ClassicTopology.Empty``, no classic topology will be built
- ``ClassicTopology.Follow``, the classic topology will be the same to the quantum topology

.. code-block:: python

    from qns.network.topology import RandomTopology
    from qns.network.network import QuantumNetwork
    from qns.network.topology.topo import ClassicTopology

    topo = RandomTopology(
        nodes_number=5,
        lines_number=10,
        qchannel_args={"delay": 0.05},
        cchannel_args={"delay": 0.05},
        memory_args=[{"capacity": 50}],
        nodes_apps=[EntanglementDistributionApp(init_fidelity=0.99)])

    # build the network, classic topology follows the quantum topology
    net = QuantumNetwork(topo=topo, classic_topo=ClassicTopology.Follow)

Manage the network
-------------------

The ``QuantumNetwork`` provides the following APIs to get or add nodes, channels, memories and applications:

- ``install``, initiate all nodes, channels, memories and applications in one step
- ``add_node``, add a new node
- ``get_node``, get a quantum nodes by its name
- ``add_qchannel``, add a new quantum channel
- ``get_qchannel``, get a quantum channel by its name
- ``add_cchannel``, add a new classic channel
- ``get_cchannel``, get a classic channel by its name
- ``add_memories``, add new quantum memories to all nodes

.. code-block:: python

    # get node by its name
    n1 = net.get_node("n1")

    # add a new node
    n2 = QNode(name="n2")
    net.add_node(n2)

      # get a quantum channel by its name
    l1 = net.get_qchannel("l1,2")

    # add a quantum channel
    l2 = QuantumChannel("l2")
    net.add_qchannel(l2)

    node_list = net.nodes # get all nodes
    qchannel_list = net.qchannels # get all quantum channels
    cchannel_list = net.cchannels # get all classic channels

    # produce a simulator
    s = Simulator(0, 60)

    # initiate the whole network
    net.install(s)

    s.run()
