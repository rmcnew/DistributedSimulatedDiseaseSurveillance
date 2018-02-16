# given a simulation configuration file and some AWS credentials via the command line, run a simulation using AWS EC2
import logging

from aws.aws_helper import *
from config.sds_config import get_runner_config
from shared.run import Run


class RunAws(Run):

    def __init__(self, config):
        super(RunAws, self).__init__(config)


def main():
    config = get_runner_config(RUN_AWS)
    logging.basicConfig(format='%(message)s',
                        # filename="{}.log".format(config[ROLE]),
                        level=logging.INFO, )
    logging.debug(config)

    run_aws = RunAws(config)

    logging.info("Running LFSDS on AWS is under construction and will be coming soon!")

    # create EC2 instances for all the nodes needed plus the overseer
    instances = create_ec2_instances(len(config[NODES]) + 1)

    overseer_instance_id = instances[0].instance_id
    start_instances([overseer_instance_id])
    overseer_instance = get_instance(overseer_instance_id)

    # create and start simulation node EC2 instances

    # generate mktemp-style simulation folder name based on simulation config filename

    # create simulation folder in S3 bucket

    # generate signed POST URLs for log files

    # get overseer EC2 instance IP address

    # read in config file

    # update overseer IP address for in-memory config file

    # save updated config file to local temp location (/tmp)

    # upload updated config file to S3 simulation folder

    # generate signed URL for config file

    # start overseer script with config file URL and log POST URL

    # start simulation node scripts with config file URL, node_id, and respective log POST URL

    # simulation nodes send heartbeats to overseer every two minutes.  Overseer checks each minute to see if no
    # heartbeat is received.  Overseer alerts if no heartbeats received from a node for five minutes or more

    # at stop_simulation, each simulation node sends logs using the respective log POST URL

    # after log is uploaded, each simulation node sends a "deregister" message to the overseer and
    # then performs shutdown




if __name__ == "__main__":
    main()
