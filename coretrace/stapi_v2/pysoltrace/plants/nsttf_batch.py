import os, sys
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import api, dot_h, math_utils
import pysoltrace.soltrace_constants as _STC
import pysoltrace.soltrace_json as stJSON
from pysoltrace.point import Point

"""init api"""
stapi = api()

"""NSTTF information"""
DNI = 930 # [W/m^2]
LATITUDE  = 35.962278    # [deg], NSTTF original tower latitude (approximate)
LONGITUDE = -106.5122622 # [deg], NSTTF original tower longitude (approximate)
TZ     = 'MST'
TZINFO = ZoneInfo("America/Denver")
ST_LOC = dot_h.args_sun_location(LATITUDE, LONGITUDE, -7.0)
# TODO: util to convert built-in datetime to st_datetime
ST_DT  = dot_h.args_sun_datetime(2025, # year
                                 6,    # month
                                 20,   # day
                                 12,   # hour
                                 34,   # minute
                                 56)   # second

"""
convert between (+x: west, +y: zenith, +z: north)
            and (+x: east, +y: north,  +z: zenith)
"""
CONVERT_COORDS = np.array([[-1., 0., 0.],
                           [ 0., 0., 1.],
                           [ 0., 1., 0.]])

# file set up
current_dir = Path(__file__).parent
data_dir    = current_dir / 'nsttf_data'
coords_f    = current_dir / 'nsttf_data' / 'coordinates.csv'
ids_f       = current_dir / 'nsttf_data' / 'ids.csv'
canting_dir = current_dir / 'nsttf_data' / 'internal_canting'

def pretty(struct):
    s = type(struct).__name__ + ': {\n'
    for field in struct._fields_:
        s += f'  {field[0]}: {getattr(struct, field[0])}\n'
    s += '}\n'
    return s

# TODO: def create_nsttf(stapi, sun_pos): stapi.clear() .. stapi.batch.clear() ...
#       def update_nsttf(stapi, sun_pos): stapi.batch.clear() ...

################################
# set up optical property sets #
################################

OPTICS = {}

