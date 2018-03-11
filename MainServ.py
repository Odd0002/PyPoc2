#!/bin/python3

#import shared_data
import helpers
import config
import map_handler
import protocol_handler
import player
import global_data
import bg_threads

import threading
import time
from twisted.internet import protocol, reactor
from twisted.internet.task import LoopingCall
from twisted.internet.endpoints import TCP4ServerEndpoint


class classic_CPE_protocol(protocol.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.buf = b''
        self.player = player.Player()

    def connectionMade(self):
        self.initialized = False
        self.CPE_done = False

    def dataReceived(self, data):
        self.buf += data
        #print("data gotten:", data)
        try:
            protocol_handler.handle_data_recv(self)
        except Exception as e:
            print("dataReceived exception:", e)
            raise Exception

    def connectionLost(self, reason):
        bg_threads.handle_player_disconnects(self)
        print("connection lost from", self.transport.getPeer())

class classic_CPE_factory(protocol.ServerFactory):
    def __init__(self, data):
        #self.data = global_data.Data()
        self.data = data
        heartbeat_thread = threading.Thread(target=bg_threads.heartbeat_handler, args=(self.data.players, self.data.salt, self.data))
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
        updater_thread = LoopingCall(bg_threads.send_player_packets, self.data.players)
        updater_thread.start(config.UPDATE_DELAY)
        update_thread = threading.Thread(target=bg_threads.update, args=(self.data,))
        update_thread.daemon = True
        update_thread.start()
        self.data.update_thread = update_thread

    def buildProtocol(self, addr):
        return classic_CPE_protocol(self)

    def handle_server_shutdown(self):   
        self.data.shutdown = True
        time.sleep(0.1)    
        finish_server(self.data)
        map_handler.save_all_maps()
        reactor.stop()



def finish_server(data):
    print("players:", data.players)
    shutdown_packet = helpers.gen_disconnect_player_packet("Server shutting down!")
    for curr_player in data.players:
        curr_player.proto_inst.transport.write(shutdown_packet)
        curr_player.proto_inst.transport.loseConnection()
    print("done shutting down!")
    time.sleep(0.1)



all_data = global_data.Data()
#reactor.addSystemEventTrigger('during', 'persist', finish_server, all_data)
endpoint = TCP4ServerEndpoint(reactor, config.PORT)
#reactor.listenTCP(config.PORT, classic_CPE_factory())
endpoint.listen(classic_CPE_factory(all_data))
reactor.run()
