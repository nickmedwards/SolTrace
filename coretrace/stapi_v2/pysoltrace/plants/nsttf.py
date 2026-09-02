import ctypes, os, sys
import numpy as np
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import STAPIv2, dot_h, math_utils
import pysoltrace.soltrace_constants as _STC
import pysoltrace.soltrace_json as stJSON
from pysoltrace.point import Point

"""init api"""
stapi = STAPIv2()

"""NSTTF information"""
DNI = 930 # [W/m^2]
LATITUDE  = 35.962278    # [deg], NSTTF original tower latitude (approximate)
LONGITUDE = -106.5122622 # [deg], NSTTF original tower longitude (approximate)

"""
convert between (+x: west, +y: zenith, +z: north)
            and (+x: east, +y: north,  +z: zenith)
"""
CONVERT_COORDS = np.array([[-1., 0., 0.],
                           [ 0., 0., 1.],
                           [ 0., 1., 0.]])

# TODO: make container spoof to mirror id calculations

"""dummy variables for batch calls"""
dummy_uint64 = ctypes.c_uint64()

def pretty(struct):
    s = '{\n'
    for field in struct._fields_:
        s += f'  {field[0]}: {getattr(struct, field[0])}\n'
    s += '}\n'
    return s

################################
# set up optical property sets #
################################

OPTICS_CALLS = []
optical_registry = stJSON.OpticalPropertyRegistry()
_RECEIVER_OPTICAL_REF = optical_registry.add(
    'receiver',
    stJSON.optical_side_json(_reflectivity = 0, _specularity_error = .2, _slope_error = .95),
    stJSON.optical_side_json(_reflectivity = 0, _specularity_error = .2, _slope_error = .95),
    stJSON.REFLECTION,
    1.1,
    1.1,
)
RECEIVER_OPTICAL_REF = len(OPTICS_CALLS)
rec_set  = dot_h.args_optical_properties_set(b'receiver', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
rec_face = dot_h.args_optical_properties_face(0, 0, .95, .2, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
                            ctypes.pointer(rec_set),
                            ctypes.pointer(rec_face),
                            ctypes.pointer(rec_face),
                            ctypes.pointer(dummy_uint64)))

_HELIOSTAT_OPTICAL_REF = optical_registry.add(
    'heliostat',
    stJSON.optical_side_json(_reflectivity = 0.885, _slope_error = 1.2, _specularity_error = .05),
    stJSON.optical_side_json(_reflectivity = 0.0, _slope_error = 1.2, _specularity_error = .05),
    stJSON.REFLECTION,
    1.1,
    1.1,
)
HELIOSTAT_OPTICAL_REF = len(OPTICS_CALLS)
helio_set   = dot_h.args_optical_properties_set(b'heliostat', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
helio_front = dot_h.args_optical_properties_face(0, 0.885, 1.2, .05, _STC.optical_error_dist.GAUSSIAN.value)
helio_back  = dot_h.args_optical_properties_face(0, 0, 1.2, .05, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
                            ctypes.pointer(helio_set),
                            ctypes.pointer(helio_front),
                            ctypes.pointer(helio_back),
                            ctypes.pointer(dummy_uint64)))

_APERTURE_OPTICAL_REF = optical_registry.add(
    'aperture',
    stJSON.optical_side_json(_reflectivity = 0.5, _transmissivity = 1, _slope_error = 523.6, _specularity_error = 0.1),
    stJSON.optical_side_json(_reflectivity = 0,   _transmissivity = 1, _slope_error = 523.6, _specularity_error = 0.1),
    stJSON.REFLECTION,
    1.1,
    1.1
)
APERTURE_OPTICAL_REF = len(OPTICS_CALLS)
ap_set   = dot_h.args_optical_properties_set(b'aperture', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
ap_front = dot_h.args_optical_properties_face(1, 0.5, 523.6, 0.1, _STC.optical_error_dist.GAUSSIAN.value)
ap_back  = dot_h.args_optical_properties_face(1, 0, 523.6, 0.1, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
                            ctypes.pointer(ap_set),
                            ctypes.pointer(ap_front),
                            ctypes.pointer(ap_back),
                            ctypes.pointer(dummy_uint64)))

