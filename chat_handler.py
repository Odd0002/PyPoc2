import helpers

def handle_inform_player_spawn(proto_inst):
    spawn_chat_packet = helpers.gen_chat_packet(proto_inst.player.username + " connected!", 0)
    proto_inst.factory.data.chat_broadcast_queue.put((spawn_chat_packet, '**connections'))