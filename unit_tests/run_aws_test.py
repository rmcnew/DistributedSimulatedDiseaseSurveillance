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
                        level=logging.DEBUG)
    logging.debug(config)

    run_aws = RunAws(config)

    # create EC2 instances for all the nodes needed plus the overseer
    #ec2_instances = create_ec2_instances(len(config[NODES]) + 1)

    # start overseer EC2 instance
    #overseer_instance = ec2_instances[0]
    #overseer_instance.start()

    # start simulation node EC2 instances
    #simulation_node_instances = ec2_instances[1:]
    #start_instances(simulation_node_instances)

    # generate simulation folder name based on simulation config filename, hostname, PID, and start timestamp
    simulation_folder_name = generate_simulation_folder_name(config)

    # the simulation "folder" is just a prefix that is added on the S3 keys
    simulation_folder_prefix = "{}/".format(simulation_folder_name)
    logging.info("Using simulation prefix: {} in S3 bucket: {}".format(simulation_folder_prefix, LFSDS_S3_BUCKET))

    # generate signed POST URLs for log files
    log_post_urls = {}
    for node_id, role in config[NODES].items():
        log_key = "{}{}-{}.log".format(simulation_folder_prefix, role, node_id) 
        logging.debug("Generating log POST URL for key: {}".format(log_key))
        #log_post_url = generate_log_post_url(LFSDS_S3_BUCKET, log_key)
 	#log_post_urls[node_id] = log_post_url	

    # get overseer EC2 instance IP address
    overseer_ip_address = '7.7.7.7'

    # read in config file and update overseer IP address for in-memory config file
    temp_config_filename = update_overseer_ip_address_in_config_file(config, overseer_ip_address, simulation_folder_name)

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
