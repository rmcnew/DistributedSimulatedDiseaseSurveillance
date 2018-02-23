import json
import logging
import time
from datetime import datetime
from urllib.parse import parse_qs

import requests
import zmq

from config.sds_config import get_overseer_config
from shared.constants import *


class Overseer:

    def __init__(self, config):
        self.config = config
        self.context = zmq.Context()
        self.reply_socket = self.context.socket(zmq.REP)
        self.reply_socket.bind(TCP_SPECIFIED_PORT + str(config[OVERSEER_REPLY_PORT]))
        self.publish_socket = self.context.socket(zmq.PUB)
        self.publish_socket.bind(TCP_SPECIFIED_PORT + str(config[OVERSEER_PUBLISH_PORT]))
        self.poller = None
        # map of node_id => ip_address:port used for address registration
        self.node_addresses = {}
        # set of nodes that are ready to start the simulation
        self.nodes_ready_to_start = set()
        # node heartbeat tracking:  map of node_id => last_heartbeat_received
        self.node_heartbeats = {}

    def shutdown_zmq(self):
        self.publish_socket.close(linger=2)
        self.reply_socket.close(linger=2)
        self.context.term()

    def send_to_node(self, socket, node_id, message):
        encoded_node_id = node_id.encode()
        encoded_message = message.encode()
        socket.send_multipart([encoded_node_id, encoded_message])

    def receive_from_nodes(self):
        [encoded_node_id, encoded_reply] = self.reply_socket.recv_multipart()
        node_id = encoded_node_id.decode()
        reply = encoded_reply.decode()
        ret_val = (node_id, reply)
        return ret_val

    def all_registrations_completed(self):
        return len(self.config[NODES]) == len(self.node_addresses)

    def all_deregistrations_completed(self):
        return len(self.node_addresses) == 0

    def handle_node_registration_request(self):
        (node_id, message) = self.receive_from_nodes()
        logging.debug("Received message: \'{}\' from: \'{}\'".format(message, node_id))
        address_map = json.loads(message)
        node_role = address_map[ROLE]
        if (node_role == ELECTRONIC_MEDICAL_RECORD) or \
                (node_role == HEALTH_DISTRICT_SYSTEM) or \
                (node_role == DISEASE_OUTBREAK_ANALYZER):

            self.node_addresses[node_id] = address_map
            logging.info("Registration received for {}, role: {}".format(node_id, node_role))

        else:
            logging.error("Unknown node role: {}.  No configuration for this node role!!".format(node_role))

        self.send_to_node(self.reply_socket, node_id, "Successful registration for {}".format(node_id))

    def handle_node_deregistration_request(self):
        (node_id, message) = self.receive_from_nodes()
        logging.debug("Received message: \'{}\' from: \'{}\'".format(message, node_id))
        if message == DEREGISTER:
            self.send_to_node(self.reply_socket, node_id, "Successful deregistration for {}".format(node_id))
            del self.node_addresses[node_id]
            logging.info("{} deregistered".format(node_id))
        else:
            warning_message = "Did not receive expected 'deregister' message!"
            logging.warning(warning_message)
            self.send_to_node(self.reply_socket, node_id, warning_message)
        
    def publish_node_addresses(self):
        json_node_addresses = json.dumps(self.node_addresses)
        self.publish_socket.send_string(json_node_addresses)

    def handle_node_ready_request(self):
        (node_id, message) = self.receive_from_nodes()
        logging.debug("Received message: \'{}\' from: \'{}\'".format(message, node_id))
        if message == READY_TO_START:
            self.nodes_ready_to_start.add(node_id)
            self.send_to_node(self.reply_socket, node_id, "'ready_to_start' received for {}".format(node_id))
            logging.info("{} is ready to start.".format(node_id))
        else:
            warning_message = "Did not receive expected 'ready_to_start' message!"
            logging.warning(warning_message)
            self.send_to_node(self.reply_socket, node_id, warning_message)

    def all_nodes_ready(self):
        return len(self.config[NODES]) == len(self.nodes_ready_to_start)

    def configure_poller(self):
        self.poller = zmq.Poller()
        self.poller.register(self.reply_socket, zmq.POLLIN)

    def publish_heartbeat(self):
        logging.info("Pub Heartbeat")
        self.publish_socket.send_string(OVERSEER_HEARTBEAT)

    def publish_start_simulation(self):
        logging.info("Starting the simulation . . .")
        start_time = datetime.now()
        # set initial node heartbeat time
        for node_id in self.node_addresses:
            self.node_heartbeats[node_id] = start_time
        # publish start message
        self.publish_socket.send_string(START_SIMULATION)

    def publish_stop_simulation(self):
        logging.info("Stopping the simulation . . .")
        self.publish_socket.send_string(STOP_SIMULATION)

    def check_node_heartbeats(self):
        current_time = datetime.now()
        for node_id, last_heartbeat_timestamp in self.node_heartbeats.items():
            elapsed_time = current_time - last_heartbeat_timestamp
            if elapsed_time.seconds > SECONDS_WITHOUT_HEARTBEAT:
                logging.error("*** No heartbeats from {} since {}!  {} may be down or bad network connection."
                              .format(node_id, last_heartbeat_timestamp, node_id))

    def post_log_to_s3(self, log_file):
        if LOG_POST_URL in self.config:
            logging.debug("POSTing log file: {} to s3 . . .".format(log_file))
            files = {FILE: open(log_file, RB)}
            post = parse_qs(self.config[LOG_POST_URL])
            reply = requests.post(post[URL], data=post[FIELDS], files=files)
            logging.debug("Received post_log_to_s3 reply: {}".format(reply))

    def supervise_simulation(self):
        self.configure_poller()
        # publish "start_simulation" message to all nodes
        self.publish_start_simulation()

        # main simulation run loop
        logging.info("Press Ctrl-C to stop simulation.")
        while True:
            try:
                sockets = dict(self.poller.poll(700))  # poll timeout in milliseconds
                if self.reply_socket in sockets:
                    (node_id, message) = self.receive_from_nodes()
                    logging.debug("Received message: {} from node: {}".format(message, node_id))
                    if message == STOP_SIMULATION:
                        self.send_to_node(self.reply_socket, node_id, ACKNOWLEDGED)
                        logging.info("Received remote shutdown request")
                        break
                    elif message == HEARTBEAT:
                        self.send_to_node(self.reply_socket, node_id, HEARTBEAT_RECEIVED)
                        self.node_heartbeats[node_id] = datetime.now()
                        logging.info("Heartbeat received from: {}".format(node_id))
                self.check_node_heartbeats()
                overseer.publish_heartbeat()
                time.sleep(1)
            except KeyboardInterrupt:  # wait for Ctrl-C to exit main simulation run loop
                break

        # publish "stop_simulation" message to all nodes
        self.publish_stop_simulation()


