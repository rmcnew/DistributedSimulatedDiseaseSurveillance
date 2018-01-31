import logging

import zmq

from config.sds_config import get_node_config
from helpers.health_district_system_helper import setup_listeners, connect_to_peers, disconnect_from_peers, \
    shutdown_listeners, handle_electronic_medical_record_request, new_daily_disease_counts, send_daily_disease_counts, \
    handle_disease_outbreak_alert
from helpers.node_helper import setup_zmq, register, receive_node_addresses, send_ready_to_start, \
    await_start_simulation, is_stop_simulation, shutdown_zmq, get_start_time, update_simulation_time
from vector_timestamp import VectorTimestamp

# get configuration and setup overseer connection
config = get_node_config("health_district_system")
node_id = config['node_id']
logging.basicConfig(level=logging.DEBUG,
                    # filename='health_district_system-' + node_id + '.log',
                    format='%(asctime)s [%(levelname)s] %(message)s')
# console = logging.StreamHandler()
# console.setLevel(logging.INFO)
# logging.getLogger('').addHandler(console)
logging.debug(config)
(context, overseer_request_socket, overseer_subscribe_socket) = setup_zmq(config)
daily_count_send_frequency = config['role_parameters']['daily_count_send_frequency']

# setup listening sockets
(electronic_medical_record_socket, disease_count_publisher_socket) = setup_listeners(context, config)

# register listener addresses with overseer
register(overseer_request_socket, node_id, config)

# get node_addresses from overseer and make peer connections
node_addresses = receive_node_addresses(overseer_subscribe_socket)
logging.debug("node_addresses received from overseer: {}".format(node_addresses))

# make peer connections
disease_outbreak_alert_subscription_sockets = connect_to_peers(context, config, node_addresses)

# configure main loop poller
logging.info("Configuring main loop poller")
poller = zmq.Poller()
poller.register(overseer_subscribe_socket, zmq.POLLIN)
poller.register(electronic_medical_record_socket, zmq.POLLIN)
for disease_outbreak_alert_subscription_socket in disease_outbreak_alert_subscription_sockets:
    poller.register(disease_outbreak_alert_subscription_socket)

# initialize vector_timestamp
my_vector_timestamp = VectorTimestamp()

# initialize current_daily_disease_counts and previous_daily_disease_counts
# these are populated from disease_notifications that electronic_medical_records send
current_daily_disease_counts = new_daily_disease_counts(config)
previous_daily_disease_counts = []

# outbreak tracking
outbreaks = set()

# send "ready_to_start" message to overseer
send_ready_to_start(overseer_request_socket, node_id)

# await "start_simulation" message from overseer
while await_start_simulation(overseer_subscribe_socket):
    pass  # do nothing until "simulation_start" is received

# main loop
logging.info("Starting simulation main loop")
run_simulation = True
start_time = get_start_time()
last_daily_count_sent = start_time
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

        if socket in disease_outbreak_alert_subscription_sockets:
            logging.debug("received disease_outbreak_alert message")
            handle_disease_outbreak_alert(socket, node_id, my_vector_timestamp, outbreaks)

        if socket == electronic_medical_record_socket:
            handle_electronic_medical_record_request(electronic_medical_record_socket,
                                                     node_id, my_vector_timestamp,
                                                     current_daily_disease_counts, outbreaks)

    # update simulation time
    (elapsed_time, sim_time) = update_simulation_time(start_time, config)

    # send the current daily disease counts to the disease_outbreak_analyzers
    # if end of day, also reset daily counts
    duration_since_last_daily_count_sent = sim_time - last_daily_count_sent
    if (duration_since_last_daily_count_sent.seconds / 3600) > daily_count_send_frequency:
        send_daily_disease_counts(disease_count_publisher_socket, config, my_vector_timestamp,
                                  current_daily_disease_counts, previous_daily_disease_counts, elapsed_time, sim_time)
        last_daily_count_sent = sim_time

# shutdown procedures
logging.info("Shutting down . . .")
disconnect_from_peers(disease_outbreak_alert_subscription_sockets)
shutdown_listeners(electronic_medical_record_socket, disease_count_publisher_socket)
shutdown_zmq(context, overseer_request_socket, overseer_subscribe_socket)
