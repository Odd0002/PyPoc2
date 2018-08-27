import helpers
import commands

import struct

import protocol_handlers

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

    # if it's a command then process it and return
    if messages[1] != '/' and commands.process_if_command(tmp_player, messages, proto_inst):
        return

    if messages[0] == '/':
        messages = messages[1:]
    full_msg = tmp_player.displayname + r': %f' + messages
    full_msg_color = proto_inst.factory.data.colors_regex.sub('&', full_msg)

    packets_to_send = helpers.handle_gen_chat_packets(full_msg_color, len(tmp_player.displayname), 0)
    for curr_packet in packets_to_send:
        proto_inst.factory.data.chat_broadcast_queue.put((curr_packet, tmp_player.username))




def handle_inform_player_spawn(proto_inst):
    spawn_chat_packet = helpers.gen_chat_packet(proto_inst.player.username + " connected!", 0)
    proto_inst.factory.data.chat_broadcast_queue.put((spawn_chat_packet, '**connections'))


protocol_handlers.register_packet_handler(1, handle_chat_packet)