# administrative coordination between nodes and overseer -- overseer functions
import zmq
import logging
import time
import json


def setup_zmq(config):
    context = zmq.Context()
    reply_socket = context.socket(zmq.REP)
    reply_socket.bind("tcp://*:" + str(config['overseer_reply_port']))
    publish_socket = context.socket(zmq.PUB)
    publish_socket.bind("tcp://*:" + str(config['overseer_publish_port']))
    ret_val = (context, reply_socket, publish_socket)
    return ret_val


def shutdown_zmq(context, reply_socket, publish_socket):
    reply_socket.close()
    publish_socket.close()
    context.term()


def send_to_node(socket, node_id, message):
    encoded_node_id = node_id.encode()
    encoded_message = message.encode()
    socket.send_multipart([encoded_node_id, encoded_message])


def receive_from_nodes(reply_socket):
    [encoded_node_id, encoded_reply] = reply_socket.recv_multipart()
    node_id = encoded_node_id.decode()
    reply = encoded_reply.decode()
    ret_val = (node_id, reply)
    return ret_val


def all_registrations_completed(config, node_addresses):
    if len(config['nodes']) == len(node_addresses):
        return True
    else:
        return False


def handle_node_registration_request(reply_socket, node_addresses):
    (node_id, message) = receive_from_nodes(reply_socket)
    logging.debug("Received message: \'" + message + "\' from: \'" + node_id + "\'")
    address_map = json.loads(message)
    node_role = address_map['role']
    if (node_role == "electronic_medical_record") or \
       (node_role == "health_district_system") or \
       (node_role == "disease_outbreak_analyzer"):

        node_addresses[node_id] = address_map
        logging.debug("Registration received for " + node_id + ", role: " + node_role)

    else:
        logging.error("Unknown node role: " + node_role + ".  No configuration for this node role!!")

    send_to_node(reply_socket, node_id, "Successful registration for " + node_id)


def broadcast_node_addresses(publish_socket, node_addresses):
    json_node_addresses = json.dumps(node_addresses)
    publish_socket.send_string(json_node_addresses)
