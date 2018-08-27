import struct
import hashlib
import helpers
import map_protocol_handler
import chat_handler
import config


#Login handling, including ban checking, name setup, CPE extensions exchange, player setup, etc
def handle_login(packet_num, data, proto_inst):
    #Populate the player's protocol instance
    #TODO restructure the server to not require this?
    tmp_player = proto_inst.player
    tmp_player.set_proto_inst(proto_inst)

    #Decode the packet
    client_info = struct.unpack('!bb64s64sb', data)

    #Extract the player's username and mppass, to be used later
    player_name = client_info[2].decode('ibm437').strip()
    player_mppass = client_info[3].decode('ibm437').strip()
    
    #Handle everything that we can now that we know the player's username and MPPASS
    if not handle_name_setup(proto_inst, player_name, player_mppass):
        return

    #Give the player an ID
    if not handle_player_id_setup(proto_inst):
        return

    #If the magic flag is set, enable CPE for the player and send them our list of supported CPE packets
    if client_info[4] == 66:
        tmp_player.set_CPE(True)
        cpe_protocol_handler.send_CPE(proto_inst)
    #Otherwise just finish the handshake
    else:
        finish_server_handshake(proto_inst)



#Handle the player's username, including making them op or disconnecting them if they're banned
def handle_name_setup(proto_inst, name, mppass):
    #If the player is silentbanned, quietly disconnect them
    if name in proto_inst.factory.data.silentbanned:
        proto_inst.transport.loseConnection()
        return False

    #If the player is crashbanned, do nothing (yet)
    if name in proto_inst.factory.data.crashbanned:
        pass
        return False

    #If the player is banned, let them know they are banned
    if name in proto_inst.factory.data.banned:
        helpers.disconnect_protocol(proto_inst, "You are banned!")
        return False
    
    #Check MPPASS (if wanted)
    if config.CHECK_USERNAMES:
        if not check_username(name, mppass, proto_inst.factory.data.salt):
            helpers.disconnect_protocol(proto_inst, "Wrong MPPASS! Log in again through the launcher to fix this.")
            return False

    #Check if the player is an operator
    if name in proto_inst.factory.data.ops:
       proto_inst.player.set_op(True)

    #set the internal player's username
    proto_inst.player.set_username(name)
    return True

#Set up a player's Player ID
def handle_player_id_setup(proto_inst):
    #Check every ID from 0 to MAX_USERS. If the ID isn't taken, assign it to this player
    for i in range(config.MAX_USERS):
        if i not in proto_inst.factory.data.taken_ids:
            proto_inst.factory.data.taken_ids.append(i)
            proto_inst.player.set_ID(i)
            return
    #If there are no more IDs, don't let the user join
    helpers.disconnect_protocol(proto_inst, "Too many players online.")

#Finish the server handshake
def finish_server_handshake(proto_inst):
    #Kick the other instance of the player if they have reconnected
    handle_check_reconnect(proto_inst)

    #Send the client the info about the server
    handle_send_server_ident(proto_inst)

    #Handle the map sending, including sending the player the initial map, 
    #as well as setting the player's spawn point and sending other player locations
    map_protocol_handler.handle_init(proto_inst)

    #If the client supports the MessageTypes extension, send one-time text
    if helpers.get_extension_state(proto_inst.player, ('MessageTypes', 1)):
        proto_inst.transport.write(helpers.gen_chat_packet('Curr pos:', 12))

    proto_inst.factory.data.players.append(proto_inst.player)
    chat_handler.handle_inform_player_spawn(proto_inst)


def handle_check_reconnect(proto_inst):
    for other_player in proto_inst.factory.data.players:
        if (proto_inst.player.username == other_player.username):
            disconnect_packet = helpers.gen_disconnect_player_packet("Reconnected!")
            print("disconnect packet put!")
            other_player.proto_inst.transport.write(disconnect_packet)


#Send a server identification packet to the client
def handle_send_server_ident(proto_inst):
    is_op = proto_inst.player.is_op
    server_ident_packet = helpers.gen_server_ident_packet(config.NAME, config.MOTD, is_op)
    proto_inst.transport.write(server_ident_packet)

def check_username(username, mppass, salt):
    to_hash = (salt + username).encode('ibm437')
    curr_hash = hashlib.md5(to_hash).hexdigest()
    if (curr_hash != mppass):
        return False
    else:
        return True


import protocol_handlers
#Register the initial packet handler
protocol_handlers.register_packet_handler(0, handle_login)


#Import CPE handler
import cpe_protocol_handler