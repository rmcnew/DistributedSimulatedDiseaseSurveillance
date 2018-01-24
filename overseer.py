from config.sds_config import get_overseer_config
from overseer_admin import setup_zmq, all_registrations_completed, handle_node_registration_request, \
                           broadcast_node_addresses
import logging

# get configuration and setup overseer listening
config = get_overseer_config()
logging.basicConfig(level=logging.DEBUG,
                    # filename='overseer.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug("overseer configuration: {}".format(config))
(context, reply_socket, publish_socket) = setup_zmq(config)


# map of Node_Id => IP Address:Port used for address registration
node_addresses = {}

# register all nodes
while not all_registrations_completed(config, node_addresses):
    handle_node_registration_request(reply_socket, node_addresses)
logging.debug("registered node_addresses: {}".format(node_addresses))

# connect to all nodes and send node_addresses to all nodes
broadcast_node_addresses(publish_socket, node_addresses)





