import logging

import zmq

from config.sds_config import get_node_config
from shared.constants import *
from shared.node import Node


class DiseaseOutbreakAnalyzer(Node):

    def __init__(self, config):
        super(DiseaseOutbreakAnalyzer, self).__init__(config)
        self.disease = self.role_parameters[DISEASE]
        self.daily_outbreak_threshold = self.role_parameters[DAILY_OUTBREAK_THRESHOLD]
        self.disease_outbreak_alert_publisher_socket = None
        self.disease_count_subscription_sockets = set()
        self.current_daily_disease_counts = self.new_daily_disease_counts()
        self.previous_daily_disease_counts = []

    # disease_outbreak_analyzer nodes use PUB listeners to publish
    # disease outbreak alerts to health_district_systems
    def setup_listeners(self):
        # create listener zmq sockets and save IP address and ports in config
        my_ip_address = self.get_ip_address()
        self.disease_outbreak_alert_publisher_socket = self.context.socket(zmq.PUB)
        disease_outbreak_alert_publisher_port = \
            self.disease_outbreak_alert_publisher_socket.bind_to_random_port(TCP_RANDOM_PORT)
        self.config[ADDRESS_MAP] = {
            ROLE: self.role,
            HEALTH_DISTRICT_SYSTEM_ADDRESS:
                "tcp://{}:{}".format(my_ip_address, str(disease_outbreak_alert_publisher_port))
        }

    # shutdown listeners that were created in setup_listeners
    def shutdown_listeners(self):
        self.disease_outbreak_alert_publisher_socket.close(linger=2)

    # each disease_outbreak_analyzer connects subscription sockets to each health_district_system node
    def connect_to_peers(self):
        # get the node_id's for connections to be made with health_district_system nodes
        connection_node_ids = self.config[CONNECTIONS]
        logging.debug("Connecting to node_id's: {}".format(connection_node_ids))
        for connection_node_id in connection_node_ids:
            # get the connection addresses
            connection_node_address = self.node_addresses[connection_node_id][DISEASE_OUTBREAK_ANALYZER_ADDRESS]
            disease_count_subscription_socket = self.context.socket(zmq.SUB)
            disease_count_subscription_socket.connect(connection_node_address)
            # empty string filter => receive all messages
            disease_count_subscription_socket.setsockopt_string(zmq.SUBSCRIBE, '')
            self.disease_count_subscription_sockets.add(disease_count_subscription_socket)

    # close connections to peer nodes
    def disconnect_from_peers(self):
        for socket in self.disease_count_subscription_sockets:
            socket.close(linger=2)

    def configure_poller(self):
        logging.debug("Configuring main loop poller")
        self.poller = zmq.Poller()
        self.poller.register(self.overseer_subscribe_socket, zmq.POLLIN)
        for disease_count_subscription_socket in self.disease_count_subscription_sockets:
            self.poller.register(disease_count_subscription_socket)

    def new_daily_disease_counts(self):
        return {DISEASE_OUTBREAK_ANALYZER_ID: self.node_id,
                DISEASE: self.disease,
                HEALTH_DISTRICT_COUNTS: {},
                TOTAL: 0,
                DAILY_OUTBREAK_THRESHOLD: self.daily_outbreak_threshold,
                NOTIFICATION_SENT: False}

    def update_daily_disease_counts(self, health_district_system_id, disease_count):
        self.current_daily_disease_counts[HEALTH_DISTRICT_COUNTS][health_district_system_id] = disease_count
        total = 0
        for health_district_system in self.current_daily_disease_counts[HEALTH_DISTRICT_COUNTS]:
            total = total + self.current_daily_disease_counts[HEALTH_DISTRICT_COUNTS][health_district_system]
        self.current_daily_disease_counts[TOTAL] = total

    def handle_daily_disease_count_message(self, message):
        self.vector_timestamp.increment_count(self.node_id)
        other_vector_timestamp = message[VECTOR_TIMESTAMP]
        self.vector_timestamp.update_from_other(other_vector_timestamp)
        health_district_system_id = message[HEALTH_DISTRICT_SYSTEM_ID]
        # filter for the disease of interest
        disease_count = message[self.disease]
        self.update_daily_disease_counts(health_district_system_id, disease_count)
        logging.info("[{}] {} daily total is now {}.  vector_timestamp: {}"
                     .format(self.get_simulation_time(), self.disease,
                             self.current_daily_disease_counts[TOTAL], self.vector_timestamp))
        if self.current_daily_disease_counts[TOTAL] >= self.daily_outbreak_threshold \
                and not self.current_daily_disease_counts[NOTIFICATION_SENT]:
            logging.info("[{}] *** ALERT *** {} outbreak detected!  vector_timestamp: {}"
                         .format(self.get_simulation_time(), self.vector_timestamp, self.disease))
            alert_message = {MESSAGE_TYPE: DISEASE_OUTBREAK_ALERT,
                             DISEASE: self.disease,
                             VECTOR_TIMESTAMP: self.vector_timestamp}
            logging.debug("Sending alert: {}".format(alert_message))
            self.disease_outbreak_alert_publisher_socket.send_pyobj(alert_message)
            self.current_daily_disease_counts[NOTIFICATION_SENT] = True

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

                if socket in self.disease_count_subscription_sockets:
                    message = socket.recv_pyobj()
                    logging.debug("Received message: {}".format(message))
                    self.handle_daily_disease_count_message(message)

            # update simulation time
            sim_time = self.get_simulation_time()
            elapsed_days = self.get_elapsed_days(self.previous_daily_disease_counts)

            # if the day is over, archive the disease count
            if self.get_elapsed_time().days > elapsed_days:
                self.current_daily_disease_counts[END_TIMESTAMP] = sim_time
                self.vector_timestamp.increment_count(self.node_id)
                self.archive_current_day(self.current_daily_disease_counts, self.previous_daily_disease_counts)
                # reset current_daily_disease_counts
                self.current_daily_disease_counts = self.new_daily_disease_counts()
                self.current_daily_disease_counts[START_TIMESTAMP] = sim_time

            # if enough time has passed, send a heartbeat to the overseer
            self.send_heartbeat_if_time()

        # shutdown procedures
        self.shutdown()


def main():
    # get configuration and setup overseer connection
    config = get_node_config(DISEASE_OUTBREAK_ANALYZER)
    log_file = "{}-{}.log".format(config[ROLE], config[NODE_ID])
    logging.basicConfig(format='%(message)s',
                        filename=log_file,
                        level=logging.DEBUG)
    logging.debug(config)

    disease_outbreak_analyzer = DiseaseOutbreakAnalyzer(config)

    # setup listening sockets
    disease_outbreak_analyzer.setup_listeners()

    # register listener addresses with overseer
    disease_outbreak_analyzer.register()

    # get node_addresses from overseer and make peer connections
    disease_outbreak_analyzer.receive_node_addresses()

    # make peer connections
    disease_outbreak_analyzer.connect_to_peers()

    # configure main loop poller
    disease_outbreak_analyzer.configure_poller()

    # send "ready_to_start" message to overseer
    disease_outbreak_analyzer.send_ready_to_start()

    # await "start_simulation" message from overseer
    disease_outbreak_analyzer.await_start_simulation()

    # run the simulation
    disease_outbreak_analyzer.run_simulation()

    # post log to S3 URL if given
    disease_outbreak_analyzer.post_log_to_s3(log_file)


if __name__ == "__main__":
    main()
