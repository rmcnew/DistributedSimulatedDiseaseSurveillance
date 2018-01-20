from config.sds_config import get_node_config
import zmq

config = get_node_config("electronic_medical_record")

# print(config)

context = zmq.Context()
socket = context.socket(zmq.REQ)
socket.connect("tcp://" + config['overseer_host'] + ":" + str(config['overseer_port']))
message = ("Hello from " + config['node_id']).encode()
socket.send(message)
reply = socket.recv()
print("Received reply: " + str(reply))
