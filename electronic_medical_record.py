import logging

import zmq

from config.sds_config import get_node_config
from helpers.electronic_medical_record_helper import setup_listeners, connect_to_peers, disconnect_from_peers, \
    shutdown_listeners, generate_disease, send_disease_notification
from helpers.node_helper import setup_zmq, register, receive_node_addresses, send_ready_to_start, \
    await_start_simulation, is_stop_simulation, shutdown_zmq, get_start_time, get_elapsed_time
from vector_timestamp import new_vector_timestamp, increment_my_vector_timestamp_count, update_my_vector_timestamp


# get configuration and setup overseer connection
config = get_node_config("electronic_medical_record")
node_id = config['node_id']
logging.basicConfig(level=logging.DEBUG,
                    # filename='electronic_medical_record-' + node_id + '.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug("electronic_medical_record configuration: {}".format(config))
(context, overseer_request_socket, overseer_subscribe_socket) = setup_zmq(config)

# setup listening sockets
setup_listeners(config)

# register listener addresses with overseer
register(overseer_request_socket, node_id, config)

# get node_addresses from overseer and make peer connections
node_addresses = receive_node_addresses(overseer_subscribe_socket)
logging.debug("node_addresses received from overseer: {}".format(node_addresses))

# make peer connections
health_district_system_socket = connect_to_peers(context, config, node_addresses)

# configure main loop poller and get time_scaling_factor
logging.info("Configuring main loop poller")
poller = zmq.Poller()
poller.register(overseer_subscribe_socket, zmq.POLLIN)
poller.register(health_district_system_socket, zmq.POLLIN)
time_scaling_factor = config['time_scaling_factor']

# initialize vector_timestamp
my_vector_timestamp = new_vector_timestamp()

# send "ready_to_start" message to overseer
send_ready_to_start(overseer_request_socket, node_id)

# await "start_simulation" message from overseer
while await_start_simulation(overseer_subscribe_socket):
    pass  # do nothing until "simulation_start" is received

# main loop
logging.info("Starting simulation main loop")
run_simulation = True
start_time = get_start_time()
while run_simulation:
    # poll sockets and handle incoming messages
    try:
        sockets = dict(poller.poll(700))  # poll timeout in milliseconds
    except KeyboardInterrupt:
        break

    if overseer_subscribe_socket in sockets:
        if is_stop_simulation(overseer_subscribe_socket):
            logging.info("received simulation_stop")
            run_simulation = False
            break

    # run disease generation to see if any diseases occurred
    elapsed_time = get_elapsed_time(start_time, time_scaling_factor)
    sim_time = start_time + elapsed_time
    logging.debug("Time elapsed: {}  Simulation datetime: {}".format(elapsed_time, sim_time))
    for disease in config['diseases']:
        if generate_disease(config):
            logging.debug("Disease occurred: {}".format(disease))
            increment_my_vector_timestamp_count(my_vector_timestamp, node_id)
            send_disease_notification(health_district_system_socket, node_id, disease, sim_time, my_vector_timestamp)

    # if end of day, send daily summary and last seven days summary

    # if outbreak daily query frequency interval is passed, send outbreak query

# shutdown procedures
logging.info("Shutting down . . .")
disconnect_from_peers(health_district_system_socket)
shutdown_listeners()
shutdown_zmq(context, overseer_request_socket, overseer_subscribe_socket)
