import config

cpe_packets = [16,      #ExtInfo packet, 0x10
               17,      #ExtEntry packet, 0x11
               19,      #CustomBlockSupportLevel, 0x13
               34,
               43       #TwoWayPing
               ]

modified_packets = [8   #Position and orientation update
                    ]

default_packet_lengths = {  0: 131,     #Identity packet, 0x00
                            5: 9,       #Set block packet, 0x05
                            8: 10,      #Position and orientation update, 0x08
                            13: 66      #Chat, 0x0d
}

def get_packet_length(packet_num, cpe_extensions):
    if packet_num not in cpe_packets and packet_num not in modified_packets:
        try:
            return default_packet_lengths[packet_num]
        except:
            raise ValueError
    else:
        return get_CPE_packet_length(packet_num, cpe_extensions)

def get_CPE_packet_length(packet_num, cpe_extensions):
    if packet_num in modified_packets:
        return get_modified_packet_length(packet_num, cpe_extensions)
    if packet_num in cpe_packets:
        return get_normal_CPE_packet_length(packet_num, cpe_extensions)
    
    
def get_modified_packet_length(packet_num, cpe_extensions):
    if (packet_num == 8):
        if ("ExtEntityPositions", 1) in cpe_extensions and ('ExtEntityPositions', 1) in config.SERVER_CPE_EXTENSIONS:
            return 16
        else:
            return default_packet_lengths[8]


def get_normal_CPE_packet_length(packet_num, cpe_extensions):
    if (packet_num == 16):
        return 67
    if (packet_num == 17):
        return 69
    if (packet_num == 19):
        if ('CustomBlocks', 1) in cpe_extensions and ('CustomBlocks', 1) in config.SERVER_CPE_EXTENSIONS:
            return 2
    if (packet_num == 34):
        if ("PlayerClicked", 1) in cpe_extensions and ("PlayerClicked", 1) in config.SERVER_CPE_EXTENSIONS:
            return 15
    if (packet_num == 43):
        if ('TwoWayPing', 1) in cpe_extensions and ('TwoWayPing', 1) in config.SERVER_CPE_EXTENSIONS:
            return 4

    raise ValueError