Logging and random generator
====================================

The logging module
-----------------------------------

SimQN uses the Python logging package as the logging and data monitor tools. To providing the simulator's internal states (especially the time), SimQN warps the logging. Users can use the ``logger`` from:

.. code-block:: Python

    import qns.utils.log as log

    s = Simulator()

    # install the log to the simulator to get simulator's internal status
    log.install(s)

Users can set the logging level and record logs:

.. code-block:: Python

    import logging
    
    log.logger.setLevel(logging.INFO)
    a = 1

    log.debug("debug message")
    log.info("info message %d", a)
    log.warn("warn message %d", a + 1)
    log.error("error message")
    log.critical("critical message")

Finally, SimQN provides ``monitor()`` for date output. ``sep`` sets the separator, the default separator is "," (like csv files). ``with_time`` is a boolean indicating whether add a column to record the simulator's current time.

.. code-block:: Python

    log.monitor(data1, date2, date3, with_date = True)
    # output: time, date1, date2, date3

With the ``Timer`` entity provided by SimQN, it is easy to print the network's status periodically.

.. code-block:: python

    from qns.simulator.simulator import Simulator
    from qns.entity.timer.timer import Timer
    import qns.utils.log as log

    s = Simulator(0, 10, 1000)
    log.install(s)

    # the trigger function is log network status
    def trigger_func():
        print("network status")

    # set the timer with a period
    t1 = Timer("t1", 0, 10, 0.5, trigger_func)
    t1.install(s)

    # run the simulation
    s.run()

Random generator's seed
--------------------------

SimQN uses ``random`` library from both Python standard library and ``numpy`` when measuring qubits or generating random topologies. To make the simulation results reproducible, SimQN provides ``set_seed()`` to fix the random generator's seed:

.. code-block:: python

    from qns.utils.random import set_seed

    set_seed(1641801012) # fix the random generator's seed

``get_randint(low, high)`` can generates an random integer in [low, high]; ``get_rand(low, high)`` can generate a float random number in [low, high); and ``get_choice(a)`` selects an random element in list ``a``.