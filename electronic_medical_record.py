import logging

from config.sds_config import get_node_config
from helpers.electronic_medical_record_helper import setup_listeners, connect_to_peers
from helpers.node_helper import setup_zmq, register, receive_node_addresses, send_ready_to_start

# get configuration and setup overseer connection
config = get_node_config("electronic_medical_record")
node_id = config['node_id']
logging.basicConfig(level=logging.DEBUG,
                    # filename='electronic_medical_record-' + node_id + '.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug("electronic_medical_record configuration: {}".format(config))
(context, overseer_request_socket, overseer_subscribe_socket) = setup_zmq(config)

# setup listening sockets
setup_listeners(config)

# register listener addresses with overseer
register(overseer_request_socket, node_id, config)

# get node_addresses from overseer and make peer connections
node_addresses = receive_node_addresses(overseer_subscribe_socket)
logging.debug("node_addresses received from overseer: {}".format(node_addresses))

# make peer connections
health_district_system_socket = connect_to_peers(context, config, node_id, node_addresses)

# send "ready_to_start" message to overseer
send_ready_to_start(overseer_request_socket, node_id)
