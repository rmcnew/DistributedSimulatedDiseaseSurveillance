from config.sds_config import get_overseer_config
from config.simulation_phases import get_simulation_phase
from overseer_admin import setup_zmq, send_to_node, receive_from_nodes, all_registrations_completed, \
                           handle_node_registration_request
import logging

config = get_overseer_config()
logging.basicConfig(level=logging.DEBUG,
                    # filename='overseer.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug(config)

simulation_phase_index = 0
simulation_phase = get_simulation_phase(simulation_phase_index)
(context, socket) = setup_zmq(config)


# Register all nodes
node_addresses = {}  # map of Node_Id => IP Address:Port

while simulation_phase == 'REGISTER':
    handle_node_registration_request(socket, node_addresses)
    if all_registrations_completed(config, node_addresses):
        simulation_phase_index = simulation_phase_index + 1
        simulation_phase = get_simulation_phase(simulation_phase_index)
logging.debug(node_addresses)


