from pox.core import core
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

class LearningSwitch(object):
    def __init__(self, connection):
        self.connection = connection
        self.mac_to_port = {}

        connection.addListeners(self)

    def _handle_PacketIn(self, event):
        packet = event.parsed
        in_port = event.port

        # Learn MAC address
        self.mac_to_port[packet.src] = in_port

        if packet.dst in self.mac_to_port:
            out_port = self.mac_to_port[packet.dst]

            msg = of.ofp_flow_mod()
            msg.match = of.ofp_match.from_packet(packet, in_port)
            msg.actions.append(of.ofp_action_output(port=out_port))
            self.connection.send(msg)

            log.info("Installing flow: %s -> %s", packet.src, packet.dst)

        else:
            msg = of.ofp_packet_out()
            msg.data = event.ofp
            msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
            msg.in_port = in_port
            self.connection.send(msg)

            log.info("Flooding packet")

def launch():
    def start_switch(event):
        log.info("Custom L2 Learning Switch Started")
        LearningSwitch(event.connection)

    core.openflow.addListenerByName("ConnectionUp", start_switch)