_TOWER_OPTICAL_REF = optical_registry.add(
    'tower',
    stJSON.optical_side_json(_reflectivity = 0, _transmissivity = 1, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.optical_side_json(_reflectivity = 0, _transmissivity = 1, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.REFLECTION,
    1.1,
    1.1
)
TOWER_OPTICAL_REF = len(OPTICS_CALLS)
tower_set  = dot_h.args_optical_properties_set(b'tower', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
tower_face = dot_h.args_optical_properties_face(1, 0, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
                            ctypes.pointer(tower_set),
                            ctypes.pointer(tower_face),
                            ctypes.pointer(tower_face),
                            ctypes.pointer(dummy_uint64)))

_SNOUT_OPTICAL_REF = optical_registry.add(
    'snout',
    stJSON.optical_side_json(_reflectivity = 0.2, _transmissivity = 0, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.optical_side_json(_reflectivity = 0,   _transmissivity = 0, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.REFLECTION,
    1.1,
    1.1
)
SNOUT_OPTICAL_REF = len(OPTICS_CALLS)
snout_set   = dot_h.args_optical_properties_set(b'snout', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
snout_front = dot_h.args_optical_properties_face(0, 0.2, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
snout_back  = dot_h.args_optical_properties_face(0, 0, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
OPTICS_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
                            ctypes.pointer(snout_set),
                            ctypes.pointer(snout_front),
                            ctypes.pointer(snout_back),
                            ctypes.pointer(dummy_uint64)))

########################
# set up G3P3 receiver #
########################

g3p3_stage_pos = np.array([-40, 8.5, 44.8177])
g3p3_stage_aim = np.array([0,   122, 44.8177])
g3p3_unstager = math_utils.get_unstager(g3p3_stage_pos, g3p3_stage_aim, 0)

G3P3_CALLS = []

# all G3P3 elements have flat surfaces, so make one and reuse it
flat_params = (ctypes.c_double * 8)()
make_c_double_8 = lambda *args: (ctypes.c_double * 8)(*args)

# aperture
APERTURE_ID = len(G3P3_CALLS)
ap_el_args = dot_h.args_element(*g3p3_unstager([0, 0, 0.662347]),
                                *g3p3_unstager([0, 1, 0.662347]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value)
ap_a_params = make_c_double_8(1.32475, 1.32475)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(ap_el_args),
                            APERTURE_OPTICAL_REF,
                            ap_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# tunnel bottom
TUNNEL_BOTTOM_ID = len(G3P3_CALLS)
tb_el_args = dot_h.args_element(*g3p3_unstager([0, 0, 0]),
                                *g3p3_unstager([0, 0.608432, 0.793606]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value)
tb_a_params = make_c_double_8(0.662347, 0, -0.662347, 0, -1.65, -0.945053, 1.65, -0.945053)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(tb_el_args),
                            SNOUT_OPTICAL_REF,
                            tb_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# tunnel east
TUNNEL_EAST_ID = len(G3P3_CALLS)
te_el_args = dot_h.args_element(*g3p3_unstager([0.662347, 0, 0]),
                                *g3p3_unstager([0.057569, 0.796394, 0]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value)
te_a_params = make_c_double_8(0, 1.32475, -1.24012, 1.175, -1.24012, -0.575, 0, 0)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(te_el_args),
                            SNOUT_OPTICAL_REF,
                            te_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# tunnel west
TUNNEL_WEST_ID = len(G3P3_CALLS)
tw_el_args = dot_h.args_element(*g3p3_unstager([-0.662347, 0, 0]),
                                *g3p3_unstager([-0.057569, 0.796394, 0]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value)
tw_a_params = make_c_double_8(1.24012, 1.175, 0, 1.32475, 0, 0, 1.24012, -0.575)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(tw_el_args),
                            SNOUT_OPTICAL_REF,
                            tw_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# tunnel top
TUNNEL_TOP_ID = len(G3P3_CALLS)
tt_el_args = dot_h.args_element(*g3p3_unstager([0, 0, 1.32475]),
                                *g3p3_unstager([0, 0.195795, 0.344105]),
                                0, True, False,
                                _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                                _STC.surface.FLAT.value)
tt_a_params = make_c_double_8(0.662347, 0, -0.662347, 0, -1.65, -0.764803, 1.65, -0.764803)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(tt_el_args),
                            SNOUT_OPTICAL_REF,
                            tt_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# shield northeast
SHIELD_NORTHEAST_ID = len(G3P3_CALLS)
sne_el_args = dot_h.args_element(*g3p3_unstager([2.65, 0.75, 2.175]),
                                 *g3p3_unstager([2.65, 1.75, 2.175]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value)
sne_a_params = make_c_double_8(2, 2)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(sne_el_args),
                            SNOUT_OPTICAL_REF,
                            sne_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# shield north
SHIELD_NORTH_ID = len(G3P3_CALLS)
sn_el_args = dot_h.args_element(*g3p3_unstager([0, 0.75, 2.175]),
                                *g3p3_unstager([0, 1.75, 2.175]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value)
sn_a_params = make_c_double_8(3.3, 2)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(sn_el_args),
                            SNOUT_OPTICAL_REF,
                            sn_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# shield northwest
SHIELD_NORTHWEST_ID = len(G3P3_CALLS)
snw_el_args = dot_h.args_element(*g3p3_unstager([-2.65, 0.75, 2.175]),
                                 *g3p3_unstager([-2.65, 1.75, 2.175]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value)
snw_a_params = make_c_double_8(2, 2)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(snw_el_args),
                            SNOUT_OPTICAL_REF,
                            snw_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))
# shield east
SHIELD_EAST_ID = len(G3P3_CALLS)
se_el_args = dot_h.args_element(*g3p3_unstager([2.65, 0.75, 0.375]),
                                *g3p3_unstager([2.65, 1.75, 0.245313]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value)
se_a_params = make_c_double_8(2, 1.75)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(se_el_args),
                            SNOUT_OPTICAL_REF,
                            se_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# shield west
SHIELD_WEST_ID = len(G3P3_CALLS)
sw_el_args = dot_h.args_element(*g3p3_unstager([-2.65, 0.75, 0.375]),
                                *g3p3_unstager([-2.65, 1.75, 0.245313]),
                                0, True, False,
                                _STC.aperture.RECTANGLE.value,
                                _STC.surface.FLAT.value)
sw_a_params = make_c_double_8(2, 1.75)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(sw_el_args),
                            SNOUT_OPTICAL_REF,
                            sw_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# shield southeast
SHIELD_SOUTHEAST_ID = len(G3P3_CALLS)
sse_el_args = dot_h.args_element(*g3p3_unstager([2.65, 0.75, -1.575]),
                                 *g3p3_unstager([2.65, 1.75, -1.575]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value)
sse_a_params = make_c_double_8(2, 2)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(sse_el_args),
                            SNOUT_OPTICAL_REF,
                            sse_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# shield south
SHIELD_SOUTH_ID = len(G3P3_CALLS)
ss_el_args = dot_h.args_element(*g3p3_unstager([0, 0.75, -1.575]),
                                 *g3p3_unstager([0, 1.75, -1.575]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value)
ss_a_params = make_c_double_8(3.3, 2)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(ss_el_args),
                            SNOUT_OPTICAL_REF,
                            ss_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# shield southwest
SHIELD_SOUTHWEST_ID = len(G3P3_CALLS)
ssw_el_args = dot_h.args_element(*g3p3_unstager([-2.65, 0.75, -1.575]),
                                 *g3p3_unstager([-2.65, 1.75, -1.575]),
                                 0, True, False,
                                 _STC.aperture.RECTANGLE.value,
                                 _STC.surface.FLAT.value)
ssw_a_params = make_c_double_8(2, 2)
G3P3_CALLS.append(
    stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                            ctypes.pointer(ssw_el_args),
                            SNOUT_OPTICAL_REF,
                            ssw_a_params,
                            flat_params,
                            ctypes.pointer(dummy_uint64)))

# measurement plane
# curtain
 
if __name__ == '__main__':
    # print(pretty(rec_set))
    # print(pretty(rec_face))
    # print(optical_registry[_RECEIVER_OPTICAL_REF])

    # print(pretty(helio_set))
    # print(pretty(helio_front))
    # print(pretty(helio_back))
    # print(optical_registry[_HELIOSTAT_OPTICAL_REF])

    # print(pretty(ap_set))
    # print(pretty(ap_front))
    # print(pretty(ap_back))
    # print(optical_registry[_APERTURE_OPTICAL_REF])
    
    # print(pretty(tower_set))
    # print(pretty(tower_face))
    # print(optical_registry[_TOWER_OPTICAL_REF])

    # print(pretty(snout_set))
    # print(pretty(snout_front))
    # print(pretty(snout_back))
    # print(optical_registry[_SNOUT_OPTICAL_REF])

    print(pretty(ap_el_args))
    test_unstager = math_utils.get_unstager(CONVERT_COORDS @ g3p3_stage_pos, CONVERT_COORDS @ g3p3_stage_aim, 0)

    print(test_unstager(CONVERT_COORDS @ np.array([0, 0, 0.662347])))
    print(test_unstager(CONVERT_COORDS @ np.array([0, 0, 0.662347])))

    print(math_utils.zrot_from_azel([0, 1, 0]))
    # test batch
    stapi.batch([
        *OPTICS_CALLS,
        *G3P3_CALLS
    ], True)

    print(stapi.num_optics())
    print(stapi.num_elements())
