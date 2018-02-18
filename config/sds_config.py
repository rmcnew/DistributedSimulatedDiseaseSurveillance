# functions to parse command line options, read configuration file, and return config object to scripts
import json
import logging
import os
import requests

from config.command_line_parser import parse_node_cmd_line, parse_overseer_cmd_line, parse_runner_cmd_line
from config.json_config_extractor import extract_node_config, extract_overseer_config, extract_runner_config
from shared.constants import *


def get_node_config(role):
    args = parse_node_cmd_line()
    json_config = get_json_config(args.config_file)
    config = extract_node_config(json_config, args.node_id)
    if config[ROLE] != role:
        raise SyntaxError(args.node_id + " has role: " + config[ROLE] + " in the configuration file.  "
                          "This script is \'" + role + "\'. Please run the correct script for " + args.node_id)
    return config


def get_overseer_config():
    args = parse_overseer_cmd_line()
    json_config = get_json_config(args.config_file)
    config = extract_overseer_config(json_config)
    config[ROLE] = OVERSEER
    return config


def get_runner_config(role):
    args = parse_runner_cmd_line()
    json_config = get_json_config(args.config_file)
    config = extract_runner_config(json_config)
    config[CONFIG_FILE] = os.path.realpath(args.config_file)
    config[ROLE] = role
    return config


def get_json_config(args_config_file):
    print("args_config_file is: {}".format(args_config_file))
    if args_config_file.startswith(HTTPS):
        logging.info("Getting config file from URL: {}".format(args_config_file))
        response = requests.get(args_config_file)
        if response.status_code == 200:
            json_config = json.loads(response.text)
            return json_config
    else:
        logging.info("Getting config file from file: {}".format(args_config_file))
        with open(args_config_file) as config_file:
            json_config = json.load(config_file)
            return json_config
