import logging

import zmq

from helpers.node_helper import get_my_ip


# disease_outbreak_analyzer nodes use PUB listeners to publish
# disease outbreak alerts to health_district_systems
def setup_listeners(context, config):
    # create listener zmq sockets and save IP address and ports in config
    my_ip_address = get_my_ip()
    health_district_system_socket = context.socket(zmq.PUB)
    health_district_system_port = health_district_system_socket.bind_to_random_port("tcp://*")
    config['address_map'] = {
        'role': config['role'],
        'health_district_system_address': "tcp://" + my_ip_address + ":" + str(health_district_system_port)
    }
    return health_district_system_socket


# each disease_outbreak_analyzer connects subscription sockets to each health_district_system node
def connect_to_peers(context, config, node_id, node_addresses):
    health_district_system_sockets = {}
    # get the node_id's for connections to be made with health_district_system nodes
    connection_node_ids = config['connections']
    logging.debug("Connecting to node_id's: {}".format(connection_node_ids))
    for connection_node_id in connection_node_ids:
        # get the connection addresses
        connection_node_address = node_addresses[connection_node_id]['disease_outbreak_analyzer_address']
        health_district_system_socket = context.socket(zmq.SUB)
        health_district_system_socket.connect(connection_node_address)
        # empty string filter => receive all messages
        health_district_system_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        health_district_system_sockets[connection_node_id] = health_district_system_socket
    return health_district_system_sockets
