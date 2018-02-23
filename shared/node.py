# parent class for all node types:  electronic_medical_record, health_district_system, and disease_outbreak_analyzer
import json
import logging
import socket
from datetime import datetime
from urllib.parse import parse_qs

import requests
import zmq

from shared.constants import *
from shared.vector_timestamp import VectorTimestamp


class Node:

    def __init__(self, config):
        self.config = config
        self.node_id = config[NODE_ID]
        self.time_scaling_factor = config[TIME_SCALING_FACTOR]
        self.role = config[ROLE]
        self.role_parameters = config[ROLE_PARAMETERS]
        self.diseases = config[DISEASES]
        self.simulation_start_time = None
        self.last_heartbeat_sent = None
        self.node_addresses = None
        self.vector_timestamp = VectorTimestamp()
        self.context = zmq.Context()
        self.poller = None
        self.overseer_request_socket = self.context.socket(zmq.REQ)
        overseer_host = config[OVERSEER_HOST]
        overseer_reply_port = str(config[OVERSEER_REPLY_PORT])
        overseer_publish_port = str(config[OVERSEER_PUBLISH_PORT])
        self.overseer_request_socket.connect("tcp://{}:{}".format(overseer_host, overseer_reply_port))
        self.overseer_subscribe_socket = self.context.socket(zmq.SUB)
        self.overseer_subscribe_socket.connect("tcp://{}:{}".format(overseer_host, overseer_publish_port))
        # empty string filter => receive all messages
        self.overseer_subscribe_socket.setsockopt_string(zmq.SUBSCRIBE, '')

    def shutdown_zmq(self):
        self.overseer_request_socket.close(linger=2)
        self.overseer_subscribe_socket.close(linger=2)
        self.context.term()

    def send_to_overseer(self, message):
        logging.debug("Sending message: \'{}\' from: {}".format(message, self.node_id))
        encoded_node_id = self.node_id.encode()
        encoded_message = message.encode()
        self.overseer_request_socket.send_multipart([encoded_node_id, encoded_message])

    def receive_from_overseer(self):
        while True:
            [encoded_destination_node_id, encoded_reply] = self.overseer_request_socket.recv_multipart()
            destination_node_id = encoded_destination_node_id.decode()
            reply = encoded_reply.decode()
            if self.node_id == destination_node_id:
                return reply

    def receive_subscription_message(self):
        return self.overseer_subscribe_socket.recv_string()

    def register(self):
        logging.debug("{} registering with overseer".format(self.node_id))
        address_map = self.config[ADDRESS_MAP]
        address_map[TYPE] = ADDRESS_MAP
        serialized_address_map = json.dumps(address_map)
        self.send_to_overseer(serialized_address_map)
        reply = self.receive_from_overseer()
        logging.debug(reply)

    def deregister(self):
        logging.debug("{} deregistering with overseer".format(self.node_id))
        message = DEREGISTER
        self.send_to_overseer(message)
        reply = self.receive_from_overseer()
        logging.debug(reply)

    def receive_node_addresses(self):
        json_node_addresses = self.receive_subscription_message()
        self.node_addresses = json.loads(json_node_addresses)
        logging.debug("node_addresses received from overseer: {}".format(self.node_addresses))

    def send_ready_to_start(self):
        message = READY_TO_START
        self.send_to_overseer(message)
        reply = self.receive_from_overseer()
        logging.debug(reply)

    def await_start_simulation(self):
        continue_to_wait = True
        while continue_to_wait:
            message = self.receive_subscription_message()
            if message == START_SIMULATION:
                continue_to_wait = False
            else:
                logging.warning("received message: '" + message + "' while awaiting for simulation_start")
                pass

    def is_stop_simulation(self):
        message = self.receive_subscription_message()
        if message == STOP_SIMULATION:
            return True
        else:
            logging.warning("received message: '" + message + "' but there is no logic defined to handle it")
            return False

    def record_start_time(self):
        self.simulation_start_time = datetime.now()
        self.last_heartbeat_sent = datetime.now()

    def get_start_time(self):
        return self.simulation_start_time

    def get_elapsed_time(self):
        return (datetime.now() - self.simulation_start_time) * self.time_scaling_factor

    def get_simulation_time(self):
        elapsed_time = self.get_elapsed_time()
        sim_time = self.simulation_start_time + elapsed_time
        # logging.debug("Time elapsed: {}  Simulation datetime: {}".format(elapsed_time, sim_time))
        return sim_time

    def send_heartbeat_if_time(self):
        current_time = datetime.now()
        time_since_last_heartbeat = current_time - self.last_heartbeat_sent
        if time_since_last_heartbeat.seconds > SECONDS_PER_HEARTBEAT:
            self.send_to_overseer(HEARTBEAT)
            reply = self.receive_from_overseer()
            self.last_heartbeat_sent = current_time
            logging.debug("Heartbeat response: {}".format(reply))

    def post_log_to_s3(self, log_file):
        if LOG_POST_URL in self.config:
            logging.debug("POSTing log file: {} to s3 . . .".format(log_file))
            slurped_log_file = open(log_file, R).read().replace('\n', ' ')
            files = {log_file: slurped_log_file}
            post = parse_qs(self.config[LOG_POST_URL])
            reply = requests.post(post[URL], data=post[FIELDS], files=files)
            logging.debug("Received post_log_to_s3 reply: {}".format(reply))

    def get_ip_address(self):
        if PUBLIC_IP_ADDRESS in self.config:
            return self.config[PUBLIC_IP_ADDRESS]
        else:
            temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                temp_socket.connect(('192.0.0.8', 1027))
            except socket.error:
                return None
            return temp_socket.getsockname()[0]

    @staticmethod
    def archive_current_day(current_daily_disease_counts, previous_daily_disease_counts):
        logging.debug("Archiving current daily disease counts: {}".format(current_daily_disease_counts))
        previous_daily_disease_counts.append(current_daily_disease_counts)
        logging.debug("previous_daily_disease_counts is now: {}".format(previous_daily_disease_counts))

    @staticmethod
    def get_elapsed_days(previous_daily_disease_counts):
        return len(previous_daily_disease_counts)
