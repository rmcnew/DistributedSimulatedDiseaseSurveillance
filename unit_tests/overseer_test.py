# unit tests for overseer
# note that most of overseer's functionality involves network communication, so unit tests are limited
import unittest

from overseer import Overseer
from shared.constants import *
from shared.node import Node


class OverseerTest(unittest.TestCase):

    def get_basic_config(self):
        # populate the config map
        return {
            OVERSEER_HOST: str(Node.get_ip_address()),
            OVERSEER_REPLY_PORT: 9001,
            OVERSEER_PUBLISH_PORT: 9091,
            TIME_SCALING_FACTOR: 1800,
            DISEASES: ['cooties'],
            NODES: ['EMR', 'HDS', 'DOA']}

    def test_not_registered(self):
        overseer = Overseer(self.get_basic_config())
        self.assertFalse(overseer.all_registrations_completed())
        overseer.shutdown_zmq()


if __name__ == '__main__':
    unittest.main()
