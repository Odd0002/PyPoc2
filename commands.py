import helpers
import map_handler

# Commands are inserted into this dictionary
commands = dict()

def register_command(command, function, argumentNum, permissionLevel, helpString):
    commands[command] = [ function, argumentNum, permissionLevel, helpString ]

def command_handle_help(player, args, proto_inst):
    if (len(args) > 0):
        commandName = args[0]

        if (not commandName in commands):
            player.add_packet(helpers.gen_chat_packet("No such command: " + commandName, 0))
            return

        helpString = commands[commandName][3]
        player.add_packet(helpers.gen_chat_packet(helpString, 0))
        return

    player.add_packet(helpers.gen_chat_packet("--- Commands: ---", 0))
    for key, value in commands.items():
        helpString = value[3]
        player.add_packet(helpers.gen_chat_packet(helpString, 0))
    player.add_packet(helpers.gen_chat_packet("---", 0))

def command_handle_kick(player, args, proto_inst):
    name = args[0]
    reason = ""

    if (len(args) > 1):
        reason = " (" + " ".join(args[1:]) + ")"

    players_matched = get_players(name, proto_inst)
    if len(players_matched) > 1:
        players_list = ''
        for curr_player in players_matched:
            players_list += curr_player.username + " "
        info = helpers.handle_gen_chat_packets(r"More than 1 player matched: &6" + players_list, 0, 0)
        for packet in info:
            player.add_packet(packet)
    elif len(players_matched) == 1:
        helpers.disconnect_protocol(players_matched[0].proto_inst, "kicked by " + player.username + reason)
    else:
        info = helpers.gen_chat_packet("No such player found.", 0)
        player.add_packet(info)

def command_handle_save(player, args, proto_inst):
    map_handler.save_all_maps()
    save_info = helpers.gen_chat_packet("All maps saved!", 0)
    proto_inst.factory.data.chat_broadcast_queue.put((save_info, '**saves'))

def command_handle_ban(player, args, proto_inst):
    name = args[0]
    reason = ""

    if (len(args) > 1):
        reason = " (" + " ".join(args[1:]) + ")"

    players_matched = get_players(name, proto_inst)
    if len(players_matched) > 1:
        players_list = ''
        for curr_player in players_matched:
            players_list += curr_player.username + " "
        info = helpers.handle_gen_chat_packets(r"More than 1 player matched: &6" + players_list, 0, 0)
        for packet in info:
            player.add_packet(packet)
    elif len(players_matched) == 1:
        proto_inst.factory.data.banned.append(players_matched[0].username)
        helpers.disconnect_protocol(players_matched[0].proto_inst, "kicked by " + player.username + reason)
    else:
        info = helpers.gen_chat_packet("No such player found.", 0)
        player.add_packet(info)

def command_handle_tp(player, args, proto_inst):
    name = args[0]

    players_matched = get_players(name, proto_inst)
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

##############################
# Register all commands here #
##############################
register_command("help", command_handle_help, 0, 0, "/help - displays command list")
register_command("kick", command_handle_kick, 1, 1, "/kick <player> [reason] - kicks player from server")
register_command("save", command_handle_save, 0, 1, "/save - saves map")
register_command("ban", command_handle_ban, 1, 1, "/ban <player> [reason] - bans player from server")
register_command("tp", command_handle_tp, 1, 0, "/tp <player> - teleports to player")

def handle_command(player, commandName, args, proto_inst):
    if (not commandName in commands):
        player.add_packet(helpers.gen_chat_packet("No such command: " + commandName, 0))
        return

    command = commands[commandName]

    function = command[0]
    argumentNum = command[1]
    permissionLevel = command[2]

    if (permissionLevel >= 1 and not player.is_op):
        handle_player_not_op(player)
        return

    if (len(args) < argumentNum):
        command_handle_help(player, [commandName], proto_inst)
        return

    # Call command function
    function(player, args, proto_inst)

# returns True if command, False if not
def process_if_command(player, inputString, proto_inst):
    if (inputString[0] == '/'):
        inputString = " ".join(inputString.split())
        commandTable = inputString[1:].split(' ')

        handle_command(player, commandTable[0].lower(), commandTable[1:], proto_inst)
        return True

    return False

####################
# Helper functions #
####################

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
