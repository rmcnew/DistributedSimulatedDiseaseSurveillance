# administrative coordination between nodes and overseer -- overseer functions
import zmq


def setup_zmq(config):
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:" + str(config['overseer_port']))
    ret_val = (context, socket)
    return ret_val


def shutdown_zmq(context, socket):
    socket.close()
    context.term()


def send_to_node(socket, node_id, message):
    encoded_node_id = node_id.encode()
    encoded_message = message.encode()
    socket.send_multipart([encoded_node_id, encoded_message])


def receive_from_nodes(socket):
    [encoded_node_id, encoded_reply] = socket.recv_multipart()
    node_id = encoded_node_id.decode()
    reply = encoded_reply.decode()
    ret_val = (node_id, reply)
    return ret_val
