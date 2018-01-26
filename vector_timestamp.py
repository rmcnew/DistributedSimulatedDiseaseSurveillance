# implement a simple vector clock

def new_vector_timestamp():
    return {};

def increment_my_vector_timestamp_count(vector_timestamp, node_id):
    if node_id in vector_timestamp:
        vector_timestamp[node_id] = vector_timestamp[node_id] + 1
    else:
        vector_timestamp[node_id] = 1


def update_my_vector_timestamp(my_vector_timestamp, other_vector_timestamp):
    # iterate through the other_vector_timestamp
    for node_id, other_count in other_vector_timestamp:
        # if my_vector_timestamp has the node_id, use the max of the two counts
        if node_id in my_vector_timestamp:
            my_count = my_vector_timestamp[node_id]
            max_count = max(my_count, other_count)
            my_vector_timestamp[node_id] = max_count
        else:  # otherwise, copy the other_count into my_vector_timestamp
            my_vector_timestamp[node_id] = other_count
