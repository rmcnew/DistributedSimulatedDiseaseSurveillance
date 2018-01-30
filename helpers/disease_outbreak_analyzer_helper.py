import logging

import zmq

from helpers.node_helper import get_my_ip


# disease_outbreak_analyzer nodes use PUB listeners to publish
# disease outbreak alerts to health_district_systems
def setup_listeners(context, config):
    # create listener zmq sockets and save IP address and ports in config
    my_ip_address = get_my_ip()
    disease_outbreak_alert_publisher_socket = context.socket(zmq.PUB)
    disease_outbreak_alert_publisher_port = disease_outbreak_alert_publisher_socket.bind_to_random_port("tcp://*")
    config['address_map'] = {
        'role': config['role'],
        'health_district_system_address': "tcp://" + my_ip_address + ":" + str(disease_outbreak_alert_publisher_port)
    }
    return disease_outbreak_alert_publisher_socket


# shutdown listeners that were created in setup_listeners
def shutdown_listeners(disease_outbreak_alert_publisher_socket):
    disease_outbreak_alert_publisher_socket.close(linger=2)


# each disease_outbreak_analyzer connects subscription sockets to each health_district_system node
def connect_to_peers(context, config, node_addresses):
    disease_count_subscription_sockets = set()
    # get the node_id's for connections to be made with health_district_system nodes
    connection_node_ids = config['connections']
    logging.debug("Connecting to node_id's: {}".format(connection_node_ids))
    for connection_node_id in connection_node_ids:
        # get the connection addresses
        connection_node_address = node_addresses[connection_node_id]['disease_outbreak_analyzer_address']
        disease_count_subscription_socket = context.socket(zmq.SUB)
        disease_count_subscription_socket.connect(connection_node_address)
        # empty string filter => receive all messages
        disease_count_subscription_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        disease_count_subscription_sockets.add(disease_count_subscription_socket)
    return disease_count_subscription_sockets


# close connections to peer nodes
def disconnect_from_peers(disease_count_subscription_sockets):
    for socket in disease_count_subscription_sockets:
        socket.close(linger=2)
