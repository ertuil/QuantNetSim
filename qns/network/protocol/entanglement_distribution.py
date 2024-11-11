#    SimQN: a discrete-event simulator for the quantum networks
#    Copyright (C) 2021-2022 Lutong Chen, Jian Li, Kaiping Xue
#    University of Science and Technology of China, USTC.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

from typing import Dict, Optional
import uuid

from qns.entity.cchannel.cchannel import ClassicChannel, ClassicPacket, RecvClassicPacket
from qns.entity.memory.memory import QuantumMemory
from qns.entity.node.app import Application
from qns.entity.node.node import QNode
from qns.entity.qchannel.qchannel import QuantumChannel, RecvQubitPacket
from qns.models.core.backend import QuantumModel
from qns.network.requests import Request
from qns.simulator.event import Event, func_to_event
from qns.simulator.simulator import Simulator
from qns.network import QuantumNetwork
from qns.models.epr import WernerStateEntanglement
from qns.simulator.ts import Time
import qns.utils.log as log


class Transmit():
    def __init__(self, id: str, src: QNode, dst: QNode,
                 first_epr_name: Optional[str] = None, second_epr_name: Optional[str] = None):
        self.id = id
        self.src = src
        self.dst = dst
        self.first_epr_name = first_epr_name
        self.second_epr_name = second_epr_name

    def __repr__(self) -> str:
        return f"<transmit {self.id}: {self.src} -> {self.dst},\
             epr: {self.first_epr_name}, {self.second_epr_name}>"


