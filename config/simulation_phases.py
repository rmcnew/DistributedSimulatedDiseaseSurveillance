# shared configuration for the simulation phases

phases = ["REGISTER", "CONNECT", "RUN_SIMULATION", "SHUTDOWN"]


def get_simulation_phase(index):
    return phases[index]