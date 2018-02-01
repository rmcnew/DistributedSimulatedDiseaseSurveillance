import unittest

from electronic_medical_record import ElectronicMedicalRecord


class ElectronicMedicalRecordTest(unittest.TestCase):

    def test_generate_disease_random(self):
        emr = ElectronicMedicalRecord()
        result_should_be_false = emr.generate_disease_random(0)
        self.assertFalse(result_should_be_false)

        result_should_be_true = emr.generate_disease_random(1)
        self.assertTrue(result_should_be_true)

        with self.assertRaises(TypeError):
            result_should_be_type_error = emr.generate_disease_random(-1)

        with self.assertRaises(TypeError):
            result_should_also_be_type_error = emr.generate_disease_random(2)

    # more unit tests here


if __name__ == '__main__':
    unittest.main()
