#!/bin/python3

import threading
import time

from twisted.internet import protocol, reactor, task
from twisted.internet.task import LoopingCall
from twisted.internet.endpoints import TCP4ServerEndpoint

#import shared_data
import helpers
import config
import map_handler
import protocol_handler
import player
import global_data
import bg_threads

import signal
import sys

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
            #raise Exception

    def connectionLost(self, reason):
        bg_threads.handle_player_disconnects(self)
        print("connection lost from", self.transport.getPeer())

class classic_CPE_factory(protocol.ServerFactory):
    def __init__(self, data):
        #self.data = global_data.Data()
        self.data = data
        heartbeat_thread = task.LoopingCall(bg_threads.heartbeat_handler, self.data.players, self.data.salt, self.data)
        heartbeat_thread.start(60)
        player_packet_sender_thread = LoopingCall(bg_threads.send_player_packets, self.data.players)
        player_packet_sender_thread.start(config.UPDATE_DELAY)

        update_thread = LoopingCall(bg_threads.update, self.data)
        update_thread.start(config.UPDATE_DELAY)

    def buildProtocol(self, addr):
        return classic_CPE_protocol(self)

    def shutdown(arg1, arg2):
        reactor.callFromThread(finish_server)
        reactor.callLater(2, stop_reactor)

def finish_server():
    data = global_data.Data()
    print("players:", data.players)
    shutdown_packet = helpers.gen_disconnect_player_packet("Server shutting down!")
    tmp_players = data.players
    data.players = []
    for curr_player in tmp_players:
        #reactor.callLater(2, curr_player.proto_inst.transport.abortConnection)
        curr_player.proto_inst.transport.write(shutdown_packet)
        print("wrote disconnect packet: ", shutdown_packet)
        curr_player.proto_inst.transport.loseConnection()
        # print("lost connection!")

def stop_reactor():
    reactor.stop()


all_data = global_data.Data()
#reactor.addSystemEventTrigger('during', 'persist', finish_server, all_data)
endpoint = TCP4ServerEndpoint(reactor, config.PORT)
#reactor.listenTCP(config.PORT, classic_CPE_factory())
endpoint.listen(classic_CPE_factory(all_data))
signal.signal(signal.SIGINT, shutdown)
reactor.run()
