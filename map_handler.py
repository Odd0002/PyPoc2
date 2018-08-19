import collections
import numpy as np
import struct
import zlib
import time
import threading

import config
import helpers

try:
    import multiprocessing as mp
except:
    config.USE_MP = False

maps_loaded = dict()

def set_block(xpos, ypos, zpos, block):
    x_map_num = xpos // config.map_dims.np_x
    z_map_num = zpos // config.map_dims.np_z

    #Find which block in the map it is
    rel_x_pos = xpos - (x_map_num * config.map_dims.np_x)
    rel_z_pos = zpos - (z_map_num * config.map_dims.np_z)
    block_int = int.from_bytes(block, byteorder='big')
    try:
        maps_loaded[(x_map_num, z_map_num)][ypos][rel_z_pos][rel_x_pos] = block_int
    except:
        load_map(x_map_num, z_map_num)
        try:
            maps_loaded[(x_map_num, z_map_num)][ypos][rel_z_pos][rel_x_pos] = block_int
        except Exception as e:
            print("ERROR LOADING MAP DURING BLOCK PLACEMENT!", e)
            return 0


def update_player_map_data(prev_x_offset, prev_z_offset, new_x_offset, new_z_offset, player, tp_packet):
    curr_time = time.time()
    player.loading = True
    init_splash_screen = helpers.gen_chat_packet("Loading map...", 100)
    end_splash_screen = helpers.gen_chat_packet("Map loaded!", 100)
    init_loading_text = helpers.gen_chat_packet("Loading...", 1)
    end_loading_text = helpers.gen_chat_packet("", 1)
    use_bbu = helpers.get_extension_state(player, ('BulkBlockUpdate', 1))
    player.add_packet(init_splash_screen)
    if helpers.get_extension_state(player, ('MessageTypes', 1)):
        player.add_packet(init_loading_text)
    fast_packets_to_send = calc_bbu_map_change_packets(prev_x_offset, prev_z_offset, new_x_offset, new_z_offset, use_bbu)
    for result in fast_packets_to_send:
        for packet in result:
            player.add_packet(packet)
    if tp_packet is not None:
        player.add_packet(tp_packet)
    if helpers.get_extension_state(player, ('MessageTypes', 1)):
        player.add_packet(end_loading_text)
    player.add_packet(end_splash_screen)
    player.last_teleport_time = time.time()
    player.loading = False
    print("took", time.time() - curr_time)


def get_player_spawn_data(source_player):
    pass


def get_player_tp_map_data(source_player, dest_player):
    source_x = source_player.x_offset
    source_z = source_player.z_offset
    source_player.x_offset = dest_player.x_offset
    source_player.z_offset = dest_player.z_offset
    t = threading.Thread(target=update_player_map_data, args=(source_x, source_z, dest_player.x_offset, dest_player.z_offset, source_player, None))
    t.start()
    '''
    curr_time = time.time()
    source_player.loading = True
    init_splash_screen = helpers.gen_chat_packet("Loading map...", 100)
    end_splash_screen = helpers.gen_chat_packet("Map loaded!", 100)
    init_loading_text = helpers.gen_chat_packet("Loading...", 1)
    end_loading_text = helpers.gen_chat_packet("", 1)
    use_bbu = helpers.get_extension_state(source_player, ('BulkBlockUpdate', 1))
    source_player.add_packet(init_splash_screen)
    if helpers.get_extension_state(source_player, ('MessageTypes', 1)):
        source_player.add_packet(init_loading_text)
    fast_packets_to_send = calc_bbu_map_change_packets(source_player.x_offset, source_player.y_offset, player.x_offset, player.z_offset, use_bbu)
    for result in fast_packets_to_send:
        for packet in result:
            player.add_packet(packet)
    player.add_packet(tp_packet)
    if helpers.get_extension_state(player, ('MessageTypes', 1)):
        player.add_packet(end_loading_text)
    player.add_packet(end_splash_screen)
    player.loading = False
    print("took", time.time() - curr_time)
    '''


