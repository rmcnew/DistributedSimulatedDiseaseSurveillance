import logging

import zmq

from config.sds_config import get_node_config
from helpers.disease_outbreak_analyzer_helper import setup_listeners, connect_to_peers, disconnect_from_peers, \
    shutdown_listeners, handle_daily_disease_count_message, new_daily_disease_counts
from helpers.node_helper import setup_zmq, register, receive_node_addresses, send_ready_to_start, \
    await_start_simulation, is_stop_simulation, shutdown_zmq, get_start_time, get_elapsed_days, \
    update_simulation_time, archive_current_day
from vector_timestamp import VectorTimestamp

# get configuration and setup overseer connection
config = get_node_config("disease_outbreak_analyzer")
node_id = config['node_id']
logging.basicConfig(level=logging.DEBUG,
                    # filename='disease_outbreak_analyzer-' + node_id + '.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
logging.debug(config)
(context, overseer_request_socket, overseer_subscribe_socket) = setup_zmq(config)

# setup listening sockets
disease_outbreak_alert_publisher_socket = setup_listeners(context, config)

# register listener addresses with overseer
register(overseer_request_socket, node_id, config)

# get node_addresses from overseer and make peer connections
node_addresses = receive_node_addresses(overseer_subscribe_socket)
logging.debug("node_addresses received from overseer: {}".format(node_addresses))

# make peer connections
disease_count_subscription_sockets = connect_to_peers(context, config, node_addresses)

# initialize vector_timestamp
my_vector_timestamp = VectorTimestamp()

# daily disease counter and previous counts
disease = config['role_parameters']['disease']
current_daily_disease_counts = new_daily_disease_counts(config)
previous_daily_disease_counts = []

# configure main loop poller
logging.info("Configuring main loop poller")
poller = zmq.Poller()
poller.register(overseer_subscribe_socket, zmq.POLLIN)
for disease_count_subscription_socket in disease_count_subscription_sockets:
    poller.register(disease_count_subscription_socket)

# send "ready_to_start" message to overseer
send_ready_to_start(overseer_request_socket, node_id)

# await "start_simulation" message from overseer
while await_start_simulation(overseer_subscribe_socket):
    pass  # do nothing until "simulation_start" is received

# main loop
logging.info("Starting simulation main loop")
run_simulation = True
start_time = get_start_time()
current_daily_disease_counts['start_timestamp'] = start_time
while run_simulation:
    try:
        sockets = dict(poller.poll(700))  # poll timeout in milliseconds
    except KeyboardInterrupt:
        break

    for socket in sockets:
        if socket == overseer_subscribe_socket:
            if is_stop_simulation(overseer_subscribe_socket):
                logging.info("received stop_simulation")
                run_simulation = False
                break

        if socket in disease_count_subscription_sockets:
            message = socket.recv_pyobj()
            logging.debug("Received message: {}".format(message))
            handle_daily_disease_count_message(disease_outbreak_alert_publisher_socket, current_daily_disease_counts,
                                               config, my_vector_timestamp, message)

    # update simulation time
    (elapsed_time, sim_time) = update_simulation_time(start_time, config)

    # if the day is over, archive the disease count
    elapsed_days = get_elapsed_days(previous_daily_disease_counts)
    node_id = config['node_id']
    if elapsed_time.days > elapsed_days:
        current_daily_disease_counts['end_timestamp'] = sim_time
        my_vector_timestamp.increment_my_vector_timestamp_count(node_id)
        archive_current_day(current_daily_disease_counts, previous_daily_disease_counts)

        # reset current_daily_disease_counts
        current_daily_disease_counts = new_daily_disease_counts(config)
        current_daily_disease_counts['start_timestamp'] = sim_time

# shutdown procedures
logging.info("Shutting down . . .")
disconnect_from_peers(disease_count_subscription_sockets)
shutdown_listeners(disease_outbreak_alert_publisher_socket)
shutdown_zmq(context, overseer_request_socket, overseer_subscribe_socket)
