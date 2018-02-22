import logging

import zmq

from config.sds_config import get_node_config
from shared.constants import *
from shared.node import Node


class HealthDistrictSystem(Node):

    def __init__(self, config):
        super(HealthDistrictSystem, self).__init__(config)
        self.daily_count_send_frequency = self.role_parameters[DAILY_COUNT_SEND_FREQUENCY]
        self.electronic_medical_record_socket = None
        self.disease_count_publisher_socket = None
        self.disease_outbreak_alert_subscription_sockets = set()
        self.current_daily_disease_counts = self.new_daily_disease_counts()
        self.previous_daily_disease_counts = []
        self.outbreaks = set()

    # health_district_system nodes use REP listeners to receive
    # electronic_medical_record messages and PUB listeners to publish
    # messages to disease_outbreak_analyzers
    def setup_listeners(self):
        # create listener zmq sockets and save IP address and ports in config
        my_ip_address = self.get_ip_address()
        self.electronic_medical_record_socket = self.context.socket(zmq.REP)
        electronic_medical_record_port = self.electronic_medical_record_socket.bind_to_random_port(TCP_RANDOM_PORT)
        self.disease_count_publisher_socket = self.context.socket(zmq.PUB)
        disease_count_publisher_port = self.disease_count_publisher_socket.bind_to_random_port(TCP_RANDOM_PORT)
        self.config[ADDRESS_MAP] = {
            ROLE: self.role,
            ELECTRONIC_MEDICAL_RECORD_ADDRESS: TCP_PREFIX + my_ip_address + ":" + str(electronic_medical_record_port),
            DISEASE_OUTBREAK_ANALYZER_ADDRESS: TCP_PREFIX + my_ip_address + ":" + str(disease_count_publisher_port)
        }

    # shutdown listeners that were created in setup_listeners
    def shutdown_listeners(self):
        self.electronic_medical_record_socket.close(linger=2)
        self.disease_count_publisher_socket.close(linger=2)

    # each health_district_system connects subscription sockets to each disease_outbreak_analyzer node
    def connect_to_peers(self):
        # get the node_id's for connections to be made with disease_outbreak_analyzers
        connection_node_ids = self.config[CONNECTIONS]
        logging.debug("Connecting to node_id's: {}".format(connection_node_ids))
        for connection_node_id in connection_node_ids:
            # get the connection addresses
            connection_node_address = self.node_addresses[connection_node_id][HEALTH_DISTRICT_SYSTEM_ADDRESS]
            disease_outbreak_alert_subscription_socket = self.context.socket(zmq.SUB)
            disease_outbreak_alert_subscription_socket.connect(connection_node_address)
            # empty string filter => receive all messages
            disease_outbreak_alert_subscription_socket.setsockopt_string(zmq.SUBSCRIBE, '')
            self.disease_outbreak_alert_subscription_sockets.add(disease_outbreak_alert_subscription_socket)

    def disconnect_from_peers(self):
        for socket in self.disease_outbreak_alert_subscription_sockets:
            socket.close(linger=2)

    def configure_poller(self):
        logging.debug("Configuring main loop poller")
        self.poller = zmq.Poller()
        self.poller.register(self.overseer_subscribe_socket, zmq.POLLIN)
        self.poller.register(self.electronic_medical_record_socket, zmq.POLLIN)
        for disease_outbreak_alert_subscription_socket in self.disease_outbreak_alert_subscription_sockets:
            self.poller.register(disease_outbreak_alert_subscription_socket)

    def handle_disease_notification(self, message):
        disease = message[DISEASE]
        self.current_daily_disease_counts[disease] = self.current_daily_disease_counts[disease] + 1

    def handle_electronic_medical_record_request(self):
        message = self.electronic_medical_record_socket.recv_pyobj()
        # logging.debug("Received message: {}".format(message))
        self.vector_timestamp.increment_count(self.node_id)

        if message[MESSAGE_TYPE] == DISEASE_NOTIFICATION:
            self.handle_disease_notification(message)
            disease_notification_vector_timestamp = message[VECTOR_TIMESTAMP]
            self.vector_timestamp.update_from_other(disease_notification_vector_timestamp)
            reply = {MESSAGE_TYPE: DISEASE_NOTIFICATION_REPLY,
                     STATUS: RECEIVED,
                     VECTOR_TIMESTAMP: self.vector_timestamp}
            # logging.debug("Sending reply: {}".format(reply))
            self.electronic_medical_record_socket.send_pyobj(reply)
            disease = message[DISEASE]
            logging.debug("{}: {} count is now {}".format(self.get_simulation_time(), disease,
                                                          self.current_daily_disease_counts[disease]))

        elif message[MESSAGE_TYPE] == OUTBREAK_QUERY:
            outbreak_query_vector_timestamp = message[VECTOR_TIMESTAMP]
            self.vector_timestamp.update_from_other(outbreak_query_vector_timestamp)
            reply = {MESSAGE_TYPE: OUTBREAK_QUERY_REPLY,
                     OUTBREAKS: self.outbreaks,
                     VECTOR_TIMESTAMP: self.vector_timestamp}
            logging.debug("Sending reply: {}".format(reply))
            self.electronic_medical_record_socket.send_pyobj(reply)

        else:
            logging.warning("Unknown message_type: {} received from node_id: {}"
                            .format(message[MESSAGE_TYPE], message[ELECTRONIC_MEDICAL_RECORD_ID]))

    def handle_disease_outbreak_alert(self, socket):
        message = socket.recv_pyobj()
        logging.debug("Received outbreak alert message: {}".format(message))
        self.vector_timestamp.increment_count(self.node_id)
        disease_outbreak_alert_vector_timestamp = message[VECTOR_TIMESTAMP]
        self.vector_timestamp.update_from_other(disease_outbreak_alert_vector_timestamp)
        outbreak_disease = message[DISEASE]
        logging.info("[{}] *** ALERT *** {} outbreak detected!  vector_timestamp: {}"
                     .format(self.get_simulation_time(), outbreak_disease, self.vector_timestamp))
        self.outbreaks.add(outbreak_disease)

    def new_daily_disease_counts(self):
        daily_disease_counts = {MESSAGE_TYPE: DAILY_DISEASE_COUNT,
                                HEALTH_DISTRICT_SYSTEM_ID: self.node_id}
        for disease in self.diseases:
            daily_disease_counts[disease] = 0
        return daily_disease_counts

    def extract_disease_count_map(self):
        disease_count_map = {}
        for disease in self.diseases:
            disease_count_map[disease] = self.current_daily_disease_counts[disease]
        return disease_count_map

    def send_daily_disease_counts_using_sockets(self):
        self.current_daily_disease_counts[VECTOR_TIMESTAMP] = self.vector_timestamp
        logging.info("[{}] Sending disease counts: {}  vector_timestamp: {}"
                     .format(self.get_simulation_time(), self.extract_disease_count_map(), self.vector_timestamp))
        self.disease_count_publisher_socket.send_pyobj(self.current_daily_disease_counts)

    def send_daily_disease_counts(self):
        elapsed_days = self.get_elapsed_days(self.previous_daily_disease_counts)
        sim_time = self.get_simulation_time()
        # if the day is over, send the end-of-day counts, then reset the counts
        if self.get_elapsed_time().days > elapsed_days:
            self.current_daily_disease_counts[END_TIMESTAMP] = sim_time
            self.vector_timestamp.increment_count(self.node_id)
            self.send_daily_disease_counts_using_sockets()
            self.archive_current_day(self.current_daily_disease_counts, self.previous_daily_disease_counts)
            # reset current_daily_disease_counts
            self.current_daily_disease_counts = self.new_daily_disease_counts()
            self.current_daily_disease_counts[START_TIMESTAMP] = sim_time
        else:  # otherwise, send the current counts if enough time has elapsed
            self.send_daily_disease_counts_using_sockets()

    def shutdown(self):
        logging.info("Shutting down . . .")
        self.disconnect_from_peers()
        self.shutdown_listeners()
        self.deregister()
        self.shutdown_zmq()

    def run_simulation(self):
        logging.info("Starting simulation main loop")
        run_simulation = True
        self.record_start_time()
        start_time = self.get_start_time()
        last_daily_count_sent = start_time
        self.current_daily_disease_counts[START_TIMESTAMP] = start_time
        while run_simulation:
            try:
                sockets = dict(self.poller.poll(700))  # poll timeout in milliseconds
            except KeyboardInterrupt:
                break

            for socket in sockets:
                if socket == self.overseer_subscribe_socket:
                    if self.is_stop_simulation():
                        logging.info("[{}] Received stop_simulation".format(self.get_simulation_time()))
                        run_simulation = False
                        break

                if socket in self.disease_outbreak_alert_subscription_sockets:
                    logging.debug("received disease_outbreak_alert message")
                    self.handle_disease_outbreak_alert(socket)

                if socket == self.electronic_medical_record_socket:
                    self.handle_electronic_medical_record_request()

            # update simulation time
            sim_time = self.get_simulation_time()

            # send the current daily disease counts to the disease_outbreak_analyzers
            # if end of day, also reset daily counts
            duration_since_last_daily_count_sent = sim_time - last_daily_count_sent
            if (duration_since_last_daily_count_sent.seconds / SECONDS_PER_HOUR) > self.daily_count_send_frequency:
                self.send_daily_disease_counts()
                last_daily_count_sent = sim_time

            # if enough time has passed, send a heartbeat to the overseer
            self.send_heartbeat_if_time()

        # shutdown procedures
        self.shutdown()


def main():
    # get configuration and setup overseer connection
    config = get_node_config(HEALTH_DISTRICT_SYSTEM)
    log_file = "{}-{}.log".format(config[ROLE], config[NODE_ID])
    logging.basicConfig(format='%(message)s',
                        filename=log_file,
                        level=logging.DEBUG)
    logging.debug(config)

    health_district_system = HealthDistrictSystem(config)

    # setup listening sockets
    health_district_system.setup_listeners()

    # register listener addresses with overseer
    health_district_system.register()

    # get node_addresses from overseer
    health_district_system.receive_node_addresses()

    # make peer connections
    health_district_system.connect_to_peers()

    # configure main loop poller
    health_district_system.configure_poller()

    # send "ready_to_start" message to overseer
    health_district_system.send_ready_to_start()

    # await "start_simulation" message from overseer
    health_district_system.await_start_simulation()

    # run the simulation
    health_district_system.run_simulation()

    # post log to S3 URL if given
    health_district_system.post_log_to_s3(log_file)


if __name__ == "__main__":
    main()