RECEIVER_OPTICAL_REF = len(OPTICS)
rec_set  = dot_h.args_optical_properties_set(b'receiver', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
rec_face = dot_h.args_optical_properties_face(0, 0, .95, .2, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS[RECEIVER_OPTICAL_REF] = stapi.batch.data.optic.add(rec_set, rec_face, rec_face)

HELIOSTAT_OPTICAL_REF = len(OPTICS)
helio_set   = dot_h.args_optical_properties_set(b'heliostat', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
helio_front = dot_h.args_optical_properties_face(0, 0.885, 1.2, .05, _STC.optical_error_dist.GAUSSIAN.value)
helio_back  = dot_h.args_optical_properties_face(0, 0, 1.2, .05, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS[HELIOSTAT_OPTICAL_REF] = stapi.batch.data.optic.add(helio_set, helio_front, helio_back)

APERTURE_OPTICAL_REF = len(OPTICS)
ap_set   = dot_h.args_optical_properties_set(b'aperture', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
ap_front = dot_h.args_optical_properties_face(1, 0.5, 523.6, 0.1, _STC.optical_error_dist.GAUSSIAN.value)
ap_back  = dot_h.args_optical_properties_face(1, 0, 523.6, 0.1, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS[APERTURE_OPTICAL_REF] = stapi.batch.data.optic.add(ap_set, ap_front, ap_back)

TOWER_OPTICAL_REF = len(OPTICS)
tower_set  = dot_h.args_optical_properties_set(b'tower', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
tower_face = dot_h.args_optical_properties_face(1, 0, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS[TOWER_OPTICAL_REF] = stapi.batch.data.optic.add(tower_set, tower_face, tower_face)

SNOUT_OPTICAL_REF = len(OPTICS)
snout_set   = dot_h.args_optical_properties_set(b'snout', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
snout_front = dot_h.args_optical_properties_face(0, 0.2, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
snout_back  = dot_h.args_optical_properties_face(0, 0, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS[SNOUT_OPTICAL_REF] = stapi.batch.data.optic.add(snout_set, snout_front, snout_back)

########################
# set up G3P3 receiver #
########################

g3p3_stage_pos = np.array([-40, 8.5, 44.8177])
g3p3_stage_aim = np.array([0,   122, 44.8177])
g3p3_unstager = math_utils.get_unstager(g3p3_stage_pos, g3p3_stage_aim, 0)

G3P3_GROUP = 0
G3P3 = {}

# aperture
APERTURE_ID = len(G3P3)
ap_el_args = dot_h.args_element(*g3p3_unstager([0, 0, 0.662347]),
                                *g3p3_unstager([0, 1, 0.662347]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[APERTURE_ID] = stapi.batch.data.element.add(ap_el_args,
                                                 APERTURE_OPTICAL_REF,
                                                 [1.32475, 1.32475], [])

# tunnel bottom
TUNNEL_BOTTOM_ID = len(G3P3)
tb_el_args = dot_h.args_element(*g3p3_unstager([0, 0, 0]),
                                *g3p3_unstager([0, 0.608432, 0.793606]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[TUNNEL_BOTTOM_ID] = \
    stapi.batch.data.element.add(tb_el_args,
                                 SNOUT_OPTICAL_REF,
                                 [0.662347, 0, -0.662347, 0, -1.65, -0.945053, 1.65, -0.945053], [])

# tunnel east
TUNNEL_EAST_ID = len(G3P3)
te_el_args = dot_h.args_element(*g3p3_unstager([0.662347, 0, 0]),
                                *g3p3_unstager([0.057569, 0.796394, 0]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[TUNNEL_EAST_ID] = \
    stapi.batch.data.element.add(te_el_args,
                                 SNOUT_OPTICAL_REF,
                                 [0, 1.32475, -1.24012, 1.175, -1.24012, -0.575, 0, 0], [])

# tunnel west
TUNNEL_WEST_ID = len(G3P3)
tw_el_args = dot_h.args_element(*g3p3_unstager([-0.662347, 0, 0]),
                                *g3p3_unstager([-0.057569, 0.796394, 0]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[TUNNEL_WEST_ID] = \
    stapi.batch.data.element.add(tw_el_args,
                                 SNOUT_OPTICAL_REF,
                                 [1.24012, 1.175, 0, 1.32475, 0, 0, 1.24012, -0.575], [])

# tunnel top
TUNNEL_TOP_ID = len(G3P3)
tt_el_args = dot_h.args_element(*g3p3_unstager([0, 0, 1.32475]),
                                *g3p3_unstager([0, 0.195795, 0.344105]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[TUNNEL_TOP_ID] = \
    stapi.batch.data.element.add(tt_el_args,
                                 SNOUT_OPTICAL_REF,
                                 [0.662347, 0, -0.662347, 0, -1.65, -0.764803, 1.65, -0.764803], [])

# shield northeast
SHIELD_NORTHEAST_ID = len(G3P3)
sne_el_args = dot_h.args_element(*g3p3_unstager([2.65, 0.75, 2.175]),
                                 *g3p3_unstager([2.65, 1.75, 2.175]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value,
                                 G3P3_GROUP)
G3P3[SHIELD_NORTHEAST_ID] = stapi.batch.data.element.add(sne_el_args,
                                                         SNOUT_OPTICAL_REF,
                                                         [2, 2], [])

# shield north
SHIELD_NORTH_ID = len(G3P3)
sn_el_args = dot_h.args_element(*g3p3_unstager([0, 0.75, 2.175]),
                                *g3p3_unstager([0, 1.75, 2.175]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[SHIELD_NORTH_ID] = stapi.batch.data.element.add(sn_el_args,
                                                     SNOUT_OPTICAL_REF,
                                                     [3.3, 2], [])

# shield northwest
SHIELD_NORTHWEST_ID = len(G3P3)
snw_el_args = dot_h.args_element(*g3p3_unstager([-2.65, 0.75, 2.175]),
                                 *g3p3_unstager([-2.65, 1.75, 2.175]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value,
                                 G3P3_GROUP)
G3P3[SHIELD_NORTHWEST_ID] = stapi.batch.data.element.add(snw_el_args,
                                                         SNOUT_OPTICAL_REF,
                                                         [2, 2], [])

# shield east
SHIELD_EAST_ID = len(G3P3)
se_el_args = dot_h.args_element(*g3p3_unstager([2.65, 0.75, 0.375]),
                                *g3p3_unstager([2.65, 1.75, 0.245313]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[SHIELD_EAST_ID] = stapi.batch.data.element.add(se_el_args,
                                                    SNOUT_OPTICAL_REF,
                                                    [2, 1.75], [])

# shield west
SHIELD_WEST_ID = len(G3P3)
sw_el_args = dot_h.args_element(*g3p3_unstager([-2.65, 0.75, 0.375]),
                                *g3p3_unstager([-2.65, 1.75, 0.245313]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value,
                                G3P3_GROUP)
G3P3[SHIELD_WEST_ID] = stapi.batch.data.element.add(sw_el_args,
                                                    SNOUT_OPTICAL_REF,
                                                    [2, 1.75], [])

# shield southeast
SHIELD_SOUTHEAST_ID = len(G3P3)
sse_el_args = dot_h.args_element(*g3p3_unstager([2.65, 0.75, -1.575]),
                                 *g3p3_unstager([2.65, 1.75, -1.575]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value,
                                 G3P3_GROUP)
G3P3[SHIELD_SOUTHEAST_ID] = stapi.batch.data.element.add(sse_el_args,
                                                         SNOUT_OPTICAL_REF,
                                                         [2, 2], [])

# shield south
SHIELD_SOUTH_ID = len(G3P3)
ss_el_args = dot_h.args_element(*g3p3_unstager([0, 0.75, -1.575]),
                                 *g3p3_unstager([0, 1.75, -1.575]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value,
                                 G3P3_GROUP)
G3P3[SHIELD_SOUTH_ID] = stapi.batch.data.element.add(ss_el_args,
                                                     SNOUT_OPTICAL_REF,
                                                     [3.3, 2], [])

# shield southwest
SHIELD_SOUTHWEST_ID = len(G3P3)
ssw_el_args = dot_h.args_element(*g3p3_unstager([-2.65, 0.75, -1.575]),
                                 *g3p3_unstager([-2.65, 1.75, -1.575]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value,
                                 G3P3_GROUP)
G3P3[SHIELD_SOUTHWEST_ID] = stapi.batch.data.element.add(ssw_el_args,
                                                         SNOUT_OPTICAL_REF,
                                                         [2, 2], [])

# measurement plane
# curtain

# heliostat and facet information
PED_HEIGHT = 4.02           # [m], heliostat pedistal height
TRACK_ERR  = 0.0005         # [rad], heliostat tracking error
PIV_OFFSET = 0.1778         # [m], facet pivot offset
RECT_AP    = 1.2192         # [m], facet side length
PARA_SURF  = .5 / 0.0034203 # [m], parabolic focal length
CANT_ERR   = 0.0017         # [rad], facet canting error

if __name__ == '__main__':
    # print(pretty(ap_el_args))
    # print(type(ap_el_args))
    # print(type(ctypes.pointer(ap_el_args)))
    # test_unstager = math_utils.get_unstager(CONVERT_COORDS @ g3p3_stage_pos, CONVERT_COORDS @ g3p3_stage_aim, 0)

    # print(test_unstager(CONVERT_COORDS @ np.array([0, 0, 0.662347])))
    # print(test_unstager(CONVERT_COORDS @ np.array([0, 0, 0.662347])))

    print(__file__)
    # print(Path(__file__).parent / 'nsttf_data')
    # print(Path(__file__).parent / 'nsttf_data' / 'coordinates.csv')
    # print(Path(__file__).parent / 'nsttf_data' / 'ids.csv')

    # print(math_utils.zrot_from_azel([0, 1, 0]))
    # # test batch
    # stapi.batch(True)

    # print(stapi.data.optic.num())
    # print(stapi.data.element.num())

    # print(stapi.data.element.get(1)[0])
    # print(stapi.data.element.get(2)[0])
    # print(stapi.data.element.get(2)[1])
    # print(stapi.data.element.get(3)[0])