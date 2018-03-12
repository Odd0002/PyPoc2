
import time
import threading
import queue

import config
import helpers
import map_handler

class Player:
    def __init__(self):
        self.username = ''
        self.title = ''
        self.displayname = ''
        self.client_name = ''
        self.player_ID = -1
        self.yaw = bytes([0])
        self.pitch = bytes([0])
        self.perms_level = 0
        self.proto_inst = None
        self.supports_CPE = False
        self.CPE_count = 0
        self.CPE_extensions = []
        self.message_buffer = ''
        self.is_op = False
        self.loading = False
        self.remove = False
        self.dc_sent = False
        self.color = r'%7'
        self.last_teleport_time = time.time()
        self.xpos = (config.map_dims.x * 32) // 2
        self.ypos = (config.map_dims.y * 32) // 2 + 51
        self.zpos = (config.map_dims.z * 32) // 2
        self.packet_queue = queue.Queue()
        self.x_offset = 0
        self.z_offset = 0
        self.ignored_players = []

    def set_username(self, username):
        self.username = username
        self.load_title()
        self.displayname = self.title + self.color + self.username

    def set_title(self, title):
        self.title = title
        self.displayname = self.title + self.username

    def set_ID(self, ID):
        self.player_ID = ID

    def set_op(self, state):
        self.is_op = state
        if state:
            self.color = r'%1'

    def set_CPE(self, state):
        self.supports_CPE = state

    def set_CPE_count(self, count):
        self.CPE_count = count

    def set_client_name(self, name):
        self.client_name = name

    def add_extension(self, extentry):
        self.CPE_extensions.append(extentry)

    def add_packet(self, packet):
        self.packet_queue.put(packet)

    def add_msg(self, text):
        space = b' '
        cleaned_text = text.decode('ibm437').strip()
        if text[1] == space[0]:
            cleaned_text = ' ' + cleaned_text
        if text[-1] == space[0]:
            cleaned_text += ' '
        self.message_buffer += cleaned_text

    def get_all_packets(self):
        return helpers.get_and_clear_queue(self.packet_queue)

    def set_proto_inst(self, protocol_instance):
        self.proto_inst = protocol_instance

    def load_title(self):
        pass
        #if self.title != '':
        #    return '[{}]'.format(self.title)


    def get_extensions(self):
        return self.CPE_extensions

    def get_ID(self):
        return self.player_ID

    def get_messages(self):
        tmp_buf = self.message_buffer
        self.message_buffer = ''
        return tmp_buf

    def teleport_to(self, player):
        self.last_teleport_time = time.time()
        self.xpos = player.xpos
        self.ypos = player.ypos
        self.zpos = player.zpos
        self.yaw = player.yaw
        self.pitch = player.pitch

    def update_pos(self, pos_data):
        if (time.time() - self.last_teleport_time > 0.75):
            self.xpos = pos_data[2]
            self.ypos = pos_data[3]
            self.zpos = pos_data[4]
            self.yaw = pos_data[5]
            self.pitch = pos_data[6]
        if not self.loading:
            self.handle_pos_tp_check()

    def handle_pos_tp_check(self):
        p_block_xpos = self.xpos // 32
        p_block_zpos = self.zpos // 32
        prev_x_offset = self.x_offset
        prev_z_offset = self.z_offset
        big_border_size = config.BORDER_SIZE * 32
        is_long = helpers.get_extension_state(self, ('ExtEntityPositions', 1))


        if (p_block_xpos + config.BORDER_SIZE > config.map_dims.x):
            print("moving player +x!")
            self.last_teleport_time = time.time()
            teleport_packet = helpers.gen_pos_packet(-1, (config.map_dims.center_x * 32) - big_border_size, self.ypos, self.zpos, self.yaw, self.pitch, is_long)
            self.xpos = (config.map_dims.center_x // 2) * 32
            self.x_offset += config.map_dims.center_x
            self.add_packet(teleport_packet)
            bbu_sm_thread = threading.Thread(target=map_handler.update_player_map_data, args=(prev_x_offset, self.z_offset, self.x_offset, self.z_offset, self, teleport_packet))
            bbu_sm_thread.start()
        elif (p_block_xpos - config.BORDER_SIZE < 0):
            print("moving player -x!")
            self.last_teleport_time = time.time()
            teleport_packet = helpers.gen_pos_packet(-1, (config.map_dims.center_x * 32) + big_border_size, self.ypos, self.zpos, self.yaw, self.pitch, is_long)
            self.xpos = (config.map_dims.center_x // 2) * 32
            self.x_offset -= config.map_dims.center_x
            self.add_packet(teleport_packet)
            bbu_sm_thread = threading.Thread(target=map_handler.update_player_map_data, args=(prev_x_offset, self.z_offset, self.x_offset, self.z_offset, self, teleport_packet))
            bbu_sm_thread.start()
        elif (p_block_zpos + config.BORDER_SIZE > config.map_dims.z):
            print("moving player +z!")
            self.last_teleport_time = time.time()
            teleport_packet = helpers.gen_pos_packet(-1, self.xpos, self.ypos, (config.map_dims.center_z * 32) - big_border_size, self.yaw, self.pitch, is_long)
            self.zpos = (config.map_dims.center_z // 2) * 32
            self.z_offset += config.map_dims.center_z
            self.add_packet(teleport_packet)
            bbu_sm_thread = threading.Thread(target=map_handler.update_player_map_data, args=(self.x_offset, prev_z_offset, self.x_offset, self.z_offset, self, teleport_packet))
            bbu_sm_thread.start()
        elif (p_block_zpos - config.BORDER_SIZE < 0):
            print("moving player -z!")
            self.last_teleport_time = time.time()
            teleport_packet = helpers.gen_pos_packet(-1, self.xpos, self.ypos, (config.map_dims.center_z * 32) + big_border_size, self.yaw, self.pitch, is_long)
            self.zpos = (config.map_dims.center_z // 2) * 32
            self.z_offset -= config.map_dims.center_z
            self.add_packet(teleport_packet)
            bbu_sm_thread = threading.Thread(target=map_handler.update_player_map_data, args=(self.x_offset, prev_z_offset, self.x_offset, self.z_offset, self, teleport_packet))
            bbu_sm_thread.start()

        pass
