# parent class for all runner classes
import logging
import os
import signal
import subprocess
import sys
from multiprocessing import Process

import zmq

from shared.constants import *


class Run:

    def __init__(self, config):
        self.config = config
        self.node_id = SIMULATION_RUNNER
        self.processes = {}
        self.context = None
        self.overseer_request_socket = None

    def get_python_interpreter(self):
        return sys.executable

    def get_script_folder(self):
        return os.path.dirname(os.path.realpath(sys.argv[0]))

    def build_overseer_command_line(self, config_file):
        return "{} {} {}".format(self.get_python_interpreter(),
                                 os.path.join(self.get_script_folder(), OVERSEER_SCRIPT_NAME),
                                 config_file)

    def build_simulation_node_command_lines(self, config_file):
        node_command_lines = {}
        for node_id in self.config[NODES]:
            role = self.config[NODES][node_id]
            script_name = None
            if role == ELECTRONIC_MEDICAL_RECORD:
                script_name = ELECTRONIC_MEDICAL_RECORD_SCRIPT_NAME
            elif role == HEALTH_DISTRICT_SYSTEM:
                script_name = HEALTH_DISTRICT_SYSTEM_SCRIPT_NAME
            elif role == DISEASE_OUTBREAK_ANALYZER:
                script_name = DISEASE_OUTBREAK_ANALYZER_SCRIPT_NAME
            else:
                raise TypeError("Unknown role {}! Cannot determine script to run!".format(role))

            node_command_line = "{} {} {} {}".format(self.get_python_interpreter(),
                                                     os.path.join(self.get_script_folder(), script_name),
                                                     node_id,
                                                     config_file)
            # logging.debug("Adding simulation node command line: {}".format(node_command_line))
            node_command_lines[node_id] = node_command_line
        return node_command_lines

    def run_as_subprocess(self, command_line):
        split_command_line = command_line.split(' ')
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        completed = subprocess.run(split_command_line, stdin=None)
        return completed

    def run_in_own_process(self, node_id, command_line):
        logging.debug("Launching process with command_line: {}".format(command_line))
        self.processes[node_id] = Process(target=self.run_as_subprocess, args=(command_line,), name=node_id)
        self.processes[node_id].start()

    def connect_to_overseer(self):
        logging.debug("connecting to overseer . . .")
        self.context = zmq.Context()
        self.overseer_request_socket = self.context.socket(zmq.REQ)
        overseer_host = self.config[OVERSEER_HOST]
        overseer_reply_port = str(self.config[OVERSEER_REPLY_PORT])
        self.overseer_request_socket.connect("tcp://{}:{}".format(overseer_host, overseer_reply_port))

    def send_to_overseer(self, message):
        logging.debug("Sending message: \'" + message + "\' from: \'" + self.node_id + "\'")
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
