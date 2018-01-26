import logging

import zmq

from config.sds_config import get_node_config
from helpers.electronic_medical_record_helper import setup_listeners, connect_to_peers, disconnect_from_peers, \
    shutdown_listeners
from helpers.node_helper import setup_zmq, register, receive_node_addresses, send_ready_to_start, \
    await_start_simulation, is_stop_simulation, shutdown_zmq

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

# send "ready_to_start" message to overseer
send_ready_to_start(overseer_request_socket, node_id)

# await "start_simulation" message from overseer
while await_start_simulation(overseer_subscribe_socket):
    pass  # do nothing until "simulation_start" is received

# configure main loop poller
logging.info("Configuring main loop poller")
poller = zmq.Poller()
poller.register(overseer_subscribe_socket, zmq.POLLIN)
poller.register(health_district_system_socket, zmq.POLLIN)

# main loop
logging.info("Starting simulation main loop")
run_simulation = True
while run_simulation:
    try:
        sockets = dict(poller.poll(700))  # poll timeout in milliseconds
    except KeyboardInterrupt:
        break

    if overseer_subscribe_socket in sockets:
        if is_stop_simulation(overseer_subscribe_socket):
            logging.info("received simulation_stop")
            run_simulation = False
            break

    if health_district_system_socket in sockets:
        pass
        # TODO: handle outbreak query response from health_district_system

    # add logic to track time scale and disease report generation

# shutdown procedures
logging.info("Shutting down . . .")
disconnect_from_peers(health_district_system_socket)
shutdown_listeners()
shutdown_zmq(context, overseer_request_socket, overseer_subscribe_socket)
