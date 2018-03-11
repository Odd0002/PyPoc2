import helpers
import map_handler

def handle_command(cmd_txt, player, proto_inst):
    to_split = cmd_txt[1:]
    command_info = to_split.split(' ')
    cmd = command_info[0]
    if (cmd[0] == '/'):
        pass
    elif cmd == 'save':
        handle_save(proto_inst)
    elif cmd == 'kick':
        handle_kick(command_info, player, proto_inst)
    elif cmd == 'tp':
        handle_tp(command_info, player, proto_inst)

    pass


def handle_save(proto_inst):
    map_handler.save_all_maps()
    save_info = helpers.gen_chat_packet("All maps saved!", 0)
    proto_inst.factory.data.chat_broadcast_queue.put((save_info, '**saves'))

def handle_kick(command_info, player, proto_inst):
    if not player.is_op:
        handle_player_not_op(player)
    else:
        players_matched = get_players(command_info[1], proto_inst)
        if len(players_matched) > 1:
            players_list = ''
            for curr_player in players_matched:
                players_list += curr_player.username + " "
            info = helpers.handle_gen_chat_packets(r"More than 1 player matched: &6" + players_list, 0, 0)
            for packet in info:
                player.add_packet(packet)
        elif len(players_matched) == 1:
            helpers.disconnect_protocol(players_matched[0].proto_inst, "kicked by " + player.username)
        else:
            info = helpers.gen_chat_packet("No such player found.", 0)
            player.add_packet(info)

def handle_ban(command_info, player, proto_inst):
    if not player.is_op:
        handle_player_not_op(player)
    else:
        players_matched = get_players(command_info[1], proto_inst)
        if len(players_matched) > 1:
            players_list = ''
            for curr_player in players_matched:
                players_list += curr_player.username + " "
            info = helpers.handle_gen_chat_packets(r"More than 1 player matched: &6" + players_list, 0, 0)
            for packet in info:
                player.add_packet(packet)
        elif len(players_matched) == 1:
            proto_inst.factory.data.banned.append(players_matched[0].username)
            helpers.disconnect_protocol(players_matched[0].proto_inst, "kicked by " + player.username)
        else:
            info = helpers.gen_chat_packet("No such player found.", 0)
            player.add_packet(info)


def handle_tp(command_info, player, proto_inst):
    players_matched = get_players(command_info[1], proto_inst)
    if len(players_matched) > 1:
        players_list = ''
        for curr_player in players_matched:
            players_list += curr_player.username + " "
        info = helpers.handle_gen_chat_packets(r"More than 1 player matched: &6" + players_list, 0, 0)
        for packet in info:
            player.add_packet(packet)
    elif len(players_matched) == 1:
        dest_player = players_matched[0]
        is_long = helpers.get_extension_state(player, ('ExtEntityPositions', 1))
        tp_packet = helpers.gen_pos_packet(-1, dest_player.xpos, dest_player.ypos, dest_player.zpos, dest_player.yaw, dest_player.pitch, is_long)
        player.add_packet(tp_packet)
        player.teleport_to(dest_player)

        if not (player.x_offset == dest_player.x_offset and player.z_offset == dest_player.z_offset):
            map_handler.get_player_tp_map_data(player, dest_player)            
            player.teleport_to(dest_player)
    else:
        info = helpers.gen_chat_packet("No such player found.", 0)
        player.add_packet(info)



















def get_players(username, proto_inst):
    players_matched = []
    for player in proto_inst.factory.data.players:
        if username.lower() in player.username.lower():
            print(username.lower())
            players_matched.append(player)
    return players_matched






































def handle_player_not_op(player):
    info_packet = helpers.gen_chat_packet("You are not an operator!", 0)
    player.add_packet(info_packet)