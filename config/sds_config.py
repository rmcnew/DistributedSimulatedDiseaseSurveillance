# functions to parse command line options, read configuration file, and return config object to scripts
import json
import os

import requests

from config.command_line_parser import parse_node_cmd_line, parse_overseer_cmd_line, parse_runner_cmd_line
from config.json_config_extractor import extract_node_config, extract_overseer_config, extract_runner_config
from shared.constants import *


def get_node_config(role):
    config = {}
    args = parse_node_cmd_line()
    if args.log_post_url:
        config[LOG_POST_URL] = args.log_post_url
    if args.public_ip_address:
        config[PUBLIC_IP_ADDRESS] = args.public_ip_address
    json_config = get_json_config(config, args.config_file)
    extract_node_config(config, json_config, args.node_id)
    if config[ROLE] != role:
        raise SyntaxError(args.node_id + " has role: " + config[ROLE] + " in the configuration file.  "
                          "This script is \'" + role + "\'. Please run the correct script for " + args.node_id)
    return config


def get_overseer_config():
    config = {}
    args = parse_overseer_cmd_line()
    if args.log_post_url:
        config[LOG_POST_URL] = args.log_post_url
    json_config = get_json_config(config, args.config_file)
    extract_overseer_config(config, json_config)
    config[ROLE] = OVERSEER
    return config


def get_runner_config(role):
    config = {}
    args = parse_runner_cmd_line()
    json_config = get_json_config(config, args.config_file)
    extract_runner_config(config, json_config)
    config[ROLE] = role
    return config


def get_json_config(config, args_config_file):
    if args_config_file.startswith(HTTPS):
        print("Getting config file from URL: {}".format(args_config_file))
        config[CONFIG_FILE] = args_config_file
        response = requests.get(args_config_file)
        if response.status_code == 200:
            json_config = json.loads(response.text)
            return json_config
    else:
        print("Getting config file from file: {}".format(args_config_file))
        config[CONFIG_FILE] = os.path.realpath(args_config_file)
        with open(args_config_file) as config_file:
            json_config = json.load(config_file)
            return json_config
