import config
import urllib
import time

import helpers
import map_handler

def heartbeat_handler(players, salt, g_data):
    while not g_data.shutdown:
        #print(players, salt)
        url_string = 'https://www.classicube.net/server/heartbeat/'
        values = {'name' : str(config.NAME), 'port' : str(config.PORT), \
                    'users' : str(len(players)), 'max' : str(config.MAX_USERS), \
                    'public' : str(config.PUBLIC).lower(), 'salt' : str(salt), \
                    'software' : str(config.SOFTWARE) }
        url_values = urllib.parse.urlencode(values)
        #print(url_values)
        full_url = url_string + '?' + url_values
        try:
            data = urllib.request.urlopen(full_url)
            #print(data.read())
        except Exception as e:
            print("Heartbeat failed:", e)
        
        for i in range(60):
            if not g_data.shutdown:
                time.sleep(1)



def update(data):
    delay = config.UPDATE_DELAY
    players = data.players
    ping_counter = 0
    save_counter = 0
    while not data.shutdown:
        try:
            if ping_counter == 5:
                handle_ping(players)
                ping_counter = 0
            else:
                ping_counter += 1

            if save_counter == config.AUTOSAVE_INTERVAL:
                map_handler.save_all_maps()
                maps_saved_msg = helpers.gen_chat_packet("Maps autosaved.", 0)
                data.chat_broadcast_queue.put((maps_saved_msg, '**autosaves'))
                save_counter = 0
            else:
                save_counter += 1

            handle_update_player_positions(players)
            handle_setblocks(data, players)
            handle_broadcast_chat(data, players)
            #send_player_packets(players)
            handle_player_removals(players)
        except Exception as e:
            print("bg update exception:", e)
            raise Exception
        time.sleep(delay)

def handle_ping(players):
    ping_packet = helpers.gen_ping_packet()
    for player in players:
        player.add_packet(ping_packet)


def handle_setblocks(data, players):
    setblocks = helpers.get_and_clear_queue(data.setblock_queue)

    for player in players:
        for block_info in setblocks:
            setblock_packet = helpers.gen_relative_setblock_packet(player, block_info)
            if setblock_packet is not None:
                player.add_packet(setblock_packet)
    for block_info in setblocks:
        #TODO Handle setting undo info
        pass

def handle_broadcast_chat(data, players):
    chat_broadcast_packets = helpers.get_and_clear_queue(data.chat_broadcast_queue)
    for player in players:
        for packet_info in chat_broadcast_packets:
            if packet_info[1] not in player.ignored_players:
                player.add_packet(packet_info[0])

def handle_update_player_positions(players):
    for player in players:
        curr_x_pos = player.x_offset + (player.xpos // 32) - config.map_dims.x // 2
        curr_z_pos = player.z_offset + (player.zpos // 32) - config.map_dims.z // 2
        if helpers.get_extension_state(player, ('MessageTypes', 1)):
            player.add_packet(helpers.gen_chat_packet("(" + str(curr_x_pos) + ", " + str(curr_z_pos) + ")", 11))
        for curr_player in players:
            if player != curr_player:
                loc_packet = helpers.gen_relative_pos_packet(player, curr_player)
                curr_player.add_packet(loc_packet)


def send_player_packets(players):
    for player in players:
        for packet in player.get_all_packets():
            player.proto_inst.transport.write(packet)
            if packet[0] == b'\x0d':
                print("packet sent:", packet)


def handle_player_removals(players):
    for player in players:
        if player.remove:
            player.proto_inst.transport.loseConnection()





def handle_player_disconnects(proto_inst):
    if proto_inst.player in proto_inst.factory.data.players:
            proto_inst.factory.data.players.remove(proto_inst.player)
            proto_inst.factory.data.taken_ids.remove(proto_inst.player.get_ID())

    print("player disconnected!")

    player_despawn_packet = helpers.gen_despawn_packet(proto_inst.player.get_ID())    
    disconnected_info_packet = helpers.gen_chat_packet(proto_inst.player.username + " disconnected!", 0)
    proto_inst.factory.data.chat_broadcast_queue.put((disconnected_info_packet, '**disconnections'))
    for player in proto_inst.factory.data.players:
        player.add_packet(player_despawn_packet)
