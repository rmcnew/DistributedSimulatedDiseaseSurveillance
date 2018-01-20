from config.sds_config import get_overseer_config
import zmq
import time

config = get_overseer_config()

# print(config)

context = zmq.Context()
socket = context.socket(zmq.REP)
socket.bind("tcp://*:" + str(config['overseer_port']))


message = socket.recv()
print("Received message: %s" % message)

time.sleep(1)

socket.send(b"Received")
