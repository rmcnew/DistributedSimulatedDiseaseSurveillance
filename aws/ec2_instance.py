import logging
from pathlib import Path

import boto3
import paramiko

from shared.constants import *


class Ec2Instance:

    ec2 = boto3.resource(EC2)
    ec2Client = boto3.client(EC2)
    key = paramiko.RSAKey.from_private_key_file(str(Path.home() / DOT_AWS / LFSDS_KEY_FILENAME))

    def __init__(self, instance_id):
        self.instance_id = instance_id
        self.instance = Ec2Instance.ec2.Instance(instance_id)
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy)
        self.ssh_succeeded = False  # wait a bit before attempting first SSH connection


    def start(self):
        self.instance.start()

    def stop(self):
        self.instance.stop()

    def terminate(self):
        self.instance.terminate()

    def get_public_ip_address(self):
        return self.instance.public_ip_address

    def get_public_dns_name(self):
        return self.instance.public_dns_name

    def ssh_connect(self):
        try:
            if not self.ssh_succeeded:
                self.ssh_client.connect(hostname=self.instance.public_ip_address,
                                        username=UBUNTU,
                                        timeout=SSH_TIMEOUT,
                                        auth_timeout=SSH_TIMEOUT,
                                        banner_timeout=SSH_TIMEOUT,
                                        pkey=Ec2Instance.key)
                self.ssh_succeeded = True

        except paramiko.AuthenticationException:
            print("AuthenticationException while connecting to {}".format(self.instance))

    def run_command(self, command):
        try:
            if not self.ssh_succeeded:
                self.ssh_connect()
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            ret_val = stdout.read()
            ret_err = stderr.read()
            logging.debug("stdout: {}".format(ret_val))
            logging.debug("stderr: {}".format(ret_err))
            return ret_val

        except paramiko.AuthenticationException:
            print("AuthenticationException while connecting to {}".format(self.instance))

    def ssh_close(self):
        self.ssh_client.close()

    def console_output(self):
        return self.instance.console_output()

    def wait_until_running(self):
        self.instance.wait_until_running()

    def wait_until_stopped(self):
        self.instance.wait_until_stopped()

    def wailt_until_terminated(self):
        self.instance.wait_until_terminated()


