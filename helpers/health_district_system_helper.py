import logging

import zmq

from helpers.node_helper import get_my_ip


# health_district_system nodes use REP listeners to receive
# electronic_medical_record messages and PUB listeners to publish
# messages to disease_outbreak_analyzers
def setup_listeners(context, config):
    # create listener zmq sockets and save IP address and ports in config
    my_ip_address = get_my_ip()
    electronic_medical_record_socket = context.socket(zmq.REP)
    electronic_medical_record_port = electronic_medical_record_socket.bind_to_random_port("tcp://*")
    disease_outbreak_analyzer_socket = context.socket(zmq.PUB)
    disease_outbreak_analyzer_port = disease_outbreak_analyzer_socket.bind_to_random_port("tcp://*")
    config['address_map'] = {
        'role': config['role'],
        'electronic_medical_record_address': "tcp://" + my_ip_address + ":" + str(electronic_medical_record_port),
        'disease_outbreak_analyzer_address': "tcp://" + my_ip_address + ":" + str(disease_outbreak_analyzer_port)
    }
    ret_val = (electronic_medical_record_socket, disease_outbreak_analyzer_socket)
    return ret_val


# each health_district_system connects subscription sockets to each disease_outbreak_analyzer node
def connect_to_peers(context, config, node_id, node_addresses):
    disease_outbreak_analyzer_sockets = {}
    # get the node_id's for connections to be made with disease_outbreak_analyzers
    connection_node_ids = config['connections']
    logging.debug("Connecting to node_id's: {}".format(connection_node_ids))
    for connection_node_id in connection_node_ids:
        # get the connection addresses
        connection_node_address = node_addresses[connection_node_id]['health_district_system_address']
        disease_outbreak_analyzer_socket = context.socket(zmq.SUB)
        disease_outbreak_analyzer_socket.connect(connection_node_address)
        # empty string filter => receive all messages
        disease_outbreak_analyzer_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        disease_outbreak_analyzer_sockets[connection_node_id] = disease_outbreak_analyzer_socket
    return disease_outbreak_analyzer_sockets
