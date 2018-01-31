import logging
from random import random

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


def send_disease_notification(health_district_system_socket, node_id, disease, local_timestamp, my_vector_timestamp):
    message = {'message_type': "disease_notification",
               'electronic_medical_record_id': node_id,
               'disease': disease,
               'local_timestamp': local_timestamp,
               'vector_timestamp': my_vector_timestamp}
    logging.debug("Sending disease notification: {}".format(message))
    health_district_system_socket.send_pyobj(message)
    reply = health_district_system_socket.recv_pyobj()
    logging.debug("Received reply: {}".format(reply))
    reply_vector_timestamp = reply['vector_timestamp']
    my_vector_timestamp.update_my_vector_timestamp(reply_vector_timestamp)


# generate disease occurrences using the pseudorandom number generator:
# probability threshold parameter is 0.0 <= x <= 1.0 where 0.0 means a disease occurrence cannot happen and 1.0 means a
# disease occurrence will happen each time
def generate_disease_random(probability_threshold):
    if (probability_threshold < 0.0) or (probability_threshold > 1.0):
        raise TypeError("probability_threshold out of range 0.0 <= x <= 1.0")
    # roll the PRNG to get a pseudorandom number
    random_number = random()
    return random_number < probability_threshold


def generate_disease(config):
    role_parameters = config['role_parameters']
    if role_parameters['disease_generation'] == "random":
        disease_generation_parameters = role_parameters['disease_generation_parameters']
        probability = disease_generation_parameters['probability']
        return generate_disease_random(probability)


def send_outbreak_query(health_district_system_socket, node_id, my_vector_timestamp):
    message = {'message_type': "outbreak_query",
               'electronic_medical_record_id': node_id,
               'vector_timestamp': my_vector_timestamp}
    logging.debug("Sending outbreak query: {}".format(message))
    health_district_system_socket.send_pyobj(message)
    reply = health_district_system_socket.recv_pyobj()
    logging.debug("Received reply: {}".format(reply))
    reply_vector_timestamp = reply['vector_timestamp']
    my_vector_timestamp.update_my_vector_timestamp(reply_vector_timestamp)
    outbreaks = reply['outbreaks']
    for disease in outbreaks:
        logging.info("*** ALERT *** {} outbreak reported!  Take appropriate precautions and advise patients."
                     .format(disease))
