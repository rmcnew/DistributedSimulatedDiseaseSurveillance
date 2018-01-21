# administrative coordination between nodes and overseer -- node functions
import zmq


def setup_zmq(config):
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://" + config['overseer_host'] + ":" + str(config['overseer_port']))
    ret_val = (context, socket)
    return ret_val


def shutdown_zmq(context, socket):
    socket.close()
    context.term()


def send_to_overseer(socket, node_id, message):
    print("Sending message: \'" + message + "\' from: \'" + node_id + "\'")
    encoded_node_id = node_id.encode()
    encoded_message = message.encode()
    socket.send_multipart([encoded_node_id, encoded_message])


def receive_from_overseer(socket, node_id):
    while True:
        [encoded_destination_node_id, encoded_reply] = socket.recv_multipart()
        destination_node_id = encoded_destination_node_id.decode()
        reply = encoded_reply.decode()
        if (node_id == destination_node_id) or ("ALL" == destination_node_id):
            return reply


# health_district_system nodes use REP listeners to receive
# electronic_medical_record messages and PUB listeners to publish
# messages to disease_outbreak_analyzers
def setup_health_district_system_zmq_listeners(context, config):
    # create listener zmq sockets and save IP address and ports in config
    electronic_medical_record_socket = context.socket(zmq.REP)
    electronic_medical_record_port = electronic_medical_record_socket.bind_to_random_port("tcp://*")