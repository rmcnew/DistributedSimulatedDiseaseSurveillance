# functions to parse command line options, read configuration file, and return config object to scripts
from config.command_line_parser import parse_cmd_line, parse_overseer_cmd_line
from config.config_file_reader import load_node_config, load_overseer_config
from shared.constants import *


def get_node_config(role):
    args = parse_cmd_line()
    config = load_node_config(args.config_file, args.node_id)
    # print(config)

    if config[ROLE] != role:
        raise SyntaxError(args.node_id + " has role: " + config[ROLE] + " in the configuration file.  "
                          "This script is \'" + role + "\'. Please run the correct script for " + args.node_id)
    return config


def get_overseer_config():
    args = parse_overseer_cmd_line()
    config = load_overseer_config(args.config_file)
    # print(config)
    return config
