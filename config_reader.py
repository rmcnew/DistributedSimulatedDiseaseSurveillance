import json


def extract_overseer(config, json_config):
    config['overseer_host'] = json_config['overseer']['host']
    config['overseer_port'] = json_config['overseer']['port']


def extract_time_scaling_factor(config, json_config):
    config['time_scaling_factor'] = json_config['time_scaling_factor']


def extract_diseases(config, json_config):
    config['diseases'] = json_config['diseases']


def extract_node_names(config, json_config):
    config['nodes'] = list(json_config['nodes'].keys())


def load_overseer_config(json_config_file):
    config = {}
    with open(json_config_file) as config_file:
        json_config = json.load(config_file)
        extract_overseer(config, json_config)
        extract_time_scaling_factor(config, json_config)
        extract_diseases(config, json_config)
        extract_node_names(config, json_config)
        return config

# TODO:  Add functions to extract needed config for EMR, HDS, and DOA
