import queue
import re

import helpers
import config

class Data:
    salt = helpers.gen_salt()
    ops = helpers.read_file('ops.txt')
    banned = helpers.read_file('banned.txt')
    silentbanned = helpers.read_file('silentbanned.txt')
    crashbanned = helpers.read_file('crashbanned.txt')
    players = []
    taken_ids = []
    update_thread = None
    shutdown = False
    setblock_queue = queue.Queue()
    chat_broadcast_queue = queue.Queue()
    def __init__(self):
        self.colors_regex = re.compile('%(?=[{}])'.format(config.SERVER_COLORS))