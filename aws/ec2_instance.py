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

    def run_command(self, command):
        try:
            self.instance.wait_until_running()
            self.ssh_client.connect(hostname=self.instance.public_ip_address, username=UBUNTU, pkey=Ec2Instance.key)
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            ret_val = stdout.read()
            self.ssh_client.close()
            return ret_val

        except paramiko.AuthenticationException:
            print("AuthenticationException while connecting to {}".format(self.instance))

    def console_output(self):
        return self.instance.console_output()

    def wait_until_running(self):
        self.instance.wait_until_running()

    def wait_until_stopped(self):
        self.instance.wait_until_stopped()

    def wailt_until_terminated(self):
        self.instance.wait_until_terminated()


