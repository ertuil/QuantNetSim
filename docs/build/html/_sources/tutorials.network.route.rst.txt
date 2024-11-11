Routing algorithm
=====================

SimQN network module also provides a routing algorithm interface and implements the default algorithm based on the Dijkstra's algorithm.

The routing algorithm interface
----------------------------------

The routing algorithm interface is ``RouteImpl`` with two methods:

- ``build`` will generate a centralized routing tables. The input is a list of quantum nodes and a list of quantum channels.
- ``query`` will returns the routing query results. The input is a source node and a destionation node. The result is a list of the following result format:
    - metric: the routing result's metric (e.g. the total path's length)
    - next hop: the next hop after the source node
    - path: the whole path, a list of nodes on this path

.. code-block:: python

    result = [
        [3, n2, [n1, n2, n5]], # first option, metric=3, next hop=n2, path=[n1, n2, n5]
        [4, n3, [n1, n3, n4, n5]] # second option
    ]

The Dijkstra's algorithm
---------------------------

The ``DijkstraRouteAlgorithm`` implements the ``RouteImpl`` based on the Dijkstra's algorithm. It has a optional injectable metric function ``metric_func``. Its input is the quantum channel and returns the channels' metric. By default, the ``metric_func`` returns 1. But users can provide their own ``metric_func``, such as the bandwidth or the congestion of the channel.

An example of using this algorithm is:

.. code-block:: python

    from qns.network.topology import RandomTopology
    from qns.network.network import QuantumNetwork
    from qns.network.route import DijkstraRouteAlgorithm

    topo = RandomTopology(
        nodes_number=5,
        lines_number=10,
        qchannel_args={"delay": 0.05, "bandwidth": 10},
        cchannel_args={"delay": 0.05},
        memory_args=[{"capacity": 50}],
        nodes_apps=[EntanglementDistributionApp(init_fidelity=0.99)])

    # use the ``DijkstraRouteAlgorithm``, using the bandwidth as the ``metric_func``
    route = DijkstraRouteAlgorithm(metric_func=lambda qchannel: qchannel.bandwidth)

    # build the network, classic topology follows the quantum topology
    net = QuantumNetwork(topo=topo, route = route)

``QuantuNetwork`` provides two methods: ``build_route`` will build the routing tables, and ``query_route`` will query the routing result.

.. code-block:: python

    n1 = net.get_node("n1")
    n5 = net.get_node("n5")

    # build the routing tables
    net.build_route()

    # query the routing result
    result = net.query_route(n1, n5)