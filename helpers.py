import random
import string
import hashlib
import struct
import ctypes

import config

def gen_salt():
    return 'sosalty'
    #return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(16))

def check_username(username, mppass, salt):
    to_hash = (salt + username).encode('ibm437')
    curr_hash = hashlib.md5(to_hash).hexdigest()
    if (curr_hash != mppass):
        return False
    else:
        return True

def read_file(filename):
    try:
        with open(filename) as f:
            return f.read().splitlines()
    except:
        return []

def prep_string(string_to_prep):
    return bytearray(string_to_prep.ljust(64)[0:64], 'ibm437')

def gen_disconnect_player_packet(reason):
    return b'\x0E' + prep_string(reason)

def disconnect_protocol(protocol_instance, reason):
    disconnect_packet = gen_disconnect_player_packet(reason)
    protocol_instance.transport.write(disconnect_packet)
    protocol_instance.transport.loseConnection()

def gen_set_texturepack_packet(url):
    return b'\x28' \
        + struct.pack('!64s', prep_string(url))

def gen_env_info_packet(env_setting, value):
    return b'\x29' \
        + struct.pack('!B', env_setting) \
        + struct.pack('!I', value)

def gen_level_init_packet():
    return b'\x02'

def gen_extinfo_packet(software_name, extension_list):
    data = b'\x10' \
        + struct.pack('!64s', prep_string(software_name)) \
        + struct.pack('!H', len(extension_list))
    return data

def gen_extentry_packet(extension_name, version):
    data = b'\x11' \
        + struct.pack('!64s', prep_string(extension_name)) \
        + struct.pack('!I', version)
    return data

def gen_server_ident_packet(server_name, server_MOTD, is_op):
    if is_op:
        op_byte = b'\x64'
    else:
        op_byte = b'\x00'
    data = b'\x00\x07' \
        + prep_string(server_name) \
        + prep_string(server_MOTD) \
        + op_byte
    return data

def gen_customblock_support_packet(version):
    data = b'\x13' \
        + struct.pack('!b', version)
    return data