def calc_bbu_map_change_packets(prev_x_offset, prev_z_offset, new_x_offset, new_z_offset, use_bbu):
    #DEFINED_2_MAPSIZE
    HALF_X = config.map_dims.x // 2
    HALF_Z = config.map_dims.z // 2
    max_new_x_map = (new_x_offset + 1 + HALF_X ) // HALF_X
    min_new_x_map = (new_x_offset - 1 + HALF_X ) // HALF_X
    max_prev_x_map = (prev_x_offset + 1 + HALF_X ) // HALF_X
    min_prev_x_map = (prev_x_offset - 1 + HALF_X ) // HALF_X
    max_new_z_map = (new_z_offset + 1 + HALF_Z ) // HALF_Z
    min_new_z_map = (new_z_offset - 1 + HALF_Z ) // HALF_Z
    max_prev_z_map = (prev_z_offset + 1 + HALF_Z ) // HALF_Z
    min_prev_z_map = (prev_z_offset - 1 + HALF_Z ) // HALF_Z

    if config.USE_MP:
        try:
            pool = mp.Pool(processes=4)
            fast_packets_to_send = pool.starmap(get_maps_diff, \
                                        zip((min_new_x_map, min_new_x_map, max_new_x_map, max_new_x_map), \
                                            (min_new_z_map, max_new_z_map, min_new_z_map, max_new_z_map), \
                                            (min_prev_x_map, min_prev_x_map, max_prev_x_map, max_prev_x_map), \
                                            (min_prev_z_map, max_prev_z_map, min_prev_z_map, max_prev_z_map), \
                                            (0, 0, HALF_X, HALF_X), \
                                            (0, HALF_Z, 0, HALF_Z), \
                                            (use_bbu, use_bbu, use_bbu, use_bbu)
                                            )
                                        )
            pool.close()
            pool.join()
        except:
            config.USE_MP = False
            return calc_bbu_map_change_packets(prev_x_offset, prev_z_offset, new_x_offset, new_z_offset, use_bbu)
    
    else:
        fast_packets_to_send = list()
        fast_packets_to_send.append(get_maps_diff(min_new_x_map, min_new_z_map, min_prev_x_map, min_prev_z_map, 0, 0, use_bbu))
        fast_packets_to_send.append(get_maps_diff(min_new_x_map, max_new_z_map, min_prev_x_map, max_prev_z_map, 0, HALF_Z, use_bbu))
        fast_packets_to_send.append(get_maps_diff(max_new_x_map, min_new_z_map, max_prev_x_map, min_prev_z_map, HALF_X, 0, use_bbu))
        fast_packets_to_send.append(get_maps_diff(max_new_x_map, max_new_z_map, max_prev_x_map, max_prev_z_map, HALF_X, HALF_Z, use_bbu))
    
    return fast_packets_to_send


def get_maps_diff(new_x, new_z, prev_x, prev_z, x_offset, z_offset, use_bbu):
    load_map_if_unloaded(new_x, new_z)
    load_map_if_unloaded(prev_x, prev_z)
    new_map = maps_loaded[(new_x, new_z)]
    prev_map = maps_loaded[(prev_x, prev_z)]
    diff_blocks = np.argwhere(new_map != prev_map)
    blocks_update_queue = collections.deque()
    x_dim = config.map_dims.x
    z_dim = config.map_dims.z

    for block_loc in diff_blocks:
        x_pos = block_loc[2]
        y_pos = block_loc[0]
        z_pos = block_loc[1]
        new_block = new_map[y_pos][z_pos][x_pos]
        if use_bbu:
            block_pos = (((y_pos * z_dim) + (z_pos + z_offset)) * x_dim) + (x_pos + x_offset)
            blocks_update_queue.append((block_pos, new_block))
        else:
            blocks_update_queue.append(((x_pos, y_pos, z_pos), new_block))

    if use_bbu:
        bbu_packets = helpers.gen_bbu_packets_fast(list(blocks_update_queue))
        return bbu_packets
    else:
        packets = []
        for block_info in list(blocks_update_queue):
            pos = block_info[0]
            block = block_info[1]
            packets.append(helpers.gen_setblock_packet(pos[0] + x_offset, pos[1], pos[2] + z_offset, block))
        return packets

