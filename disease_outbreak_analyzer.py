import logging

import zmq

from config.sds_config import get_node_config
from helpers.disease_outbreak_analyzer_helper import setup_listeners, connect_to_peers
from helpers.node_helper import setup_zmq, register, receive_node_addresses, send_ready_to_start, await_simulation_start

# get configuration and setup overseer connection
config = get_node_config("disease_outbreak_analyzer")
node_id = config['node_id']
logging.basicConfig(level=logging.DEBUG,
                    # filename='disease_outbreak_analyzer-' + node_id + '.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug(config)
(context, overseer_request_socket, overseer_subscribe_socket) = setup_zmq(config)

# setup listening sockets
disease_outbreak_alert_publisher_socket = setup_listeners(context, config)

# register listener addresses with overseer
register(overseer_request_socket, node_id, config)

# get node_addresses from overseer and make peer connections
node_addresses = receive_node_addresses(overseer_subscribe_socket)
logging.debug("node_addresses received from overseer: {}".format(node_addresses))

# make peer connections
disease_count_subscription_sockets = connect_to_peers(context, config, node_id, node_addresses)

# send "ready_to_start" message to overseer
send_ready_to_start(overseer_request_socket, node_id)

# await "start_simulation" message from overseer
while await_simulation_start(overseer_subscribe_socket):
    pass  # do nothing until "simulation_start" is received

# configure main loop poller
poller = zmq.Poller()
poller.register(overseer_subscribe_socket, zmq.POLLIN)
for disease_count_subscription_socket in disease_count_subscription_sockets.values():
    poller.register(disease_count_subscription_socket)
