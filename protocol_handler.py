import struct

import helpers
import config
import recv_protocol
import map_handler
import commands


def handle_data_recv(proto_inst):
    packet_num = proto_inst.buf[0]
    packet_length = recv_protocol.get_packet_length(packet_num, proto_inst.player.get_extensions())

    #loop through all the data until there is none left
    while packet_length <= len(proto_inst.buf):
        #extract data and update buffer
        data = proto_inst.buf[:packet_length]
        proto_inst.buf = proto_inst.buf[packet_length:]
        
        handle_packet(packet_num, data, proto_inst)

        try:
            packet_num = proto_inst.buf[0]
            packet_length = recv_protocol.get_packet_length(packet_num, proto_inst.player.get_extensions())
        except IndexError:
            return
        except ValueError:
            print("Error! packet num, data and buf was", packet_num, data + proto_inst.buf)
            return

    

def handle_packet(packet_num, data, proto_inst):
    if not proto_inst.initialized:
        handle_initialization(packet_num, data, proto_inst)
        return
    if not proto_inst.CPE_done:
        handle_CPE(packet_num, data, proto_inst)
        return
    else:
        if packet_num == 5:
            handle_setblock_packet(data, proto_inst)
        if packet_num == 8:
            handle_pos_update_packet(data, proto_inst)
        if packet_num == 13:
            handle_chat_packet(data, proto_inst)
        if packet_num == 19:
            handle_customblock_support_packet(proto_inst)
        if packet_num == 43:
            handle_two_way_ping(data, proto_inst)
            pass
        #handle_packet(proto_inst)



def handle_initialization(packet_num, data, proto_inst):
        if (packet_num != 0):
            helpers.disconnect_protocol(proto_inst, "Wrong initial packet!")
        else:
            handle_login(packet_num, data, proto_inst)


def handle_login(packet_num, data, proto_inst):
    tmp_player = proto_inst.player
    tmp_player.set_proto_inst(proto_inst)
    client_info = struct.unpack('!bb64s64sb', data)


    player_name = client_info[2].decode('ibm437').strip()
    player_mppass = client_info[3].decode('ibm437').strip()
    
    if not handle_name_setup(proto_inst, player_name, player_mppass):
        return 
    handle_player_id_setup(proto_inst)
    if client_info[4] == 66:
        tmp_player.set_CPE(True)
        send_CPE(proto_inst)
    else:
        proto_inst.CPE_done = True
        finish_server_handshake(proto_inst)

    proto_inst.initialized = True

def handle_name_setup(proto_inst, name, mppass):
    if name in proto_inst.factory.data.ops:
       proto_inst.player.set_op(True)
    if name in proto_inst.factory.data.silentbanned:
        proto_inst.transport.loseConnection()
        return False
    if name in proto_inst.factory.data.crashbanned:
        pass
        return False
    if name in proto_inst.factory.data.banned:
        helpers.disconnect_protocol(proto_inst, "You are banned!")
        return False
    
    if config.CHECK_USERNAMES:
        if not helpers.check_username(name, mppass, proto_inst.factory.data.salt):
            helpers.disconnect_protocol(proto_inst, "Wrong MPPASS!")
            return False

    proto_inst.player.set_username(name)
    return True

def handle_player_id_setup(proto_inst):
    for i in range(128):
        if i not in proto_inst.factory.data.taken_ids:
            proto_inst.player.set_ID(i)
            proto_inst.factory.data.taken_ids.append(i)
            return


def send_CPE(proto_inst):
    extinfo_packet = helpers.gen_extinfo_packet(config.SOFTWARE, config.SERVER_CPE_EXTENSIONS)
    proto_inst.transport.write(extinfo_packet)

    for extension_info in config.SERVER_CPE_EXTENSIONS:
        extentry_packet = helpers.gen_extentry_packet(extension_info[0], extension_info[1])
        proto_inst.transport.write(extentry_packet)


def handle_CPE(packet_num, data, proto_inst):
    if (packet_num != 16 and packet_num != 17):
        helpers.disconnect_protocol(proto_inst, "Wrong CPE packet!")
        return
    if (packet_num == 16):
        handle_init_CPE(packet_num, data, proto_inst)
    else:
        handle_CPE_extension(packet_num, data, proto_inst)
    return


def handle_init_CPE(packet_num, data, proto_inst):
    tmp_player = proto_inst.player
    extinfo = struct.unpack('!b64sH', data)
    tmp_player.set_client_name(extinfo[1].decode('ibm437').strip())
    tmp_player.set_CPE_count(extinfo[2])


def handle_CPE_extension(packet_num, data, proto_inst):
    tmp_player = proto_inst.player

    extentry = struct.unpack('!b64sI', data)
    tmp_player.add_extension((extentry[1].decode('ibm437').strip(), extentry[2]))

    if tmp_player.CPE_count == len(tmp_player.get_extensions()):
        handle_CPE_done(proto_inst)
    return

def handle_customblock_support_packet(proto_inst):
    finish_server_handshake(proto_inst)
    pass

def handle_CPE_done(proto_inst):
    proto_inst.CPE_done = True
    if ('CustomBlocks', 1) in proto_inst.player.get_extensions():
        custom_block_support_packet = helpers.gen_customblock_support_packet(1)
        proto_inst.transport.write(custom_block_support_packet)
    else:
        finish_server_handshake(proto_inst)


