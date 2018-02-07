# given a simulation configuration file, run a simulation on the local host
import logging
import time

from config.sds_config import get_runner_config
from shared.constants import *
from shared.run import Run


class RunLocal(Run):

    def __init__(self, config):
        super(RunLocal, self).__init__(config)


def main():
    config = get_runner_config(RUN_LOCAL)
    logging.basicConfig(format='%(message)s',
                        # filename="{}.log".format(config[ROLE]),
                        level=logging.INFO, )
    logging.debug(config)

    run_local = RunLocal(config)

    overseer_command_line = run_local.build_overseer_command_line()
    # logging.debug("overseer command line is: {}".format(overseer_command_line))

    simulation_node_command_lines = run_local.build_simulation_node_command_lines()
    # logging.debug("simulation node command lines are: {}".format(simulation_node_command_lines))

    # start overseer
    logging.info("Starting the Overseer . . .")
    run_local.run_in_own_process(OVERSEER, overseer_command_line)

    # start simulation nodes
    for sim_node_id, sim_node_command_line in simulation_node_command_lines.items():
        logging.info("Starting simulation node_id: {}".format(sim_node_id))
        run_local.run_in_own_process(sim_node_id, sim_node_command_line)
        time.sleep(1)

    # wait until all child processes are started before creating zmq context
    run_local.connect_to_overseer()

    logging.info("Simulation is starting.  Press Ctrl-C to stop the simulation.")
    # listen for Ctrl-C
    while True:
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            break

    # upon Ctrl-C, send "stop_simulation" message to overseer
    logging.info("\nSending stop_simulation to Overseer . . .")
    run_local.send_to_overseer(STOP_SIMULATION)
    reply = run_local.receive_from_overseer()
    logging.debug("Overseer reply: {}".format(reply))

    for node_id, process in run_local.processes.items():
        logging.debug("Joining {}".format(node_id))
        process.join()
    logging.info("All simulation processes stopped.  Exiting . . .")


if __name__ == "__main__":
    main()
