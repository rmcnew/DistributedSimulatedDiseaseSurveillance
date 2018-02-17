# aws functions
import json
import logging
import os
import socket
import tempfile
from datetime import datetime
from pathlib import Path

import boto3

from aws.ec2_instance import Ec2Instance
from shared.constants import *


def create_ec2_instances(count):
    ec2 = boto3.resource(EC2)
    ec2_instances = []
    instances = ec2.create_instances(
        ImageId=UBUNTU_PYTHON3_AMI_ID,
        MinCount=count,
        MaxCount=count,
        SecurityGroupIds=[LFSDS_SECURITY_GROUP_ID],
        KeyName=LFSDS_KEY_NAME,
        InstanceType=T2_MICRO)
    for instance in instances:
        ec2_instance = Ec2Instance(instance.instance_id)
        ec2_instances.append(ec2_instance)
    return ec2_instances


def get_running_instances():
    ec2 = boto3.resource(EC2)
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        print(instance.id, instance.instance_type)
    return instances


def start_instances(ec2_instance_list):
    instance_id_list = []
    for ec2_instance in ec2_instance_list:
        instance_id_list.append(ec2_instance.instance_id)
    ec2 = boto3.client(EC2)
    ec2.start_instances(InstanceIds=instance_id_list)


def stop_instances(ec2_instance_list):
    instance_id_list = []
    for ec2_instance in ec2_instance_list:
        instance_id_list.append(ec2_instance.instance_id)
    ec2 = boto3.resource(EC2)
    ec2.instances.filter(InstanceIds=instance_id_list).stop()


def terminate_instances(ec2_instance_list):
    instance_id_list = []
    for ec2_instance in ec2_instance_list:
        instance_id_list.append(ec2_instance.instance_id)
    ec2 = boto3.resource(EC2)
    ec2.instances.filter(InstanceIds=instance_id_list).terminate()


def get_ec2_instance(instance_id):
    return Ec2Instance(instance_id)


def generate_simulation_folder_name(config):
    config_filename_path = Path(config[CONFIG_FILE])
    config_filename = config_filename_path.stem
    hostname = socket.getfqdn()
    pid = os.getpid()
    timestamp = datetime.now()

    return "SIM_{}-HOST_{}-PID_{}-DATETIME_{}-{}-{}T{}-{}-{}" \
        .format(config_filename, hostname, pid,
                timestamp.year, timestamp.month, timestamp.day, timestamp.hour, timestamp.minute, timestamp.second)


def generate_log_post_url(bucket, key):
    s3 = boto3.client(S3)
    return s3.generate_presigned_post(bucket, key) # Note that the URL will expire in 1 hour based on default settings


def generate_config_url(bucket, key):
    s3 = boto3.client(S3)
    return s3.generate_presigned_url( ClientMethod=GET_OBJECT, Params={ BUCKET: bucket, KEY: key }) 


def update_overseer_ip_address_in_config_file(config, overseer_ip_address, temp_name):
    temp_dir = tempfile.gettempdir()
    temp_path = Path(temp_dir) / temp_name
    logging.debug("Creating temp config file: {}".format(temp_path))
    temp_handle = open(temp_path, WRITE)  
    with open(config[CONFIG_FILE]) as config_file:
        json_config = json.load(config_file)
        json_config[OVERSEER][HOST] = str(overseer_ip_address)
        json.dump(json_config, temp_handle)
    temp_handle.close()
    return temp_path


def upload_and_rename_file_to_s3_bucket(bucket, source_file, s3_key):
    s3 = boto3.resource(S3)
    logging.debug("Uploading {} to bucket: {} with key: {}".format(source_file, bucket, s3_key))
    s3.Bucket(bucket).upload_file(source_file, s3_key)

