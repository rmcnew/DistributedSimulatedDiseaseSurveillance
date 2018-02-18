# functions to parse and extract data from JSON-formatted network configuration file
from shared.constants import *


def extract_overseer(config, json_config):
    config[OVERSEER_HOST] = json_config[OVERSEER][HOST]
    config[OVERSEER_REPLY_PORT] = json_config[OVERSEER][REPLY_PORT]
    config[OVERSEER_PUBLISH_PORT] = json_config[OVERSEER][PUBLISH_PORT]


def extract_time_scaling_factor(config, json_config):
    config[TIME_SCALING_FACTOR] = json_config[TIME_SCALING_FACTOR]


def extract_diseases(config, json_config):
    config[DISEASES] = json_config[DISEASES]


def extract_node_names(config, json_config):
    config[NODES] = list(json_config[NODES].keys())


def extract_node_roles(config, json_config):
    config[NODES] = {}
    for node_id in json_config[NODES]:
        node = json_config[NODES][node_id]
        config[NODES][node_id] = node[ROLE]


def extract_node(config, json_config, node_id):
    if node_id in json_config[NODES]:
        node = json_config[NODES][node_id]
        config[NODE_ID] = node_id
        config[ROLE] = node[ROLE]
        config[ROLE_PARAMETERS] = node[ROLE_PARAMETERS]
        config[CONNECTIONS] = node[CONNECTIONS]
    else:
        raise KeyError("node_id: " + node_id + " was not found in the configuration file!")


def extract_node_config(json_config, node_id):
    config = {}
    extract_overseer(config, json_config)
    extract_time_scaling_factor(config, json_config)
    extract_diseases(config, json_config)
    extract_node(config, json_config, node_id)
    return config


def extract_overseer_config(json_config):
    config = {}
    extract_overseer(config, json_config)
    extract_time_scaling_factor(config, json_config)
    extract_diseases(config, json_config)
    extract_node_names(config, json_config)
    return config


def extract_runner_config(json_config):
    config = {}
    extract_overseer(config, json_config)
    extract_node_roles(config, json_config)
    return config
