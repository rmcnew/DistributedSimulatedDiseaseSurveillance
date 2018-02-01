import json
import logging
import time

import zmq

from config.sds_config import get_overseer_config


class Overseer:

    def __init__(self, config):
        self.config = config
        self.context = zmq.Context()
        self.reply_socket = self.context.socket(zmq.REP)
        self.reply_socket.bind("tcp://*:" + str(config['overseer_reply_port']))
        self.publish_socket = self.context.socket(zmq.PUB)
        self.publish_socket.bind("tcp://*:" + str(config['overseer_publish_port']))
        # map of node_id => ip_address:port used for address registration
        self.node_addresses = {}
        # set of nodes that are ready to start the simulation
        self.nodes_ready_to_start = set()
        # node heartbeat tracking:  map of node_id => last_heartbeat_received
        # TODO: add node heartbeat sending and overseer alert trigger if no heartbeat received
        self.node_heartbeats = {}

    def shutdown_zmq(self):
        self.reply_socket.close(linger=2)
        self.publish_socket.close(linger=2)
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
        return len(self.config['nodes']) == len(self.node_addresses)

    def handle_node_registration_request(self):
        (node_id, message) = self.receive_from_nodes()
        logging.debug("Received message: \'{}\' from: \'{}\'".format(message, node_id))
        address_map = json.loads(message)
        node_role = address_map['role']
        if (node_role == "electronic_medical_record") or \
                (node_role == "health_district_system") or \
                (node_role == "disease_outbreak_analyzer"):

            self.node_addresses[node_id] = address_map
            logging.debug("Registration received for {}, role: {}".format(node_id, node_role))

        else:
            logging.error("Unknown node role: {}.  No configuration for this node role!!".format(node_role))

        self.send_to_node(self.reply_socket, node_id, "Successful registration for {}".format(node_id))

    def publish_node_addresses(self):
        json_node_addresses = json.dumps(self.node_addresses)
        self.publish_socket.send_string(json_node_addresses)

    def handle_node_ready_request(self):
        (node_id, message) = self.receive_from_nodes()
        logging.debug("Received message: \'{}\' from: \'{}\'".format(message, node_id))
        if message == "ready_to_start":
            self.nodes_ready_to_start.add(node_id)
            self.send_to_node(self.reply_socket, node_id, "'ready_to_start' received for {}".format(node_id))
        else:
            warning_message = "Did not receive expected 'ready_to_start' message!"
            logging.warning(warning_message)
            self.send_to_node(self.reply_socket, node_id, warning_message)

    def all_nodes_ready(self):
        return len(self.config['nodes']) == len(self.nodes_ready_to_start)

    def publish_start_simulation(self):
        self.publish_socket.send_string("start_simulation")

    def publish_stop_simulation(self):
        self.publish_socket.send_string("stop_simulation")

    def supervise_simulation(self):
        # publish "start_simulation" message to all nodes
        self.publish_start_simulation()

        # main simulation run loop
        while True:
            try:
                # TODO: add heartbeat handling here
                (node_id, reply) = self.receive_from_nodes()
                time.sleep(1)
            except KeyboardInterrupt:  # wait for Ctrl-C to exit main simulation run loop
                break

        # publish "stop_simulation" message to all nodes
        self.publish_stop_simulation()

        # supervise shutdown and report collection from all nodes

        # print summary report

        # shutdown
        self.shutdown_zmq()


def main():
    # get configuration and setup overseer listening
    config = get_overseer_config()
    logging.basicConfig(level=logging.DEBUG,
                        # filename='overseer.log',
                        format='%(asctime)s [%(levelname)s] %(message)s')
    logging.debug("overseer configuration: {}".format(config))

    overseer = Overseer(config)

    # register all nodes
    while not overseer.all_registrations_completed():
        overseer.handle_node_registration_request()
    logging.debug("registered node_addresses: {}".format(overseer.node_addresses))

    # publish node_addresses to all nodes
    overseer.publish_node_addresses()

    # wait for all nodes to connect to peers and then send "Ready" message
    while not overseer.all_nodes_ready():
        overseer.handle_node_ready_request()
    logging.debug("all nodes are ready to start.  Starting the simulation.  Press Ctrl-C to stop simulation.")

    # supervise simulation until user presses Ctrl-C
    overseer.supervise_simulation()


if __name__ == "__main__":
    main()
