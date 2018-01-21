from config.sds_config import get_node_config
from config.simulation_phases import get_simulation_phase
from node_admin import setup_zmq, send_to_overseer, receive_from_overseer

config = get_node_config("health_district_system")
node_id = config['node_id']
# print(config)
simulation_phase_index = 0
simulation_phase = get_simulation_phase(simulation_phase_index)

(context, overseer_socket) = setup_zmq(config)