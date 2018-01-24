import logging

from config.sds_config import get_overseer_config
from helpers.overseer_helper import setup_zmq, all_registrations_completed, handle_node_registration_request, \
    publish_node_addresses, all_nodes_ready, handle_node_ready_request, publish_start_simulation, receive_from_nodes, \
    publish_stop_simulation, shutdown_zmq

# get configuration and setup overseer listening
config = get_overseer_config()
logging.basicConfig(level=logging.DEBUG,
                    # filename='overseer.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug("overseer configuration: {}".format(config))
(context, reply_socket, publish_socket) = setup_zmq(config)

# map of node_id => ip_address:port used for address registration
node_addresses = {}

# set of nodes that are ready to start the simulation
nodes_ready_to_start = set()

# node heartbeat tracking:  map of node_id => last_heartbeat_received
node_heartbeats = {}  # TODO: add node heartbeat sending and overseer alert trigger if no heartbeat received

# register all nodes
while not all_registrations_completed(config, node_addresses):
    handle_node_registration_request(reply_socket, node_addresses)
logging.debug("registered node_addresses: {}".format(node_addresses))

# publish node_addresses to all nodes
publish_node_addresses(publish_socket, node_addresses)

# wait for all nodes to connect to peers and then send "Ready" message
while not all_nodes_ready(config, nodes_ready_to_start):
    handle_node_ready_request(reply_socket, nodes_ready_to_start)
logging.debug("all nodes are ready to start.  Starting the simulation . . .")

# publish "start_simulation" message to all nodes
publish_start_simulation(publish_socket)

# main simulation run loop
while True:
    try:
        # TODO: add heartbeat handling here
        (node_id, reply) = receive_from_nodes(reply_socket)
    except KeyboardInterrupt:  # wait for Ctrl-C to exit main simulation run loop
        break

# publish "stop_simulation" message to all nodes
publish_stop_simulation(publish_socket)

# supervise shutdown and report collection from all nodes

# print summary report

# shutdown
shutdown_zmq(context, reply_socket, publish_socket)
