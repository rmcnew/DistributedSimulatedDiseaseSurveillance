import logging

import zmq

from helpers.node_helper import get_my_ip, get_elapsed_days, archive_current_day
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
    disease_outbreak_alert_subscription_sockets = set()
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
        disease_outbreak_alert_subscription_sockets.add(disease_outbreak_alert_subscription_socket)
    return disease_outbreak_alert_subscription_sockets


def disconnect_from_peers(disease_outbreak_alert_subscription_sockets):
    for socket in disease_outbreak_alert_subscription_sockets:
        socket.close(linger=2)


def handle_disease_notification(message, current_daily_disease_counts):
    disease = message['disease']
    current_daily_disease_counts[disease] = current_daily_disease_counts[disease] + 1


def handle_electronic_medical_record_request(electronic_medical_record_socket,
                                             node_id, my_vector_timestamp,
                                             current_daily_disease_counts, outbreaks):
    message = electronic_medical_record_socket.recv_pyobj()
    # logging.debug("Received message: {}".format(message))
    increment_my_vector_timestamp_count(my_vector_timestamp, node_id)

    if message['message_type'] == 'disease_notification':
        handle_disease_notification(message, current_daily_disease_counts)
        disease_notification_vector_timestamp = message['vector_timestamp']
        update_my_vector_timestamp(my_vector_timestamp, disease_notification_vector_timestamp)
        reply = {'message_type': "disease_notification_reply",
                 'status': "received",
                 'vector_timestamp': my_vector_timestamp}
        # logging.debug("Sending reply: {}".format(reply))
        electronic_medical_record_socket.send_pyobj(reply)
        disease = message['disease']
        logging.debug("{} count is now {}".format(disease, current_daily_disease_counts[disease]))

    elif message['message_type'] == 'outbreak_query':
        outbreak_query_vector_timestamp = message['vector_timestamp']
        update_my_vector_timestamp(my_vector_timestamp, outbreak_query_vector_timestamp)
        reply = {'message_type': "outbreak_query_reply",
                 'outbreaks': outbreaks,
                 'vector_timestamp': my_vector_timestamp}
        logging.debug("Sending reply: {}".format(reply))
        electronic_medical_record_socket.send_pyobj(reply)

    else:
        logging.warning("Unknown message_type: {} received from node_id: {}"
                        .format(message['message_type'], message['electronic_medical_record_id']))


def handle_disease_outbreak_alert(socket, node_id, my_vector_timestamp, outbreaks):
    message = socket.recv_pyobj()
    logging.debug("Received outbreak alert message: {}".format(message))
    increment_my_vector_timestamp_count(my_vector_timestamp, node_id)
    disease_outbreak_alert_vector_timestamp = message['vector_timestamp']
    update_my_vector_timestamp(my_vector_timestamp, disease_outbreak_alert_vector_timestamp)
    outbreak_disease = message['disease']
    logging.info("*** ALERT *** {} outbreak detected!".format(outbreak_disease))
    outbreaks.add(outbreak_disease)


def new_daily_disease_counts(config):
    daily_disease_counts = {'message_type': "daily_disease_count", config['role'] + '_id': config['node_id']}
    for disease in config['diseases']:
        daily_disease_counts[disease] = 0
    return daily_disease_counts


def send_daily_disease_counts_using_sockets(send_socket, current_daily_disease_counts, my_vector_timestamp):
    current_daily_disease_counts['vector_timestamp'] = my_vector_timestamp
    logging.debug("Sending daily disease counts: {}".format(current_daily_disease_counts))
    send_socket.send_pyobj(current_daily_disease_counts)


def send_daily_disease_counts(sending_socket, config, my_vector_timestamp, current_daily_disease_counts,
                              previous_daily_disease_counts, elapsed_time, sim_time):
    elapsed_days = get_elapsed_days(previous_daily_disease_counts)
    node_id = config['node_id']
    # if the day is over, send the end-of-day counts, then reset the counts
    if elapsed_time.days > elapsed_days:
        current_daily_disease_counts['end_timestamp'] = sim_time
        increment_my_vector_timestamp_count(my_vector_timestamp, node_id)
        send_daily_disease_counts_using_sockets(sending_socket, current_daily_disease_counts, my_vector_timestamp)
        archive_current_day(current_daily_disease_counts, previous_daily_disease_counts)

        # reset current_daily_disease_counts
        current_daily_disease_counts = new_daily_disease_counts(config)
        current_daily_disease_counts['start_timestamp'] = sim_time

    else:  # otherwise, send the current counts if enough time has elapsed
        send_daily_disease_counts_using_sockets(sending_socket, current_daily_disease_counts, my_vector_timestamp)
