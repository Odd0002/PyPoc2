import recv_protocol

# Protocol handlers are inserted into this dictionary
handlers = dict()

#Register the packet handler
def register_packet_handler(packet_num, function):
    handlers[packet_num] = function

#Run the function registered to run the function
def handle_packet(packet_num, data, protocol_instance):
    curr_packet_handler = handlers[packet_num]
    curr_packet_handler(packet_num, data, protocol_instance)

#Handle data that has been received
def handle_data_recv(proto_inst):
    packet_num = proto_inst.buf[0]
    packet_length = recv_protocol.get_packet_length(packet_num, proto_inst.player.get_extensions())

    #loop through all the data until there is none left
    while packet_length <= len(proto_inst.buf):
        #extract data and update buffer
        data = proto_inst.buf[:packet_length]
        proto_inst.buf = proto_inst.buf[packet_length:]
        
        #Handle the packet
        handle_packet(packet_num, data, proto_inst)


#Import files that depend on the above functions
import login_protocol_handler