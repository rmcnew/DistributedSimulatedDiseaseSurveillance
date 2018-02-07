# given a simulation configuration file and some AWS credentials via the command line, run a simulation using AWS EC2
import logging
from logging.handlers import RotatingFileHandler

from config.sds_config import get_runner_config
from shared.constants import *
from shared.run import Run


class RunAws(Run):

    def __init__(self, config):
        super(RunAws, self).__init__(config)


def main():
    config = get_runner_config()
    logging.basicConfig(level=logging.INFO, format='%(message)s')

    if config[LOG_TO_CONSOLE]:
        file_logger = RotatingFileHandler("run_aws.log", APPEND, LOG_MAX_SIZE, LOG_BACKUP_COUNT)
        file_logger.setLevel(logging.INFO)
        logging.getLogger('').addHandler(file_logger)

    logging.debug(config)

    # use AWS credentials from command line to connect

    # create instance and start overseer

    # create instances and start simulation nodes

    # listen for Ctrl-C

    # upon Ctrl-C, send "stop_simulation" message to overseer

    # stop and shutdown simulation nodes

    # stop and shutdown overseer


if __name__ == "__main__":
    main()
