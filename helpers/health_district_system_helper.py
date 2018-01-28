import logging

import zmq

from helpers.node_helper import get_my_ip
from vector_timestamp import increment_my_vector_timestamp_count, update_my_vector_timestamp

# health_district_system nodes use REP listeners to receive
# electronic_medical_record messages and PUB listeners to publish
# messages to disease_outbreak_analyzers
def setup_listeners(context, config):
    # create listener zmq sockets and save IP address and ports in config
    my_ip_address = get_my_ip()
    electronic_medical_record_socket = context.socket(zmq.REP)
    electronic_medical_record_port = electronic_medical_record_socket.bind_to_random_port("tcp://*")
    disease_count_publisher_socket = context.socket(zmq.PUB)
    disease_count_publisher_port = disease_count_publisher_socket.bind_to_random_port("tcp://*")
    config['address_map'] = {
        'role': config['role'],
        'electronic_medical_record_address': "tcp://" + my_ip_address + ":" + str(electronic_medical_record_port),
        'disease_outbreak_analyzer_address': "tcp://" + my_ip_address + ":" + str(disease_count_publisher_port)
    }
    ret_val = (electronic_medical_record_socket, disease_count_publisher_socket)
    return ret_val


# shutdown listeners that were created in setup_listeners
def shutdown_listeners(electronic_medical_record_socket, disease_count_publisher_socket):
    electronic_medical_record_socket.close(linger=2)
    disease_count_publisher_socket.close(linger=2)


# each health_district_system connects subscription sockets to each disease_outbreak_analyzer node
def connect_to_peers(context, config, node_addresses):
    disease_outbreak_alert_subscription_sockets = {}
    # get the node_id's for connections to be made with disease_outbreak_analyzers
    connection_node_ids = config['connections']
    logging.debug("Connecting to node_id's: {}".format(connection_node_ids))
    for connection_node_id in connection_node_ids:
        # get the connection addresses
        connection_node_address = node_addresses[connection_node_id]['health_district_system_address']
        disease_outbreak_alert_subscription_socket = context.socket(zmq.SUB)
        disease_outbreak_alert_subscription_socket.connect(connection_node_address)
        # empty string filter => receive all messages
        disease_outbreak_alert_subscription_socket.setsockopt_string(zmq.SUBSCRIBE, '')
        disease_outbreak_alert_subscription_sockets[connection_node_id] = disease_outbreak_alert_subscription_socket
    return disease_outbreak_alert_subscription_sockets


def disconnect_from_peers(disease_outbreak_alert_subscription_sockets):
    for socket in disease_outbreak_alert_subscription_sockets.values():
        socket.close(linger=2)


def handle_disease_notification(message):
    pass


def handle_electronic_medical_record_request(electronic_medical_record_socket, node_id, my_vector_timestamp):
    message = electronic_medical_record_socket.recv_pyobj()
    logging.debug("Received message: {}".format(message))
    increment_my_vector_timestamp_count(my_vector_timestamp, node_id)
    if message['message_type'] == 'disease_notification':
        handle_disease_notification(message)
        disease_notification_vector_timestamp = message['vector_timestamp']
        update_my_vector_timestamp(my_vector_timestamp, disease_notification_vector_timestamp)
        reply = {'message_type': "disease_notification_reply",
                 'status': "received",
                 'vector_timestamp': my_vector_timestamp}
        logging.debug("Sending reply: {}".format(reply))
        electronic_medical_record_socket.send_pyobj(reply)

    elif message['message_type'] == 'daily_disease_count_report':
        pass

    elif message['message_type'] == 'past_seven_days_disease_count_report':
        pass

    elif message['message_type'] == 'outbreak_query':
        pass

    else:
        logging.warning("Unknown message_type: {} received from node_id: {}"
                        .format(message['message_type'], message['electronic_medical_record_id']))