def finish_server_handshake(proto_inst):
    handle_send_server_ident(proto_inst)
    helpers.send_map(map_handler.get_initial_map_compressed(), config.map_dims.x, config.map_dims.y, config.map_dims.z, proto_inst)
    handle_set_init_pos(proto_inst)
    if helpers.get_extension_state(proto_inst.player, ('MessageTypes', 1)):
        proto_inst.transport.write(helpers.gen_chat_packet('Curr pos:', 12))

    handle_reconnect(proto_inst)
    handle_spawn_other_players(proto_inst)
    proto_inst.factory.data.players.append(proto_inst.player)
    handle_inform_player_spawn(proto_inst)
    #set_up_player(proto_inst)

def handle_send_server_ident(proto_inst):
    is_op = proto_inst.player.is_op
    server_ident_packet = helpers.gen_server_ident_packet(config.NAME, config.MOTD, is_op)
    proto_inst.transport.write(server_ident_packet)

def handle_set_init_pos(proto_inst):
    is_long = helpers.get_extension_state(proto_inst.player, ('ExtEntityPositions', 1))
    spawn_packet = helpers.gen_player_spawn_packet(proto_inst.player, True, is_long)
    proto_inst.transport.write(spawn_packet)
    init_pos_packet = helpers.gen_player_pos_packet(proto_inst.player, True)
    proto_inst.transport.write(init_pos_packet)

def handle_reconnect(proto_inst):
    for other_player in proto_inst.factory.data.players:
        if (proto_inst.player.username == other_player.username):
            disconnect_packet = helpers.gen_disconnect_player_packet("Reconnected!")
            print("disconnect packet put!")
            other_player.proto_inst.transport.write(disconnect_packet)

def handle_spawn_other_players(proto_inst):
    tmp_player = proto_inst.player
    for other_player in proto_inst.factory.data.players:
        if other_player != tmp_player:
            tmp_is_long = helpers.get_extension_state(tmp_player, ('ExtEntityPositions', 1))
            other_is_long = helpers.get_extension_state(other_player, ('ExtEntityPositions', 1))
            spawn_tmp_player_packet = helpers.gen_player_spawn_packet(tmp_player, False, other_is_long)
            spawn_other_player_packet = helpers.gen_player_spawn_packet(other_player, False, tmp_is_long)
            other_player.add_packet(spawn_tmp_player_packet)
            tmp_player.add_packet(spawn_other_player_packet)


def handle_pos_update_packet(data, proto_inst):
    tmp_player = proto_inst.player
    if helpers.get_extension_state(tmp_player, ('ExtEntityPositions', 1)):
        pos_data = struct.unpack('!bbiiicc', data)
    else:
        pos_data = struct.unpack('!bbhhhcc', data)
    tmp_player.update_pos(pos_data)

def handle_two_way_ping(data, proto_inst):
    tmp_player = proto_inst.player
    ping_data = struct.unpack('!bBh', data)
    if ping_data[1] == 0:
        packet = helpers.gen_two_way_ping_packet(ping_data[2])
        tmp_player.add_packet(packet)

def handle_chat_packet(data, proto_inst):
    tmp_player = proto_inst.player
    chat_data = struct.unpack('!bb64s', data)
    if helpers.get_extension_state(tmp_player, ('LongerMessages', 1)):        
        tmp_player.add_msg(chat_data[2])
        if chat_data[1] == 0:
            handle_chat(tmp_player, proto_inst)
    else:
        tmp_player.add_msg(chat_data[2])
        handle_chat(tmp_player, proto_inst)

def handle_chat(tmp_player, proto_inst):
    messages = tmp_player.get_messages()
    if messages[0] == '/':
        commands.handle_command(messages, tmp_player, proto_inst)
    else:
        full_msg = tmp_player.displayname + r': %f' + messages
        full_msg_color = proto_inst.factory.data.colors_regex.sub('&', full_msg)
        
        packets_to_send = helpers.handle_gen_chat_packets(full_msg_color, len(tmp_player.displayname), 0)
        for curr_packet in packets_to_send:
            proto_inst.factory.data.chat_broadcast_queue.put((curr_packet, tmp_player.username))

def handle_setblock_packet(data, proto_inst):
    tmp_player = proto_inst.player
    setblock_data = struct.unpack('!bhhhcc', data)
    sb_x = setblock_data[1]
    sb_y = setblock_data[2]
    sb_z = setblock_data[3]
    sb_block = setblock_data[5]

    sb_absolute_x = sb_x + tmp_player.x_offset
    sb_absolute_z = sb_z + tmp_player.z_offset

    sb_delete = setblock_data[4]
    if sb_delete == b'\x00':
        sb_block = b'\x00'
    handle_setblock(sb_absolute_x, sb_y, sb_absolute_z, sb_block, proto_inst)

def handle_setblock(absolute_x, y, absolute_z, block, proto_inst):
    proto_inst.factory.data.setblock_queue.put((absolute_x, y, absolute_z, block, proto_inst.player))
    #block_info_update_handler.set_block(absolute_x, y, absolute_z, block, proto_inst.player)
    map_handler.set_block(absolute_x, y, absolute_z, block)

def handle_inform_player_spawn(proto_inst):
    spawn_chat_packet = helpers.gen_chat_packet(proto_inst.player.username + " connected!", 0)
    proto_inst.factory.data.chat_broadcast_queue.put((spawn_chat_packet, '**connections'))