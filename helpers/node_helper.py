# helper functions for all node types:  electronic_medical_record, health_district_system, and disease_outbreak_analyzer
import json
import logging
import socket
from datetime import datetime

import zmq

from vector_timestamp import update_my_vector_timestamp, increment_my_vector_timestamp_count


def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.0.8', 1027))
    except socket.error:
        return None
    return s.getsockname()[0]


def setup_zmq(config):
    context = zmq.Context()
    overseer_request_socket = context.socket(zmq.REQ)
    overseer_request_socket.connect("tcp://" + config['overseer_host'] + ":" + str(config['overseer_reply_port']))
    overseer_subscribe_socket = context.socket(zmq.SUB)
    overseer_subscribe_socket.connect("tcp://" + config['overseer_host'] + ":" + str(config['overseer_publish_port']))
    overseer_subscribe_socket.setsockopt_string(zmq.SUBSCRIBE, '')  # empty string filter => receive all messages
    ret_val = (context, overseer_request_socket, overseer_subscribe_socket)
    return ret_val


def shutdown_zmq(context, overseer_request_socket, overseer_subscribe_socket):
    overseer_request_socket.close(linger=2)
    overseer_subscribe_socket.close(linger=2)
    context.term()


def send_to_overseer(overseer_socket, node_id, message):
    logging.info("Sending message: \'" + message + "\' from: \'" + node_id + "\'")
    encoded_node_id = node_id.encode()
    encoded_message = message.encode()
    overseer_socket.send_multipart([encoded_node_id, encoded_message])


def receive_from_overseer(overseer_request_socket, node_id):
    while True:
        [encoded_destination_node_id, encoded_reply] = overseer_request_socket.recv_multipart()
        destination_node_id = encoded_destination_node_id.decode()
        reply = encoded_reply.decode()
        if node_id == destination_node_id:
            return reply


def receive_subscription_message(overseer_subscribe_socket):
    message = overseer_subscribe_socket.recv_string()
    return message


def register(overseer_request_socket, node_id, config):
    logging.info(str(node_id) + " registering with overseer")
    address_map = config['address_map']
    address_map['type'] = 'address_map'
    serialized_address_map = json.dumps(address_map)
    send_to_overseer(overseer_request_socket, node_id, serialized_address_map)
    reply = receive_from_overseer(overseer_request_socket, node_id)
    logging.info(reply)


def receive_node_addresses(overseer_subscribe_socket):
    json_node_addresses = receive_subscription_message(overseer_subscribe_socket)
    node_addresses = json.loads(json_node_addresses)
    return node_addresses


def send_ready_to_start(overseer_request_socket, node_id):
    message = "ready_to_start"  # the overseer checks this string for a match
    send_to_overseer(overseer_request_socket, node_id, message)
    reply = receive_from_overseer(overseer_request_socket, node_id)
    logging.info(reply)


def await_start_simulation(overseer_subscribe_socket):
    message = receive_subscription_message(overseer_subscribe_socket)
    if message == "start_simulation":
        return False
    else:
        logging.warning("received message: '" + message + "' while awaiting for simulation_start")
        return True


def is_stop_simulation(overseer_subscribe_socket):
    message = receive_subscription_message(overseer_subscribe_socket)
    if message == "stop_simulation":
        return True
    else:
        logging.warning("received message: '" + message + "' but no logic defined to handle it")
        return False


def get_start_time():
    return datetime.now()


def get_elapsed_time(start_time, time_scaling_factor):
    return (datetime.now() - start_time) * time_scaling_factor


def update_simulation_time(start_time, config):
    time_scaling_factor = config['time_scaling_factor']
    elapsed_time = get_elapsed_time(start_time, time_scaling_factor)
    sim_time = start_time + elapsed_time
    logging.debug("Time elapsed: {}  Simulation datetime: {}".format(elapsed_time, sim_time))
    ret_val = (elapsed_time, sim_time)
    return ret_val


# daily_disease_count handling for electronic_medical_record and health_district_system
def new_daily_disease_counts(config):
    daily_disease_counts = {'message_type': "daily_disease_count", config['role'] + '_id': config['node_id']}
    for disease in config['diseases']:
        daily_disease_counts[disease] = 0
    return daily_disease_counts


def send_daily_disease_counts_using_sockets(send_socket, config, current_daily_disease_counts, my_vector_timestamp):
    current_daily_disease_counts['vector_timestamp'] = my_vector_timestamp
    logging.debug("Sending daily disease counts: {}".format(current_daily_disease_counts))
    send_socket.send_pyobj(current_daily_disease_counts)
    if config['role'] == 'electronic_medical_record':
        reply = send_socket.recv_pyobj()
        logging.debug("Received reply: {}".format(reply))
        reply_vector_timestamp = reply['vector_timestamp']
        update_my_vector_timestamp(my_vector_timestamp, reply_vector_timestamp)


def archive_current_day(current_daily_disease_counts, previous_daily_disease_counts):
    logging.debug("Archiving current daily disease counts: {}".format(current_daily_disease_counts))
    previous_daily_disease_counts.append(current_daily_disease_counts)
    logging.debug("previous_daily_disease_counts is now: {}".format(previous_daily_disease_counts))


def get_elapsed_days(previous_daily_disease_counts):
    return len(previous_daily_disease_counts)


def send_daily_disease_counts(sending_socket, config, my_vector_timestamp, current_daily_disease_counts,
                              previous_daily_disease_counts, elapsed_time, sim_time):
    elapsed_days = get_elapsed_days(previous_daily_disease_counts)
    node_id = config['node_id']
    if elapsed_time.days > elapsed_days:
        current_daily_disease_counts['end_timestamp'] = sim_time
        increment_my_vector_timestamp_count(my_vector_timestamp, node_id)
        send_daily_disease_counts_using_sockets(sending_socket, config,
                                                current_daily_disease_counts, my_vector_timestamp)
        archive_current_day(current_daily_disease_counts, previous_daily_disease_counts)

        # reset current_daily_disease_counts
        current_daily_disease_counts = new_daily_disease_counts(config)
        current_daily_disease_counts['start_timestamp'] = sim_time