#Get a block based on its absolute position
def get_block(xpos, ypos, zpos):
    #Find what map it is on
    x_map_num = xpos // config.map_dims.np_x
    z_map_num = zpos // config.map_dims.np_z

    #Find which block in the map it is
    rel_x_pos = xpos - (x_map_num * config.map_dims.np_x)
    rel_z_pos = zpos - (z_map_num * config.map_dims.np_x)

    #Return the block
    try:
        return maps_loaded[(x_map_num, z_map_num)][ypos][rel_z_pos][rel_x_pos]
    except:
        load_map(x_map_num, z_map_num)
        try:
            return maps_loaded[(x_map_num, z_map_num)][ypos][rel_z_pos][rel_x_pos]
        except:
            print("ERROR LOADING MAP!")
            return 0

#Generates a map
#Currently empty but could use a map generation algorithm to make maps
def gen_map(x_map_num, z_map_num):
    temp_map = np.zeros((config.map_dims.np_y, config.map_dims.np_z, config.map_dims.np_x), dtype=np.uint8)
    y_mid = int(config.map_dims.np_y/2)
    temp_map[0:y_mid - 1] = 3
    temp_map[y_mid - 1:y_mid] = 2
    maps_loaded[(x_map_num, z_map_num)] = temp_map

def load_map(x_map_num, z_map_num):
    map_file_compressed = config.MAPS_DIR + "/" + str(x_map_num) + "_" + str(z_map_num) + ".npz"
    try:
        #Load map file using numpy, which contains multiple arrays, so select the first array
        file_data = np.load(map_file_compressed)
        map_data = file_data[list(file_data.keys())[0]]
        maps_loaded[(x_map_num, z_map_num)] = map_data
    except FileNotFoundError as e:
        print(e)
        gen_map(x_map_num, z_map_num)

def map_loaded(x_map_num, z_map_num):
    if (x_map_num, z_map_num) in maps_loaded:
        return True
    else:
        return False

def load_map_if_unloaded(x_map_num, z_map_num):
    if not map_loaded(x_map_num, z_map_num):
        load_map(x_map_num, z_map_num)


#Save a specific map
def save_map(x_map_num, z_map_num):
    map_file_compressed = config.MAPS_DIR + "/" + str(x_map_num)+ "_" + str(z_map_num) + ".npz"

    try:
        np.savez_compressed(map_file_compressed, maps_loaded[(x_map_num, z_map_num)])
    except Exception as e:
        print("SAVING FILE", map_file_compressed, "FAILED!")
        print("exception:", e)


#Saves all currently loaded maps
def save_all_maps():
    for key, value in maps_loaded.copy().items():
        save_map(key[0], key[1])
    print("Maps saved!")


#Generates a copy of the initial map
def get_initial_map_compressed():
    map_block_count = config.map_dims.x * config.map_dims.y * config.map_dims.z
    map_blocks_count = struct.pack('!i', map_block_count)

    x_nums = config.map_dims.x // config.map_dims.np_x
    z_nums = config.map_dims.z // config.map_dims.np_z

    tmp_map = np.zeros((config.map_dims.y, config.map_dims.z, config.map_dims.x), dtype=np.uint8)
    for x in range(z_nums):
        for z in range(x_nums):
            z_start = (z) * config.map_dims.np_z
            z_end = (z + 1) * config.map_dims.np_z
            x_start = (x) * config.map_dims.np_x
            x_end = (x + 1) * config.map_dims.np_x
            load_map_if_unloaded(x, z)
            tmp_map[:,z_start:z_end,x_start:x_end] = maps_loaded[(x, z)]


    map_bytes = tmp_map.tobytes()

    #Compress using gzip
    gzip_compressor = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS | 16)
    compressed_map = gzip_compressor.compress(map_blocks_count + map_bytes) + gzip_compressor.flush()

    return compressed_map
