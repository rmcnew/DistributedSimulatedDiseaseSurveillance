from config.sds_config import get_node_config
from config.simulation_phases import get_simulation_phase
from node_admin import setup_zmq, setup_disease_outbreak_analyzer_zmq_listeners, register_request, register_reply
import logging

config = get_node_config("disease_outbreak_analyzer")
node_id = config['node_id']
logging.basicConfig(level=logging.INFO,
                    # filename='disease_outbreak_analyzer-' + node_id + '.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug(config)
simulation_phase_index = 0
simulation_phase = get_simulation_phase(simulation_phase_index)

(context, overseer_socket) = setup_zmq(config)
health_district_system_socket = setup_disease_outbreak_analyzer_zmq_listeners(context, config)

# Register listener addresses with Overseer
register_request(overseer_socket, node_id, config)
register_reply(overseer_socket, node_id)


