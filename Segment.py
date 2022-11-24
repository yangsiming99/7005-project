import json
import struct

from util import parse_number_to_fit_length


class Segment:
    HEADER_SIZE = 20
    MAX_SEGMENT_SIZE = 556
    HEADER_FORMAT = 'I I L' + str(MAX_SEGMENT_SIZE) + 's'
    PACKET_SIZE = HEADER_SIZE + MAX_SEGMENT_SIZE

    def __int__(self, ack_no, sequence, window_size, data):
        self.ack_no = ack_no
        self.sequence = sequence
        self.window_size = window_size
        self.data = data

    def pack_segment(self):
        data_padding = self.MAX_SEGMENT_SIZE - len(self.data)
        self.data += ' ' * data_padding
        return struct.pack(self.HEADER_FORMAT, self.ack_no, self.sequence, self.window_size, str(self.data))

    @classmethod
    def unpack_segment(cls, packed_segment):
        (cls.ack_no, cls.sequence, cls.window_size, cls.data) = struct.unpack(Segment.HEADER_FORMAT, packed_segment)
        return cls
