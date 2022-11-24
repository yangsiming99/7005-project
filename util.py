import json
import math
import struct


def parse_number_to_fit_length(number):
    length = len(str(number))
    result = str(number)
    if length < 4:
        result = "0" * (4 - length) + str(number)
    return result


def pack_segment(ack_no, sequence, data, window_size):
    return json.dumps({
        "ack_no": parse_number_to_fit_length(ack_no),
        "sequence": parse_number_to_fit_length(sequence),
        "window_size": parse_number_to_fit_length(window_size),
        "data": data
    }).encode('utf-8')


def get_data_index(segment_size, number):
    return segment_size * number

