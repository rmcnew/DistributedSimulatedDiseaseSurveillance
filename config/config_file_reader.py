# functions to parse and extract data from JSON-formatted network configuration file
import json


def extract_overseer(config, json_config):
    config['overseer_host'] = json_config['overseer']['host']
    config['overseer_reply_port'] = json_config['overseer']['reply_port']
    config['overseer_publish_port'] = json_config['overseer']['publish_port']


def extract_time_scaling_factor(config, json_config):
    config['time_scaling_factor'] = json_config['time_scaling_factor']


def extract_diseases(config, json_config):
    config['diseases'] = json_config['diseases']


def extract_node_names(config, json_config):
    config['nodes'] = list(json_config['nodes'].keys())


def extract_node(config, json_config, node_id):
    if node_id in json_config["nodes"]:
        node = json_config["nodes"][node_id]
        config['node_id'] = node_id
        config['role'] = node['role']
        config['role_parameters'] = node['role_parameters']
        config['connections'] = node['connections']
    else:
        raise KeyError("node_id: " + node_id + " was not found in the configuration file!")


def load_node_config(json_config_file, node_id):
    config = {}
    with open(json_config_file) as config_file:
        json_config = json.load(config_file)
        extract_overseer(config, json_config)
        extract_time_scaling_factor(config, json_config)
        extract_diseases(config, json_config)
        extract_node(config, json_config, node_id)
        return config


def load_overseer_config(json_config_file):
    config = {}
    with open(json_config_file) as config_file:
        json_config = json.load(config_file)
        extract_overseer(config, json_config)
        extract_time_scaling_factor(config, json_config)
        extract_diseases(config, json_config)
        extract_node_names(config, json_config)
        return config
