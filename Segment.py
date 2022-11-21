import json

from util import parse_number_to_fit_length


class Segment:
    HEADER_SIZE = 73
    MAX_SEGMENT_SIZE = 951
    PACKET_SIZE = HEADER_SIZE + MAX_SEGMENT_SIZE

    def __int__(self, ack_no, sequence, window_size, data):
        self.ack_no = ack_no
        self.sequence = sequence
        self.window_size = window_size
        self.data = data

    def to_string(self):
        return json.dumps({
            "ack_no": parse_number_to_fit_length(self.ack_no),
            "sequence": parse_number_to_fit_length(self.sequence),
            "window_size": parse_number_to_fit_length(self.window_size),
            "data": self.data
        }).encode('utf-8')

    def to_json(self):
        return {
            "ack_no": parse_number_to_fit_length(self.ack_no),
            "sequence": parse_number_to_fit_length(self.sequence),
            "window_size": parse_number_to_fit_length(self.window_size),
            "data": self.data
        }
