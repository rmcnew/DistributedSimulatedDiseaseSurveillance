# given a simulation configuration file and some AWS credentials via the command line, run a simulation using AWS EC2
import logging

from config.sds_config import get_runner_config
from shared.constants import *
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

    # use AWS credentials from command line to connect

    # create instance and start overseer

    # create instances and start simulation nodes

    # listen for Ctrl-C

    # upon Ctrl-C, send "stop_simulation" message to overseer

    # stop and shutdown simulation nodes

    # stop and shutdown overseer


if __name__ == "__main__":
    main()