def send_map(map_data, x_size, y_size, z_size, proto_inst):
    total_size = len(map_data) // 1024
    curr_data = map_data[0:1024]
    counter = 0
    proto_inst.transport.write(gen_level_init_packet())
    while (len(curr_data) != 0):

        curr_size = struct.pack('!h', len(curr_data))
        curr_data = curr_data.ljust(1024, b'\x00')
        complete_percent = (counter // total_size)

        data = b'\x03' + curr_size + curr_data + complete_percent.to_bytes(1, byteorder='big')
        proto_inst.transport.write(data)
        counter += 1

        curr_data = map_data[1024 * counter:1024 * (counter + 1)]

    dimensions = struct.pack('!hhh', x_size, y_size, z_size)
    proto_inst.transport.write(b'\x04' + dimensions)

def gen_player_spawn_packet(player, is_self, is_long):
    if (is_self):
        p_id = -1
    else:
        p_id = player.get_ID()

    return gen_spawn_packet(p_id, player.username, player.xpos, player.ypos, player.zpos, player.yaw, player.pitch, is_long)

def gen_player_pos_packet(player, is_self):
    if (is_self):
        p_id = -1
    else:
        p_id = player.get_ID()

    is_long = get_extension_state(player, ('ExtEntityPositions', 1))

    return gen_pos_packet(p_id, player.xpos, player.ypos, player.zpos, player.yaw, player.pitch, is_long)

def gen_spawn_packet(p_id, username, xpos, ypos, zpos, yaw, pitch, is_long):
    if is_long:
        pos_data = gen_long_pos_data(xpos, ypos, zpos, yaw, pitch)
    else:
        pos_data = gen_short_pos_data(xpos, ypos, zpos, yaw, pitch)
    data = b'\x07' + struct.pack('!b64s', p_id, prep_string(username)) + pos_data
    return data

def gen_pos_packet(p_id, xpos, ypos, zpos, yaw, pitch, is_long):
    if is_long:
        pos_data = gen_long_pos_data(xpos, ypos, zpos, yaw, pitch)
    else:
        pos_data = gen_short_pos_data(xpos, ypos, zpos, yaw, pitch)
    data = b'\x08' + struct.pack('!b', p_id) + pos_data
    return data

def gen_short_pos_data(xpos, ypos, zpos, yaw, pitch):
    xpos = ctypes.c_short(int(xpos)).value
    ypos = ctypes.c_short(int(ypos)).value
    zpos = ctypes.c_short(int(zpos)).value
    data = struct.pack('!hhh', xpos, ypos, zpos) \
        + struct.pack('!cc', yaw, pitch)
    return data

def gen_long_pos_data(xpos, ypos, zpos, yaw, pitch):
    data = struct.pack('!iii', xpos, ypos, zpos) \
        + struct.pack('!cc', yaw, pitch)
    return data

def gen_chat_packet(message, player_ID):
    try:
        decoded_message = message.decode('ibm437').strip()
    except AttributeError:
        decoded_message = message

    data = b'\x0D' \
        + struct.pack('!b64s', player_ID, prep_string(decoded_message))
    return data

def gen_despawn_packet(player_ID):
    data = b'\x0C' \
    + struct.pack('!b', player_ID)
    return data

def gen_setblock_packet(xpos, ypos, zpos, block_id):
    try:
        block_id = int.from_bytes(block_id, byteorder='big')
    except:
        pass
    data = b'\x06' \
        + struct.pack('!HHHB', int(xpos), int(ypos), int(zpos), block_id)
    return data

def gen_relative_pos_packet(sender, receiver):
    x_offset_diff = sender.x_offset - receiver.x_offset
    z_offset_diff = sender.z_offset - receiver.z_offset
    x_pos_calculated = (x_offset_diff * 32) + sender.xpos
    z_pos_calculated = (z_offset_diff * 32) + sender.zpos
    is_long = get_extension_state(receiver, ('ExtEntityPositions', 1))
    return gen_pos_packet(sender.player_ID, x_pos_calculated, sender.ypos, z_pos_calculated, sender.yaw, sender.pitch, is_long)


def gen_bbu_packets_fast(fast_blocks_info):
    bbu_packets = []
    for i in range(0, len(fast_blocks_info), 255):
        tmp_list = fast_blocks_info[i:i + 255]
        bbu_packets.append(gen_bulkblockupdate_packet(tmp_list, len(tmp_list)))
    return bbu_packets


def gen_bulkblockupdate_packet(blocks_info, blocks_count):
    data = b'\x26' \
        + struct.pack('!B', blocks_count)

    blocks_data = b''

    for i in range(256):
        try:
            data += struct.pack('!I', blocks_info[i][0])
            blocks_data += struct.pack('!B', blocks_info[i][1])
        except:
            data += struct.pack('!I', 0)
            blocks_data += struct.pack('!B', 0)
    return (data + blocks_data)


def handle_gen_chat_packets(msg_left, name_length, p_id):
    packets = []

    if len(msg_left) > 64:
        split_point = msg_left[:63].rfind(" ") + 1
        if split_point < name_length + 3:
            split_point = 64
        init_string_to_prep = msg_left[:split_point]
        init_string = prep_string(init_string_to_prep)
        packets.append(gen_chat_packet(init_string, p_id))    
        msg_left = msg_left[split_point:]
        while(len(msg_left) > 62):
            split_point = msg_left[:62].rfind(" ") + 1
            if split_point <= 0:
                split_point = 63
            string_to_prep = '>' + msg_left[:split_point]
            #print("string to prep:", string_to_prep)
            msg_string = prep_string(string_to_prep)
            packets.append(gen_chat_packet(msg_string, p_id))
            msg_left = msg_left[split_point:]

    msg_string = prep_string(msg_left)
    packets.append(gen_chat_packet(msg_string, p_id))
    return packets

def get_and_clear_queue(queue_1):
    with queue_1.mutex:
        data = list(queue_1.queue)
        queue_1.queue.clear()
        queue_1.all_tasks_done.notify_all()
        queue_1.unfinished_tasks = 0
    return data

def gen_relative_setblock_packet(receiver, block_info):
    x_offset_diff = block_info[0] - receiver.x_offset
    z_offset_diff = block_info[2] - receiver.z_offset
    if x_offset_diff < 0 or z_offset_diff < 0:
        return None
    else:
        return gen_setblock_packet(x_offset_diff, block_info[1], z_offset_diff, block_info[3])



def gen_ping_packet():
    return b'\x01'

def gen_two_way_ping_packet(num):
    data = b'\x2B' \
        + struct.pack('!Bh', 0, num)
    return data

def get_extension_state(player, extension):
    if extension in player.get_extensions() and extension in config.SERVER_CPE_EXTENSIONS:
        return True
    else:
        return False

