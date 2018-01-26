import logging

import zmq


# electronic_medical_record nodes connect to health_district_system nodes
# using REQ sockets; they have no listeners and do not provide a listener address
# nevertheless, they register so the overseer knows that they are ready to receive
# peer addresses
def setup_listeners(config):
    config['address_map'] = {'role': config['role']}


# shutdown listeners that were created in setup_listeners
def shutdown_listeners():
    pass


# each electronic_medical_record connects to a single health_district_system node
def connect_to_peers(context, config, node_addresses):
    # get node_id for the connection that needs to be made from config
    connection_node_id = config['connections'][0]
    logging.debug("Connecting to node_id: {}".format(connection_node_id))
    # get the connection address from node_addresses
    connection_node_address = node_addresses[connection_node_id]['electronic_medical_record_address']
    logging.debug("Found node_id {} address as: {}".format(connection_node_id, connection_node_address))
    # create the REQ socket and connect
    health_district_system_socket = context.socket(zmq.REQ)
    health_district_system_socket.connect(connection_node_address)
    return health_district_system_socket


# close connections to peer nodes
def disconnect_from_peers(health_district_system_socket):
    health_district_system_socket.close(linger=2)
