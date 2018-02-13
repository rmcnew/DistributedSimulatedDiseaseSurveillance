import unittest

import boto3

from shared.constants import *


class S3Test(unittest.TestCase):

    def test_bucket_list(self):
        s3 = boto3.resource(S3)
        bucket_list = s3.buckets.all()
        bucket_names = set()
        for bucket in bucket_list:
            print(bucket.name)
            bucket_names.add(bucket.name)
        self.assertTrue(LFSDS_S3_BUCKET in bucket_names)


if __name__ == '__main__':
    unittest.main()
