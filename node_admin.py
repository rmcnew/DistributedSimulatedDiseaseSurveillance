# administrative coordination between nodes and overseer -- node functions
import socket
import zmq
import json
import logging

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('192.0.0.8', 1027))
    except socket.error:
        return None
    return s.getsockname()[0]


def setup_zmq(config):
    context = zmq.Context()
    overseer_socket = context.socket(zmq.REQ)
    overseer_socket.connect("tcp://" + config['overseer_host'] + ":" + str(config['overseer_port']))
    ret_val = (context, overseer_socket)
    return ret_val


def shutdown_zmq(context, overseer_socket):
    overseer_socket.close()
    context.term()


def send_to_overseer(overseer_socket, node_id, message):
    logging.info("Sending message: \'" + message + "\' from: \'" + node_id + "\'")
    encoded_node_id = node_id.encode()
    encoded_message = message.encode()
    overseer_socket.send_multipart([encoded_node_id, encoded_message])


def receive_from_overseer(overseer_socket, node_id):
    while True:
        [encoded_destination_node_id, encoded_reply] = overseer_socket.recv_multipart()
        destination_node_id = encoded_destination_node_id.decode()
        reply = encoded_reply.decode()
        if (node_id == destination_node_id) or ("ALL" == destination_node_id):
            return reply


def register_request(overseer_socket, node_id, config):
    logging.info(str(node_id) + " registering with Overseer")
    serialized_address_map = json.dumps(config['address_map'])
    send_to_overseer(overseer_socket, node_id, serialized_address_map)


def register_reply(overseer_socket, node_id):
    reply = receive_from_overseer(overseer_socket, node_id)
    logging.info(reply)


# electronic_medical_record nodes connect to health_district_system nodes
# using REQ sockets; they have no listeners and do not provide a listener address
# nevertheless, they register so the overseer knows that their respective node_id is ready
def setup_electronic_medical_record_zmq_listeners(config):
    config['address_map'] = {'role': config['role']}


# health_district_system nodes use REP listeners to receive
# electronic_medical_record messages and PUB listeners to publish
# messages to disease_outbreak_analyzers
def setup_health_district_system_zmq_listeners(context, config):
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


# disease_outbreak_analyzer nodes use PUB listeners to publish
# disease outbreak alerts to health_district_systems
def setup_disease_outbreak_analyzer_zmq_listeners(context, config):
    # create listener zmq sockets and save IP address and ports in config
    my_ip_address = get_my_ip()
    health_district_system_socket = context.socket(zmq.PUB)
    health_district_system_port = health_district_system_socket.bind_to_random_port("tcp://*")
    config['address_map'] = {
        'role': config['role'],
        'health_district_system_address': "tcp://" + my_ip_address + ":" + str(health_district_system_port)
    }
    return health_district_system_socket
