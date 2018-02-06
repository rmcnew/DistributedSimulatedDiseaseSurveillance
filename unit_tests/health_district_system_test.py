# unit tests for health district system
# note that most of health district system's functionality involves network communication, so unit tests are limited

import unittest

from health_district_system import HealthDistrictSystem
from overseer import Overseer
from shared.constants import *
from shared.node import Node
from shared.vector_timestamp import VectorTimestamp


class HealthDistrictSystemTest(unittest.TestCase):

    def get_basic_config(self):
        # populate the config map
        return {
            OVERSEER_HOST: str(Node.get_ip_address()),
            OVERSEER_REPLY_PORT: 9001,
            OVERSEER_PUBLISH_PORT: 9091,
            TIME_SCALING_FACTOR: 1800,
            DISEASES: ['cooties'],
            NODES: ['EMR', 'HDS', 'DOA']}

    def get_node_config(self):
        node_config = self.get_basic_config()
        node_config[NODE_ID] = "Node_A"
        node_config[ROLE] = HEALTH_DISTRICT_SYSTEM
        node_config[ROLE_PARAMETERS] = {
            DAILY_COUNT_SEND_FREQUENCY: 2
        }
        node_config[ADDRESS_MAP] = {
            ROLE: HEALTH_DISTRICT_SYSTEM
        }
        print(node_config)
        return node_config

    def test_handle_disease_notification(self):
        overseer = Overseer(self.get_basic_config())
        health_district_system = HealthDistrictSystem(self.get_node_config())
        self.assertEqual(health_district_system.current_daily_disease_counts['cooties'], 0)
        vector_timestamp = VectorTimestamp()
        vector_timestamp.increment_count("Mock_EMR")
        message = {MESSAGE_TYPE: DISEASE_NOTIFICATION,
                   ELECTRONIC_MEDICAL_RECORD_ID: "Mock_EMR",
                   DISEASE: "cooties",
                   LOCAL_TIMESTAMP: "Sometime",
                   VECTOR_TIMESTAMP: vector_timestamp}
        health_district_system.handle_disease_notification(message)
        self.assertEqual(health_district_system.current_daily_disease_counts['cooties'], 1)


if __name__ == '__main__':
    unittest.main()