def main():
    # get configuration and setup overseer listening
    config = get_overseer_config()
    log_file = OVERSEER_LOG
    logging.basicConfig(format='%(message)s',
                        filename=log_file,
                        level=logging.DEBUG)
    logging.debug(config)

    overseer = Overseer(config)

    # register all nodes
    logging.info("Waiting for nodes to register . . .")
    overseer.publish_heartbeat()
    while not overseer.all_registrations_completed():
        overseer.handle_node_registration_request()
        overseer.publish_heartbeat()
    logging.info("All nodes are registered.")
    logging.debug("registered node_addresses: {}".format(overseer.node_addresses))

    # publish node_addresses to all nodes
    logging.info("Publishing node addresses . . .")
    overseer.publish_heartbeat()
    overseer.publish_node_addresses()

    # wait for all nodes to connect to peers and then send "Ready" message
    logging.info("Waiting for nodes to get ready . . .")
    overseer.publish_heartbeat()
    while not overseer.all_nodes_ready():
        overseer.publish_heartbeat()
        overseer.handle_node_ready_request()
    logging.info("All nodes are ready to start.")

    # supervise simulation until user presses Ctrl-C
    overseer.supervise_simulation()

    # wait for all nodes to deregister
    logging.info("Waiting for nodes to deregister . . .")
    overseer.publish_heartbeat()
    while not overseer.all_deregistrations_completed():
        overseer.publish_heartbeat()
        overseer.handle_node_deregistration_request()
    logging.info("All nodes are deregistered.  Shutting down . . .")

    # shutdown
    overseer.shutdown_zmq()

    # post log to S3 URL if given
    overseer.post_log_to_s3(log_file)


if __name__ == "__main__":
    main()
