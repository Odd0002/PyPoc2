import types
map_dims = types.SimpleNamespace()


PORT = 9999
NAME = "INF. MAP SERV 2, now 34.8% more stable!"
SOFTWARE = "PyPoc2 0.1.00.0"
MOTD = "horspeed=1.5"
MAPS_DIR = "maps"
CHECK_USERNAMES = False
UPDATE_DELAY = 0.03

MAX_USERS = 128
PUBLIC = "true"

SERVER_CPE_EXTENSIONS = (('CustomBlocks', 1), ('BulkBlockUpdate', 1), ('FullCP437', 1), ('MessageTypes', 1), ('SetMapEnvProperty', 1), ('HackControl', 1), ('LongerMessages', 1), ('ExtEntityPositions', 1), ('TwoWayPing', 1))

SERVER_COLORS = '01234567890abcdef'
STATUS_MESSAGES = ['**connections', '**disconnections', '**saves', '**autosaves']


BORDER_SIZE = 5

map_dims.x = 256
map_dims.y = 128
map_dims.z = 256
map_dims.np_x = map_dims.x // 2
map_dims.np_y = map_dims.y
map_dims.np_z = map_dims.z // 2

map_dims.center_x = map_dims.x // 2
map_dims.center_z = map_dims.z // 2