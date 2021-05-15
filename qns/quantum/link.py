import random
from qns.quantum.entanglement import Entanglement
from qns.topo import Channel
from qns.schedular import Simulator, Event
from .events import GenerationEntanglementAfterEvent, GenerationEvent

# An EPR generator

class QuantumChannel(Channel):
    def __init__(self, nodes=[],  rate=1, possible=1, delay=0, generation_func=None):
        self.nodes = nodes
        self.rate = rate
        self.possible = possible
        self.delay = delay
        if generation_func is None:
            self.generation_func = self.default_generation_func
        else:
            self.generation_func = generation_func

    def install(self, simulator: Simulator):
        self.simulator = simulator
        self.delay_time_slice = simulator.to_time_slice(self.delay)

        for n in self.nodes:
            n.links.append(self)

        ge = GenerationEvent(self, simulator.current_time)
        start_time_slice = simulator.start_time_slice
        end_time_slice = simulator.end_time_slice
        step_time_slice = int(simulator.time_accuracy / self.rate)
        for t in range(start_time_slice, end_time_slice, step_time_slice):
            simulator.add_event(t, ge)

    def handle(self, simulator: Simulator, msg: object, source=None, event: Event = None):
        pass

    def default_generation_func(self, simulator: Simulator):
        '''generation one EPR'''
        if random.random() > self.possible:
            print("generation failed due to failure")
            return

        e = Entanglement(self.nodes, simulator.current_time_slice)
        geae = GenerationEntanglementAfterEvent(
            e, self, self.nodes, simulator.current_time)
        simulator.add_event(simulator.current_time_slice +
                            self.delay_time_slice, geae)

    def generation(self, simulator: Simulator):
        self.generation_func(simulator)
