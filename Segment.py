import json
import struct

from util import parse_number_to_fit_length


class Segment(object):
    HEADER_SIZE = 16
    MAX_SEGMENT_SIZE = 600
    HEADER_FORMAT = '<I I I I' + str(MAX_SEGMENT_SIZE) + 's'
    PACKET_SIZE = HEADER_SIZE + MAX_SEGMENT_SIZE

    def __init__(self, ack_no, sequence_no, window_size, segment_index, data):
        self.ack_no = ack_no
        self.sequence_no = sequence_no
        self.window_size = window_size
        self.segment_index = segment_index
        self.data = data

    def pack_segment(self):
        data_padding = self.MAX_SEGMENT_SIZE - len(self.data)
        self.data += ' ' * data_padding
        return struct.pack(
            self.HEADER_FORMAT, self.ack_no, self.sequence_no, self.window_size, self.segment_index, bytes(self.data, 'utf-8')
        )

    @classmethod
    def unpack_segment(cls, packed_segment):
        (cls.ack_no, cls.sequence_no, cls.window_size, cls.segment_index, cls.data) = \
            struct.unpack(Segment.HEADER_FORMAT, packed_segment)
        return cls
