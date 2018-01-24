# helper functions for all node types:  electronic_medical_record, health_district_system, and disease_outbreak_analyzer
import json
import logging
import socket

import zmq


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


def shutdown_zmq(context, overseer_socket):
    overseer_socket.close()
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
