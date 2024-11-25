Quick start
===========================

In this guide, users can start a quantum network simulation in a few lines of code. We present two examples to give a overall sense of SimQN.

QKD simulation with manual network construction
-----------------------------------------------------

The first experiments, we will carry out a BB84 protocol between two nodes. ``BB84SendApp`` and ``BB84RecvApp`` provided by SimQN implements the major protocol. First, we instantiate  the simulator:

.. code-block:: python

    from qns.simulator.simulator import Simulator

    s = Simulator(0, 10, accuracy=10000000000)

The simulation is last for 10 seconds and the ``accuracy`` is 10,000,000,000 slots in one second. Then, we generate two nodes and connect them with a quantum channel and a classic channel:

.. code-block:: python

    from qns.entity.cchannel.cchannel import ClassicChannel
    from qns.entity.qchannel.qchannel import QuantumChannel
    from qns.entity import QNode
    import numpy as np

    light_speed = 299791458
    length = 100000 # 100,000 m

    def drop_rate(length):
        # drop 0.2 db/KM
        return 1 - np.exp(- length / 50000) #or  1 - np.power(10, - length / 50000)

    # generate quantum nodes
    n1 = QNode(name="n1")
    n2 = QNode(name="n2")

    # generate quantum channels and classic channels
    qlink = QuantumChannel(name="l1", delay=length / light_speed,
        drop_rate=drop_rate(length))

    clink = ClassicChannel(name="c1", delay=length / light_speed)

    # add channels to the nodes
    n1.add_cchannel(clink)
    n2.add_cchannel(clink)
    n1.add_qchannel(qlink)
    n2.add_qchannel(qlink)

Finally, we add ``BB84SendApp`` to ``n1``, it will generate qubits with random bases and send the qubit to n2. ``BB84RecvApp`` will be installed on ``n2``, it will receive the qubits and measure the qubits with random bases.

.. code-block:: python

    from qns.network.protocol.bb84 import BB84RecvApp, BB84SendApp

    sp = BB84SendApp(n2, qlink, clink, send_rate=1000)
    rp = BB84RecvApp(n1, qlink, clink)
    n1.add_apps(sp)
    n2.add_apps(rp)

We set the sending rate to 1000 qubits/second. We install the simulator to all nodes (automatically initiate all channels and applications). Finally, we run the simulation and get the results.

.. code-block:: python

    # install all nodes
    n1.install(s)
    n2.install(s)

    # run the simulation
    s.run()

    # BB84RecvApp's succ_key_pool counts the number of success key distribution
    # the rate is succ_key_pool/ simulation_time (10s)
    print(len(rp.succ_key_pool) / 10)

Entanglement distribution with topology generator
-----------------------------------------------------

To further reduce user's work, SimQN provides the network module to build large-scale networks. In this experiment, we will use ``EntanglementDistributionApp`` to distribute entanglements from remote nodes.

First, we generate the simulator and produce the network produce:

.. code-block:: python

    from qns.simulator.simulator import Simulator
    from qns.network.topology import RandomTopology
    from qns.network.protocol.entanglement_distribution import EntanglementDistributionApp
    from qns.network import QuantumNetwork
    from qns.network.route.dijkstra import DijkstraRouteAlgorithm
    from qns.network.topology.topo import ClassicTopology
    import qns.utils.log as log
    import logging

    init_fidelity = 0.99 # the initial entanglement's fidelity 
    nodes_number = 150 # the number of nodes
    lines_number = 450 # the number of quantum channels
    qchannel_delay = 0.05 # the delay of quantum channels
    cchannel_delay = 0.05 # the delay of classic channels
    memory_capacity = 50 # the size of quantum memories
    send_rate = 10 # the send rate
    requests_number = 10 # the number of sessions (SD-pairs)

    # generate the simulator
    s = Simulator(0, 10, accuracy=1000000)

    # set the log's level
    log.logger.setLevel(logging.INFO)
    log.install(s)

    # generate a random topology using the parameters above
    # each node will install EntanglementDistributionApp for hop-by-hop entanglement distribution
    topo = RandomTopology(nodes_number=nodes_number,
        lines_number=lines_number,
        qchannel_args={"delay": qchannel_delay},
        cchannel_args={"delay": cchannel_delay},
        memory_args=[{"capacity": memory_capacity}],
        nodes_apps=[EntanglementDistributionApp(init_fidelity=init_fidelity)])

    # build the network, with Dijkstra's routing algorithm
    net = QuantumNetwork( topo=topo, classic_topo=ClassicTopology.All, route=DijkstraRouteAlgorithm())

    # build the routing table
    net.build_route()

    # randomly select multiple sessions (SD-pars)
    net.random_requests(requests_number, attr={"send_rate": send_rate})

    # all entities in the network will install the simulator and do initiate works.
    net.install(s)

Now, it is possible to run the simulation and get the results:

.. code-block:: Python

    # run simulation
    s.run()

    # count the number of successful entanglement distribution for each session
    results = [req.src.apps[0].success_count for req in net.requests]

    # log the results
    log.monitor(requests_number, nodes_number, results, s.time_spend, sep=" ")
