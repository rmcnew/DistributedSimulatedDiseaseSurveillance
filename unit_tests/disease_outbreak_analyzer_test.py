# unit tests for disease outbreak analyzer
# note that most of disease outbreak analyzer's functionality involves network communication, so unit tests are limited
import unittest
from datetime import datetime

from disease_outbreak_analyzer import DiseaseOutbreakAnalyzer
from overseer import Overseer
from shared.constants import *
from shared.node import Node, VectorTimestamp


class DiseaseOutbreakAnalyzerTest(unittest.TestCase):

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
        node_config[ROLE] = DISEASE_OUTBREAK_ANALYZER
        node_config[ROLE_PARAMETERS] = {
            DISEASE: 'cooties',
            DAILY_OUTBREAK_THRESHOLD: 10
        }
        node_config[ADDRESS_MAP] = {
            ROLE: DISEASE_OUTBREAK_ANALYZER
        }
        print(node_config)
        return node_config

    def test_handle_daily_disease_count_message(self):
        overseer = Overseer(self.get_basic_config())
        disease_outbreak_analzyer = DiseaseOutbreakAnalyzer(self.get_node_config())
        disease_outbreak_analzyer.simulation_start_time = datetime.now()

        vector_timestamp = VectorTimestamp()
        vector_timestamp.increment_count("Mock_HDS")
        message = {MESSAGE_TYPE: DAILY_DISEASE_COUNT,
                   HEALTH_DISTRICT_SYSTEM_ID: "Mock_HDS",
                   VECTOR_TIMESTAMP: vector_timestamp,
                   'cooties': 5}
        disease_outbreak_analzyer.handle_daily_disease_count_message(message)
        self.assertEqual(disease_outbreak_analzyer.current_daily_disease_counts[TOTAL], 5)


if __name__ == '__main__':
    unittest.main()
