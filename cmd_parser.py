import argparse


def parse_overseer_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("config_file", help="the simulation configuration file in JSON format")
    args = parser.parse_args()
    return args


def parse_cmd_line():
    parser = argparse.ArgumentParser()
    parser.add_argument("node_id", help="the node_id to specify the role and parameters of "
                                        "this program as found in the config_file")
    parser.add_argument("config_file", help="the simulation configuration file in JSON format")
    args = parser.parse_args()
    return args
