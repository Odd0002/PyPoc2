import helpers
import map_handler
import config
import chat_handler

import struct

def handle_init(proto_inst):
    helpers.send_map(map_handler.get_initial_map_compressed(), config.map_dims.x, config.map_dims.y, config.map_dims.z, proto_inst)
    handle_set_init_pos(proto_inst)
    
    handle_spawn_other_players(proto_inst)
    proto_inst.factory.data.players.append(proto_inst.player)
    chat_handler.handle_inform_player_spawn(proto_inst)

def handle_set_init_pos(proto_inst):
    is_long = helpers.get_extension_state(proto_inst.player, ('ExtEntityPositions', 1))
    spawn_packet = helpers.gen_player_spawn_packet(proto_inst.player, True, is_long)
    proto_inst.transport.write(spawn_packet)
    init_pos_packet = helpers.gen_player_pos_packet(proto_inst.player, True)
    proto_inst.transport.write(init_pos_packet)

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

def handle_pos_update_packet(data, proto_inst):
    tmp_player = proto_inst.player
    if helpers.get_extension_state(tmp_player, ('ExtEntityPositions', 1)):
        pos_data = struct.unpack('!bbiiicc', data)
    else:
        pos_data = struct.unpack('!bbhhhcc', data)
    tmp_player.update_pos(pos_data)