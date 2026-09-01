import ctypes, os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import STAPIv2, dot_h, found_in
import pysoltrace.soltrace_constants as _STC
import pysoltrace.soltrace_json as stJSON
from pysoltrace.point import Point

"""init api"""
stapi = STAPIv2()

"""NSTTF information"""
DNI = 930 # [W/m^2]
LATITUDE  = 35.962278    # [deg], NSTTF original tower latitude (approximate)
LONGITUDE = -106.5122622 # [deg], NSTTF original tower longitude (approximate)

# TODO: make container spoof to mirror id calculations

"""dummy variables for batch calls"""
dummy_uint64 = ctypes.c_uint64()

def pretty(struct):
    s = '{\n'
    for field in struct._fields_:
        s += f'  {field[0]}: {getattr(struct, field[0])}\n'
    s += '}\n'
    return s

optics_batch_calls = []
optical_registry = stJSON.OpticalPropertyRegistry()
_RECEIVER_OPTICAL_REF = optical_registry.add(
    'receiver',
    stJSON.optical_side_json(_reflectivity = 0, _specularity_error = .2, _slope_error = .95),
    stJSON.optical_side_json(_reflectivity = 0, _specularity_error = .2, _slope_error = .95),
    stJSON.REFLECTION,
    1.1,
    1.1,
)
RECEIVER_OPTICAL_REF = len(optics_batch_calls)
rec_set  = dot_h.args_optical_properties_set(b'receiver', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
rec_face = dot_h.args_optical_properties_face(0, 0, .95, .2, _STC.optical_error_dist.GAUSSIAN.value)
# dot_h.args_optical_properties_face(.25, .25, 2, 2, _STC.optical_error_dist.GAUSSIAN)
optics_batch_calls.append(stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
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

_APERTURE_OPTICAL_REF = optical_registry.add(
    'aperture',
    stJSON.optical_side_json(_reflectivity = 0.5, _transmissivity = 1, _slope_error = 523.6, _specularity_error = 0.1),
    stJSON.optical_side_json(_reflectivity = 0,   _transmissivity = 1, _slope_error = 523.6, _specularity_error = 0.1),
    stJSON.REFLECTION,
    1.1,
    1.1
)

_TOWER_OPTICAL_REF = optical_registry.add(
    'tower',
    stJSON.optical_side_json(_reflectivity = 0, _transmissivity = 1, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.optical_side_json(_reflectivity = 0, _transmissivity = 1, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.REFLECTION,
    1.1,
    1.1
)

_SNOUT_OPTICAL_REF = optical_registry.add(
    'snout',
    stJSON.optical_side_json(_reflectivity = 0.2, _transmissivity = 0, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.optical_side_json(_reflectivity = 0,   _transmissivity = 0, _slope_error = 0.95, _specularity_error = 0.2),
    stJSON.REFLECTION,
    1.1,
    1.1
)

if __name__ == '__main__':
    print(pretty(rec_set))
    print(pretty(rec_face))
    print(optical_registry[_RECEIVER_OPTICAL_REF])

    print(_HELIOSTAT_OPTICAL_REF)
    print(_APERTURE_OPTICAL_REF)
    print(_TOWER_OPTICAL_REF)
    print(_SNOUT_OPTICAL_REF)
