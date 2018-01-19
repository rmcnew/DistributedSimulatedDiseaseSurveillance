from cmd_parser import parse_overseer_cmd_line
from config_reader import load_overseer_config

args = parse_overseer_cmd_line()
config = load_overseer_config(args.config_file)
print(config)
