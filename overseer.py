from config.sds_config import get_overseer_config
from config.simulation_phases import get_simulation_phase
from overseer_admin import setup_zmq, send_to_node, receive_from_nodes
import time

config = get_overseer_config()
simulation_phase_index = 0
simulation_phase = get_simulation_phase(0)

# print(config)

(context, socket) = setup_zmq(config)
while True:
    (node_id, message) = receive_from_nodes(socket)
    print("Received message: \'" + message + "\' from: \'" + node_id + "\'")
    time.sleep(1)
    send_to_node(socket, node_id, "Received")

