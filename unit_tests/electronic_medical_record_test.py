# unit tests for electronic medical record
# note that most of electronic medical record's functionality involves network communication, so unit tests are limited

import unittest

from electronic_medical_record import ElectronicMedicalRecord
from overseer import Overseer
from shared.constants import *
from shared.node import Node


class ElectronicMedicalRecordTest(unittest.TestCase):

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
        node_config[ROLE] = ELECTRONIC_MEDICAL_RECORD
        node_config[ROLE_PARAMETERS] = {
            OUTBREAK_DAILY_QUERY_FREQUENCY: 1
        }
        node_config[ADDRESS_MAP] = {
            ROLE: ELECTRONIC_MEDICAL_RECORD
        }
        print(node_config)
        return node_config

    def test_generate_disease_random(self):
        overseer = Overseer(self.get_basic_config())
        emr = ElectronicMedicalRecord(self.get_node_config())
        result_should_be_false = emr.generate_disease_random(0)
        self.assertFalse(result_should_be_false)

        result_should_be_true = emr.generate_disease_random(1)
        self.assertTrue(result_should_be_true)

        with self.assertRaises(TypeError):
            result_should_be_type_error = emr.generate_disease_random(-1)

        with self.assertRaises(TypeError):
            result_should_also_be_type_error = emr.generate_disease_random(2)


if __name__ == '__main__':
    unittest.main()
