import logging
from datetime import datetime
from math import sin, tau
from random import random

import zmq

from config.sds_config import get_node_config
from shared.constants import *
from shared.node import Node


class ElectronicMedicalRecord(Node):

    def __init__(self, config):
        super(ElectronicMedicalRecord, self).__init__(config)
        self.outbreak_daily_query_frequency = self.role_parameters[OUTBREAK_DAILY_QUERY_FREQUENCY]
        self.health_district_system_socket = None
        self.outbreaks = set()

    # electronic_medical_record nodes connect to health_district_system nodes
    # using REQ sockets; they have no listeners and do not provide a listener address
    # nevertheless, they register so the overseer knows that they are ready to receive
    # peer addresses
    def setup_listeners(self):
        self.config[ADDRESS_MAP] = {ROLE: self.config[ROLE]}

    # shutdown listeners that were created in setup_listeners
    def shutdown_listeners(self):
        pass

    # each electronic_medical_record connects to a single health_district_system node
    def connect_to_peers(self):
        # get node_id for the connection that needs to be made from config
        connection_node_id = self.config[CONNECTIONS][0]
        logging.debug("Connecting to node_id: {}".format(connection_node_id))
        # get the connection address from node_addresses
        connection_node_address = self.node_addresses[connection_node_id][ELECTRONIC_MEDICAL_RECORD_ADDRESS]
        logging.debug("Found node_id {} address as: {}".format(connection_node_id, connection_node_address))
        # create the REQ socket and connect
        self.health_district_system_socket = self.context.socket(zmq.REQ)
        self.health_district_system_socket.connect(connection_node_address)

    # close connections to peer nodes
    def disconnect_from_peers(self):
        self.health_district_system_socket.close(linger=2)

    def configure_poller(self):
        logging.debug("Configuring main loop poller")
        self.poller = zmq.Poller()
        self.poller.register(self.overseer_subscribe_socket, zmq.POLLIN)
        self.poller.register(self.health_district_system_socket, zmq.POLLIN)

    def send_disease_notification(self, disease, local_timestamp):
        message = {MESSAGE_TYPE: DISEASE_NOTIFICATION,
                   ELECTRONIC_MEDICAL_RECORD_ID: self.node_id,
                   DISEASE: disease,
                   LOCAL_TIMESTAMP: local_timestamp,
                   VECTOR_TIMESTAMP: self.vector_timestamp}
        logging.debug("Sending disease notification: {}".format(message))
        self.health_district_system_socket.send_pyobj(message)
        reply = self.health_district_system_socket.recv_pyobj()
        logging.debug("Received reply: {}".format(reply))
        reply_vector_timestamp = reply[VECTOR_TIMESTAMP]
        self.vector_timestamp.update_from_other(reply_vector_timestamp)

    # generate disease occurrences using the pseudorandom number generator:
    # probability threshold parameter is 0.0 <= x <= 1.0 where 0.0 means a disease occurrence
    # cannot happen and 1.0 means a disease occurrence will happen each time
    def generate_disease_random(self, probability_threshold):
        if (probability_threshold < 0.0) or (probability_threshold > 1.0):
            raise TypeError("probability_threshold out of range 0.0 <= x <= 1.0")
        # roll the PRNG to get a pseudorandom number
        random_number = random()
        return random_number < probability_threshold

    def generate_disease_sine(self, min_probability, max_probability):
        difference = max_probability - min_probability
        sine_probability = abs(sin((datetime.now().second / 60) * tau)) * difference + min_probability
        if sine_probability < min_probability:
            sine_probability = min_probability
        elif sine_probability > max_probability:
            sine_probability = max_probability
        logging.debug("sine_probability: {}".format(sine_probability))
        return self.generate_disease_random(sine_probability)

    def generate_disease(self):
        if self.role_parameters[DISEASE_GENERATION] == RANDOM:
            disease_generation_parameters = self.role_parameters[DISEASE_GENERATION_PARAMETERS]
            probability = disease_generation_parameters[PROBABILITY]
            return self.generate_disease_random(probability)
        elif self.role_parameters[DISEASE_GENERATION] == SINE:
            disease_generation_parameters = self.role_parameters[DISEASE_GENERATION_PARAMETERS]
            min_probability = disease_generation_parameters[MIN_PROBABILITY]
            max_probability = disease_generation_parameters[MAX_PROBABILITY]
            return self.generate_disease_sine(min_probability, max_probability)

    def send_outbreak_query(self):
        message = {MESSAGE_TYPE: OUTBREAK_QUERY,
                   ELECTRONIC_MEDICAL_RECORD_ID: self.node_id,
                   VECTOR_TIMESTAMP: self.vector_timestamp}
        logging.debug("Sending outbreak query: {}".format(message))
        self.health_district_system_socket.send_pyobj(message)
        reply = self.health_district_system_socket.recv_pyobj()
        logging.debug("Received reply: {}".format(reply))
        reply_vector_timestamp = reply[VECTOR_TIMESTAMP]
        self.vector_timestamp.update_from_other(reply_vector_timestamp)
        outbreaks = reply[OUTBREAKS]
        for disease in outbreaks:
            if disease not in self.outbreaks:
                self.outbreaks.add(disease)
                logging.info("[{}] *** ALERT *** {} outbreak reported!  vector_timestamp: {}"
                             .format(self.get_simulation_time(), disease, self.vector_timestamp))

    def shutdown(self):
        logging.info("Shutting down . . .")
        self.disconnect_from_peers()
        self.shutdown_listeners()
        self.deregister()
        self.shutdown_zmq()

    def run_simulation(self):
        logging.info("Starting simulation main loop")
        self.record_start_time()
        start_time = self.get_start_time()
        elapsed_days = 0
        last_outbreak_query_time = start_time
        while True:
            # poll sockets and handle incoming messages
            try:
                sockets = dict(self.poller.poll(700))  # poll timeout in milliseconds
            except KeyboardInterrupt:
                break

            if self.overseer_subscribe_socket in sockets:
                if self.is_stop_simulation():
                    logging.info("[{}] Received stop_simulation".format(self.get_simulation_time()))
                    break

            # update simulation time
            sim_time = self.get_simulation_time()

            # run disease generation to see if any diseases occurred
            for disease in self.diseases:
                if self.generate_disease():
                    self.vector_timestamp.increment_count(self.node_id)
                    self.send_disease_notification(disease, sim_time)
                    logging.info("[{}] Disease occurred: {}  vector_timestamp: {}"
                                 .format(sim_time, disease, self.vector_timestamp))

            # if outbreak daily query frequency interval is passed, send outbreak query
            duration_since_last_query = sim_time - last_outbreak_query_time
            if (duration_since_last_query.seconds / SECONDS_PER_HOUR) > self.outbreak_daily_query_frequency:
                self.send_outbreak_query()
                last_outbreak_query_time = sim_time

            # if a simulation day passed, reset outbreak notification
            if self.get_elapsed_time().days > elapsed_days:
                self.outbreaks = set()
                elapsed_days = elapsed_days + 1

            # if enough time has passed, send a heartbeat to the overseer
            self.send_heartbeat_if_time()

        # shutdown procedures
        self.shutdown()


def main():
    # get configuration and setup overseer connection
    config = get_node_config(ELECTRONIC_MEDICAL_RECORD)
    log_file = "{}-{}.log".format(config[ROLE], config[NODE_ID])
    logging.basicConfig(format='%(message)s',
                        filename=log_file,
                        level=logging.INFO)
    logging.debug(config)

    electronic_medical_record = ElectronicMedicalRecord(config)

    # setup listening sockets
    electronic_medical_record.setup_listeners()

    # register listener addresses with overseer
    electronic_medical_record.register()

    # get node_addresses from overseer
    electronic_medical_record.receive_node_addresses()

    # make peer connections
    electronic_medical_record.connect_to_peers()

    # configure main loop poller
    electronic_medical_record.configure_poller()

    # send "ready_to_start" message to overseer
    electronic_medical_record.send_ready_to_start()

    # await "start_simulation" message from overseer
    electronic_medical_record.await_start_simulation()

    # run the simulation
    electronic_medical_record.run_simulation()

    # post log to S3 URL if given
    electronic_medical_record.post_log_to_s3(log_file)


if __name__ == "__main__":
    main()
