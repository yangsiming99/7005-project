import struct


class Segment(object):
    HEADER_SIZE = 17
    MAX_SEGMENT_SIZE = 600
    HEADER_FORMAT = '<I I I I ?' + str(MAX_SEGMENT_SIZE) + 's'
    PACKET_SIZE = HEADER_SIZE + MAX_SEGMENT_SIZE
    TIME_OUT = 2.0
    INIT_WINDOW_SIZE = 5

    def __init__(self, ack_no, sequence_no, window_size, segment_index, retransmit, data):
        self.ack_no = ack_no
        self.sequence_no = sequence_no
        self.window_size = window_size
        self.segment_index = segment_index
        self.retransmit = retransmit
        self.data = data

    def pack_segment(self):
        data_padding = self.MAX_SEGMENT_SIZE - len(self.data)
        self.data += ' ' * data_padding
        return struct.pack(
            self.HEADER_FORMAT,
            self.ack_no,
            self.sequence_no,
            self.window_size,
            self.segment_index,
            self.retransmit,
            bytes(self.data, 'utf-8')
        )

    def set_retransmit(self, retransmit):
        self.retransmit = retransmit

    @classmethod
    def unpack_segment(cls, packed_segment):
        (cls.ack_no, cls.sequence_no, cls.window_size, cls.segment_index, cls.retransmit, cls.data) = \
            struct.unpack(Segment.HEADER_FORMAT, packed_segment)
        return cls
