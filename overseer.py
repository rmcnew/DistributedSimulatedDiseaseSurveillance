import logging

from config.sds_config import get_overseer_config
from helpers.overseer_helper import setup_zmq, all_registrations_completed, handle_node_registration_request, \
    publish_node_addresses, all_nodes_ready, handle_node_ready_request

# get configuration and setup overseer listening
config = get_overseer_config()
logging.basicConfig(level=logging.DEBUG,
                    # filename='overseer.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug("overseer configuration: {}".format(config))
(context, reply_socket, publish_socket) = setup_zmq(config)


# map of Node_Id => IP Address:Port used for address registration
node_addresses = {}

# set of nodes that are ready to start the simulation
nodes_ready_to_start = set()


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

# register Ctrl-C handler to do clean shutdown of all nodes

# wait for Ctrl-C

# supervise shutdown and report collection from all nodes

# print summary report