class EntanglementDistributionApp(Application):
    def __init__(self, send_rate: Optional[int] = None, init_fidelity: float = 0.99):
        super().__init__()
        self.init_fidelity = init_fidelity
        self.net: QuantumNetwork = None
        self.own: QNode = None
        self.memory: QuantumMemory = None
        self.src: Optional[QNode] = None
        self.dst: Optional[QNode] = None
        self.send_rate: int = send_rate

        self.state: Dict[str, Transmit] = {}

        self.success = []
        self.success_count = 0
        self.send_count = 0

        self.add_handler(self.RecvQubitHandler, [RecvQubitPacket])
        self.add_handler(self.RecvClassicPacketHandler, [RecvClassicPacket])

    def install(self, node: QNode, simulator: Simulator):
        super().install(node, simulator)
        self.own: QNode = self._node
        self.memory: QuantumMemory = self.own.memories[0]
        self.net = self.own.network
        try:
            request: Request = self.own.requests[0]
            if self.own == request.src:
                self.dst = request.dest
            elif self.own == request.dest:
                self.src = request.src
            self.send_rate = request.attr.get("send_rate")
        except IndexError:
            pass

        if self.dst is not None:
            # I am a sender
            t = simulator.ts
            event = func_to_event(t, self.new_distribution, by=self)
            self._simulator.add_event(event)

    def RecvQubitHandler(self, node: QNode, event: Event):
        self.response_distribution(event)

    def RecvClassicPacketHandler(self, node: QNode, event: Event):
        self.handle_response(event)

    def new_distribution(self):
        # insert the next send event
        t = self._simulator.tc + Time(sec=1 / self.send_rate)
        event = func_to_event(t, self.new_distribution, by=self)
        self._simulator.add_event(event)
        log.debug(f"{self.own}: start new request")

        # generate new entanglement
        epr = self.generate_qubit(self.own, self.dst, None)
        log.debug(f"{self.own}: generate epr {epr.name}")

        self.state[epr.transmit_id] = Transmit(
            id=epr.transmit_id,
            src=self.own,
            dst=self.dst,
            second_epr_name=epr.name)

        log.debug(f"{self.own}: generate transmit {self.state[epr.transmit_id]}")
        if not self.memory.write(epr):
            self.memory.read(epr)
            self.state[epr.transmit_id] = None
        self.send_count += 1
        self.request_distrbution(epr.transmit_id)

    def request_distrbution(self, transmit_id: str):
        transmit = self.state.get(transmit_id)
        if transmit is None:
            return
        epr_name = transmit.second_epr_name
        epr = self.memory.get(epr_name)
        if epr is None:
            return

        dst = transmit.dst
        # get next hop
        route_result = self.net.query_route(self.own, dst)
        try:
            next_hop: QNode = route_result[0][1]
        except IndexError:
            raise Exception("Route error")

        qchannel: QuantumChannel = self.own.get_qchannel(next_hop)
        if qchannel is None:
            raise Exception("No such quantum channel")

        # send the entanglement
        log.debug(f"{self.own}: send epr {epr.name} to {next_hop}")
        qchannel.send(epr, next_hop)

    def response_distribution(self, packet: RecvQubitPacket):
        qchannel: QuantumChannel = packet.qchannel
        from_node: QNode = qchannel.node_list[0] \
            if qchannel.node_list[1] == self.own else qchannel.node_list[1]

        cchannel: ClassicChannel = self.own.get_cchannel(from_node)
        if cchannel is None:
            raise Exception("No such classic channel")

        # receive the first epr
        epr: WernerStateEntanglement = packet.qubit
        log.debug(f"{self.own}: recv epr {epr.name} from {from_node}")

        # generate the second epr
        next_epr = self.generate_qubit(
            src=epr.src, dst=epr.dst, transmit_id=epr.transmit_id)
        log.debug(f"{self.own}: generate epr {next_epr.name}")
        self.state[epr.transmit_id] = Transmit(
            id=epr.transmit_id,
            src=epr.src,
            dst=epr.dst,
            first_epr_name=epr.name,
            second_epr_name=next_epr.name)
        log.debug(
            f"{self.own}: generate transmit {self.state[epr.transmit_id]}")

        log.debug(f"{self.own}: store {epr.name} and {next_epr.name}")
        ret1 = self.memory.write(epr)
        ret2 = self.memory.write(next_epr)
        if not ret1 or not ret2:
            log.debug(f"{self.own}: store fail, destory {epr} and {next_epr}")
            # if failed (memory is full), destory all entanglements
            self.memory.read(epr)
            self.memory.read(next_epr)
            classic_packet = ClassicPacket(
                msg={"cmd": "revoke", "transmit_id": epr.transmit_id}, src=self.own, dest=from_node)
            cchannel.send(classic_packet, next_hop=from_node)
            log.debug(f"{self.own}: send {classic_packet.msg} to {from_node}")
            return

        classic_packet = ClassicPacket(
            msg={"cmd": "swap", "transmit_id": epr.transmit_id}, src=self.own, dest=from_node)
        cchannel.send(classic_packet, next_hop=from_node)
        log.debug(
            f"{self.own}: send {classic_packet.msg} from {self.own} to {from_node}")

    def handle_response(self, packet: RecvClassicPacket):
        msg = packet.packet.get()
        cchannel = packet.cchannel

        from_node: QNode = cchannel.node_list[0] \
            if cchannel.node_list[1] == self.own else cchannel.node_list[1]

        log.debug(f"{self.own}: recv {msg} from {from_node}")

        cmd = msg["cmd"]
        transmit_id = msg["transmit_id"]
        transmit = self.state.get(transmit_id)

        if cmd == "swap":
            if self.own != transmit.src:
                # perfrom entanglement swapping
                first_epr: WernerStateEntanglement = self.memory.read(
                    transmit.first_epr_name)
                second_epr: WernerStateEntanglement = self.memory.read(
                    transmit.second_epr_name)
                #change code
                #Check fidelitu before swapping
                if first_epr.fidelity < 0.7 or second_epr.fidelity < 0.7:
                    #Inroduce probability of decoherence based on fidelity
                    print("test")
                    decoherence_probability = 1 - min(first_epr.fidelity, second_epr.fidelity) / 0.7
                    if get_rand() < decoherence_probability:
                        log.debug(f"{self.own}:Decoherence occurred, revoking entanglement.")
                        self.revoke_entanglement(transmit, from_node, cchannel)
                        self.restart_request(transmit)
                        return
                #
                new_epr = first_epr.swapping(second_epr, name=uuid.uuid4().hex)
                log.debug(
                    f"{self.own}:perform swap use {first_epr} and {second_epr}")
                log.debug(f"{self.own}:perform swap generate {new_epr}")

                src: QNode = transmit.src
                app: EntanglementDistributionApp = src.get_apps(
                    EntanglementDistributionApp)[0]
                app.set_second_epr(new_epr, transmit_id=transmit_id)

                app: EntanglementDistributionApp = from_node.get_apps(
                    EntanglementDistributionApp)[0]
                app.set_first_epr(new_epr, transmit_id=transmit_id)

            classic_packet = ClassicPacket(
                msg={"cmd": "next", "transmit_id": transmit_id}, src=self.own, dest=from_node)
            cchannel.send(classic_packet, next_hop=from_node)
            log.debug(f"{self.own}: send {classic_packet.msg} to {from_node}")
        elif cmd == "next":
            # finish or request to the next hop
            if self.own == transmit.dst:
                result_epr = self.memory.read(transmit.first_epr_name)
                self.memory.read(transmit.second_epr_name)
                self.success.append(result_epr)
                self.state[transmit_id] = None
                self.success_count += 1
                log.debug(f"{self.own}: successful distribute {result_epr}")

                classic_packet = ClassicPacket(
                    msg={"cmd": "succ", "transmit_id": transmit_id},
                    src=self.own, dest=transmit.src)
                cchannel = self.own.get_cchannel(transmit.src)
                if cchannel is not None:
                    log.debug(
                        f"{self.own}: send {classic_packet} to {from_node}")
                    cchannel.send(classic_packet, next_hop=transmit.src)
            else:
                log.debug(f"{self.own}: begin new request {transmit_id}")
                self.request_distrbution(transmit_id)
        elif cmd == "succ":
            # the source notice that entanglement distribution is succeed.
            result_epr = self.memory.read(transmit.second_epr_name)
            log.debug(f"{self.own}: recv success distribution {result_epr}")
            self.state[transmit_id] = None
            self.success_count += 1
        elif cmd == "revoke":
            # clean memory
            log.debug(
                f"{self.own}: clean memory {transmit.first_epr_name}\
                    and {transmit.second_epr_name}")
            self.memory.read(transmit.first_epr_name)
            self.memory.read(transmit.second_epr_name)
            self.state[transmit_id] = None
            if self.own != transmit.src:
                classic_packet = ClassicPacket(
                    msg={"cmd": "revoke", "transmit_id": transmit_id},
                    src=self.own, dest=transmit.src)
                cchannel = self.own.get_cchannel(transmit.src)
                if cchannel is not None:
                    log.debug(
                        f"{self.own}: send {classic_packet} to {from_node}")
                    cchannel.send(classic_packet, next_hop=transmit.src)

    def generate_qubit(self, src: QNode, dst: QNode,
                       transmit_id: Optional[str] = None) -> QuantumModel:
        epr = WernerStateEntanglement(
            fidelity=self.init_fidelity, name=uuid.uuid4().hex)
        epr.src = src
        epr.dst = dst
        epr.transmit_id = transmit_id if transmit_id is not None else uuid.uuid4().hex
        return epr

    def set_first_epr(self, epr: QuantumModel, transmit_id: str):
        transmit = self.state.get(transmit_id, None)
        if transmit is None or transmit.first_epr_name is None:
            return
        self.memory.read(transmit.first_epr_name)
        self.memory.write(epr)
        transmit.first_epr_name = epr.name

    def set_second_epr(self, epr: QuantumModel, transmit_id: str):
        transmit = self.state.get(transmit_id, None)
        if transmit is None or transmit.second_epr_name is None:
            return
        self.memory.read(transmit.second_epr_name)
        self.memory.write(epr)
        transmit.second_epr_name = epr.name
