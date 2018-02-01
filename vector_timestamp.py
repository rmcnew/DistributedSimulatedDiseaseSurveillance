# implement a simple vector clock


class VectorTimestamp:

    def __init__(self):
        self.vector_timestamp = {}

    def increment_count(self, node_id):
        if node_id in self.vector_timestamp:
            self.vector_timestamp[node_id] = self.vector_timestamp[node_id] + 1
        else:
            self.vector_timestamp[node_id] = 1

    def update_from_other(self, other_vector_timestamp):
        # iterate through the other_vector_timestamp
        for node_id, other_count in other_vector_timestamp.items():
            # if vector_timestamp has the node_id, use the max of the two counts
            if node_id in self.vector_timestamp:
                my_count = self.vector_timestamp[node_id]
                max_count = max(my_count, other_count)
                self.vector_timestamp[node_id] = max_count
            else:  # otherwise, copy the other_count into vector_timestamp
                self.vector_timestamp[node_id] = other_count

    def items(self):
        return self.vector_timestamp.items()

    def __repr__(self):
        return str(self.vector_timestamp)
