# unit tests for vector_timestamp

import unittest

from shared.vector_timestamp import VectorTimestamp


class VectorTimestampTest(unittest.TestCase):

    def test_increment_count(self):
        vector_timestamp = VectorTimestamp()
        vector_timestamp.increment_count("A")
        vector_timestamp.increment_count("A")
        vector_timestamp.increment_count("A")
        vector_timestamp.increment_count("B")
        vector_timestamp.increment_count("B")
        vector_timestamp.increment_count("C")
        expected = {'A': 3, 'B': 2, 'C': 1}
        print(vector_timestamp)
        self.assertIsNotNone(vector_timestamp)
        self.assertTrue(vector_timestamp.vector_timestamp == expected)

    def test_update_from_other(self):
        vector_timestamp = VectorTimestamp()
        vector_timestamp.increment_count("A")
        vector_timestamp.increment_count("A")
        vector_timestamp.increment_count("A")
        vector_timestamp.increment_count("B")
        vector_timestamp.increment_count("B")
        vector_timestamp.increment_count("C")
        other = VectorTimestamp()
        other.increment_count("A")
        other.increment_count("A")
        other.increment_count("A")
        other.increment_count("A")
        other.increment_count("B")
        other.increment_count("C")
        other.increment_count("C")
        other.increment_count("C")
        other.increment_count("D")
        vector_timestamp.update_from_other(other)
        expected = {'A': 4, 'B': 2, 'C': 3, 'D': 1}
        print(vector_timestamp)
        self.assertTrue(vector_timestamp.vector_timestamp == expected)


if __name__ == '__main__':
    unittest.main()
