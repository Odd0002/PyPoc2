import struct
import helpers
import config
import protocol_handlers
import login_protocol_handler

#Send CPE information to the client
def send_CPE(proto_inst):
    #Send ExtInfo packet
    extinfo_packet = helpers.gen_extinfo_packet(config.SOFTWARE, config.SERVER_CPE_EXTENSIONS)
    proto_inst.transport.write(extinfo_packet)

    #Generate and send ExtEntry packets for all supported extensions
    for extension_info in config.SERVER_CPE_EXTENSIONS:
        extentry_packet = helpers.gen_extentry_packet(extension_info[0], extension_info[1])
        proto_inst.transport.write(extentry_packet)


#Handle the initial CPE ExtInfo packet
def handle_init_CPE(packet_num, data, proto_inst):
    tmp_player = proto_inst.player
    extinfo = struct.unpack('!b64sH', data)
    
    #Set player info based on CPE data received
    tmp_player.set_client_name(extinfo[1].decode('ibm437').strip())
    tmp_player.set_CPE_count(extinfo[2])


#Handle all CPE ExtEntry packets
def handle_CPE_extension(packet_num, data, proto_inst):
    tmp_player = proto_inst.player

    #Extract packet data and add the extension into the list of extensions supported by the player's client
    extentry = struct.unpack('!b64sI', data)
    tmp_player.add_extension((extentry[1].decode('ibm437').strip(), extentry[2]))

    #If the client has sent as many ExtEntry packets as it said it would, finalize CPE negotiation
    if tmp_player.CPE_count == len(tmp_player.get_extensions()):
        handle_CPE_done(proto_inst)

    return



def handle_customblock_support_packet(proto_inst):
    #TODO implement
    login_protocol_handler.finish_server_handshake(proto_inst)
    pass

#Handle final 
def handle_CPE_done(proto_inst):
    #TODO do we need this? investigate 
    proto_inst.CPE_done = True
    #If the client supports CustomBlocks, send the client which CustomBlocks version we support
    if ('CustomBlocks', 1) in proto_inst.player.get_extensions():
        custom_block_support_packet = helpers.gen_customblock_support_packet(1)
        proto_inst.transport.write(custom_block_support_packet)
    #Otherwise finish the handshake
    else:
        login_protocol_handler.finish_server_handshake(proto_inst)




#Handle two way ping packets
def handle_two_way_ping(data, proto_inst):
    tmp_player = proto_inst.player
    ping_data = struct.unpack('!bBh', data)
    if ping_data[1] == 0:
        packet = helpers.gen_two_way_ping_packet(ping_data[2])
        tmp_player.add_packet(packet)


#Register ExtInfo packet handler
protocol_handlers.register_packet_handler(16, handle_init_CPE)

#Register ExtInfo packet handler
protocol_handlers.register_packet_handler(17, handle_CPE_extension)

#Register the custom block packet handler
protocol_handlers.register_packet_handler(19, handle_customblock_support_packet)

#Register the two way ping packet handler
protocol_handlers.register_packet_handler(43, handle_customblock_support_packet)
