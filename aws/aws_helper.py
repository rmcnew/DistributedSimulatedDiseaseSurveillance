# aws functions
from pathlib import Path

import boto3
import paramiko

from shared.constants import *


def create_ec2_instances(count):
    ec2 = boto3.resource(EC2)
    instances = ec2.create_instances(
        ImageId=UBUNTU_PYTHON3_AMI_ID,
        MinCount=count,
        MaxCount=count,
        SecurityGroupIds=[LFSDS_SECURITY_GROUP_ID],
        KeyName=LFSDS_KEY_NAME,
        InstanceType=T2_MICRO)
    return instances


def get_running_instances():
    ec2 = boto3.resource(EC2)
    instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    for instance in instances:
        print(instance.id, instance.instance_type)
    return instances


def start_instances(instance_id_list):
    ec2 = boto3.client(EC2)
    ec2.start_instances(InstanceIds=instance_id_list)


def stop_instances(instance_id_list):
    ec2 = boto3.resource(EC2)
    ec2.instances.filter(InstanceIds=instance_id_list).stop()


def terminate_instances(instance_id_list):
    ec2 = boto3.resource(EC2)
    ec2.instances.filter(InstanceIds=instance_id_list).terminate()


def run_command(instance, command):
    key = paramiko.RSAKey.from_private_key_file(str(Path.home() / DOT_AWS / LFSDS_KEY_FILENAME))
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)

    try:
        ssh_client.connect(hostname=instance.public_ip_address, pkey=key)
        stdin, stdout, stderr = ssh_client.exec_command(command)
        ret_val = stdout.read()
        ssh_client.close()
        return ret_val

    except paramiko.AuthenticationException:
        print("AuthenticationException while connecting to {}".format(instance))
