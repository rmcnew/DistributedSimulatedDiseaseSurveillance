import logging

import zmq

from config.sds_config import get_node_config
from helpers.disease_outbreak_analyzer_helper import setup_listeners, connect_to_peers, disconnect_from_peers, \
    shutdown_listeners
from helpers.node_helper import setup_zmq, register, receive_node_addresses, send_ready_to_start, \
    await_start_simulation, is_stop_simulation, shutdown_zmq

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
disease_count_subscription_sockets = connect_to_peers(context, config, node_addresses)

# send "ready_to_start" message to overseer
send_ready_to_start(overseer_request_socket, node_id)

# await "start_simulation" message from overseer
while await_start_simulation(overseer_subscribe_socket):
    pass  # do nothing until "simulation_start" is received

# configure main loop poller
logging.info("Configuring main loop poller")
poller = zmq.Poller()
poller.register(overseer_subscribe_socket, zmq.POLLIN)
for disease_count_subscription_socket in disease_count_subscription_sockets.values():
    poller.register(disease_count_subscription_socket)

# main loop
logging.info("Starting simulation main loop")
run_simulation = True
while run_simulation:
    try:
        sockets = dict(poller.poll(700))  # poll timeout in milliseconds
    except KeyboardInterrupt:
        break

    for socket, event in sockets.items():
        if socket == overseer_subscribe_socket:
            if is_stop_simulation(overseer_subscribe_socket):
                logging.info("received simulation_stop")
                run_simulation = False
                break

        if socket in disease_count_subscription_sockets:
            # handle disease count report 
            pass

# shutdown procedures
logging.info("Shutting down . . .")
disconnect_from_peers(disease_count_subscription_sockets)
shutdown_listeners(disease_outbreak_alert_publisher_socket)
shutdown_zmq(context, overseer_request_socket, overseer_subscribe_socket)
