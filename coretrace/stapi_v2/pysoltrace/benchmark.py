"""
(x: done, -: skipped, i: in progress, T: have TODO, blank: not done)

function name | ctrl type: |   range   |   varience
-------------------------------------------------------
 generate_api_call              [ ]           [x]
 read_input_json (dict)         [ ]           [x]
 read_input_json (bytes)        [ ]           [x]
 set_simulation_parameters      [ ]           [x]
 sim_params                     [ ]           [x]
 sim_errors                     [ ]           [x]
 sim_location                   [ ]           [x]
 sim_tolerance                  [ ]           [x]
 num_optics                     [ ]           [x]
 add_optical_properties_set     [ ]           [x]
 delete_optic                   [ ]           [x]
 clear_optics                   [ ]           [x]
 num_elements                   [ ]           [x]
 add_element                    [ ]           [x]
 delete_element                 [ ]           [x]
 clear_elements                 [ ]           [x]
 element_enabled                [ ]           [x]
 element_virtual                [ ]           [x]
 element_xyz                    [ ]           [x]
 element_aim                    [ ]           [x]
 element_zrot                   [ ]           [x]
 element_aperture               [ ]           [x]
 element_surface                [ ]           [x]
 element_optic                  [ ]           [x]
 add_sun_buie                   [ ]           [x]
 add_sun_userdata               [ ]           [x]
 sun_shape                      [ ]           [x]
 sun_xyz                        [ ]           [x]
 sun_userdata                   [ ]           [x]
 check_success_code             [ ]           [x]
 check_error_code               [ ]           [x]
 sim_setup                      [x]           [ ]
 sim_run_v2                     [x]           [ ]
 sim_report                     [x]           [ ]
 num_intersections              [x]           [ ]
 locations                      [x]           [ ]
 cosines                        [x]           [ ]
 elementmap                     [x]           [ ]
 stagemap                       [x]           [ ]
 raynumbers                     [x]           [ ]
 sun_stats                      [x]           [ ]
 get_results_data               [x]           [ ]
"""

import ctypes, orjson
from datetime import datetime

try:
    from timer import timer, benchmark_store # pyright: ignore[reportMissingModuleSource]
    from chedder import dot_h, found_in
    import soltrace_constants as _STC
    import soltrace_json as _stjson
    from point import Point
    from stapi_v2 import STAPIv2, STAPIv2Exception
    from legacy import legacy
except ImportError:
    from .timer import timer, benchmark_store
    from .chedder import dot_h, found_in
    from . import soltrace_constants as _STC
    from . import soltrace_json as _stjson
    from .point import Point
    from .stapi_v2 import STAPIv2, STAPIv2Exception
    from .legacy import legacy

# set up dummy values
bytes_str = b'string of bytes'
c_double = ctypes.c_double()
c_uint64 = ctypes.c_uint64()
double_ptr = (ctypes.c_double * 64)()
uint64_ptr  = (ctypes.c_uint64 * 64)()

sim_params = dot_h.args_simulation_parameters(1, 100, .1, 35.962278, -106.5122622, True, True, False)

args_sun_buie     = dot_h.args_sun(0, 2, 2, 2, .5, 'b'.encode())
args_sun_user     = dot_h.args_sun(len(_stjson.SUN_DEFAULT_USER_ANGLE), 608, 303, 1000, 5, 'd'.encode())
angles            = [0, 1, 2]
intensities       = [0, 1, 2]
batch_angles      = (ctypes.c_double * 3)(*angles)
batch_intensities = (ctypes.c_double * 3)(*intensities)

opt_set = dot_h.args_optical_properties_set("dummy".encode(), 1.1, 1.1, 2)
front   = dot_h.args_optical_properties_face(.5, .5, 5, 5, 'g'.encode())
back    = dot_h.args_optical_properties_face(.25, .25, 2, 2, 'g'.encode())

el_args = dot_h.args_element(2, 2, 2, 2, 2, 2, 2, False, True, 'c'.encode(), 'p'.encode())
opt_id = 0

ap   = b'c'
surf = b'p'
a_params = [2]
s_params = [2, 2]
batch_a_params = (ctypes.c_double * 8)(*a_params)
batch_s_params = (ctypes.c_double * 8)(*s_params)

results_args = dot_h.args_results_data(double_ptr, double_ptr, double_ptr, 
                                       double_ptr, double_ptr, double_ptr,
                                       uint64_ptr, uint64_ptr, uint64_ptr)

f = open('./sample.json', mode='rb')
sample_json = orjson.loads(f.read())
f.close()

stapi = STAPIv2(testing = True, benchmarking = True)

def do_benchmark(_t: timer, key: str, func: callable, args: tuple, count: int):
    for _ in range(count):
        _t.ic(key)
        func(*args)
        _t.oc(key)
    return _t.summarize(key)

def generic_inner(key: str, func: callable, args: tuple, count: int = 10):
    def _inner(_t: timer):
        stapi.reset()
        for _ in range(count):
            _t.ic(key)
            # single arged funcs should be defined like (arg1, )
            func(*args)
            _t.oc(key)
        return key
    return _inner

# get varience from summary of timer key
get_var = lambda _t, key: _t.summarize(key)[2] ** 2

def do_var_ctrl_benchmark(_t: timer, inner: callable[[timer], str], tol: float = .001):
    # init benchmark
    key = inner(_t)
    prev_var = get_var(_t, key)
    var_err = tol * 10

    # do variance controlled benchmark
    while var_err > tol:
        inner(_t)
        var = get_var(_t, key)
        var_err = ((prev_var - var) / prev_var) ** 2
        prev_var = var

    return _t.summarize(key)

generate_api_func_args = [
    ('generate read input json call',            stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_READ_INPUT_JSON, bytes_str)),
    ('generate set simulation parameters call',  stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SET_SIMULATION_PARAMETERS, ctypes.pointer(sim_params))),
    ('generate sim params call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SIM_PARAMS, 1, 100, True)),
    ('generate sim errors call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SIM_ERRORS, True, True)),
    ('generate sim location call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SIM_LOCATION, 35.962278, -106.5122622)),
    ('generate sim tolerance call',              stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SIM_TOLERANCE, .1)),
    ('generate num optics call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_NUM_OPTICS, ctypes.pointer(c_uint64))),
    ('generate add optical properties set call', stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
                                                                           ctypes.pointer(opt_set),
                                                                           ctypes.pointer(front),
                                                                           ctypes.pointer(back),
                                                                           ctypes.pointer(c_uint64))),
    ('generate delete optic call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_DELETE_OPTIC, 0)),
    ('generate clear optics call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_CLEAR_OPTICS, )),
    ('generate num elements call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_NUM_ELEMENTS, ctypes.pointer(c_uint64))),
    ('generate add element call',                stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                                                                           ctypes.pointer(el_args),
                                                                           opt_id,
                                                                           batch_a_params,
                                                                           batch_s_params,
                                                                           ctypes.pointer(c_uint64))),
    ('generate delete element call',             stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_DELETE_ELEMENT, 0)),
    ('generate clear elements call',             stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_CLEAR_ELEMENTS, )),
    ('generate element enabled call',            stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_ENABLED, 0, True)),
    ('generate element virtual call',            stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_VIRTUAL, 0, False)),
    ('generate element xyz call',                stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_XYZ, 0, 4, 4, 4)),
    ('generate element aim call',                stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_AIM, 0, 4, 4, 4)),
    ('generate element zrot call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_ZROT, 0, 4)),
    ('generate element aperture call',           stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_APERTURE, 0, ap, batch_a_params)),
    ('generate element surface call',            stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_SURFACE, 0, surf, batch_s_params)),
    ('generate element optic call',              stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENT_OPTIC, 0, opt_id)),
    ('generate add user sun call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ADD_SUN,
                                                                           ctypes.pointer(args_sun_user),
                                                                           batch_angles,
                                                                           batch_intensities)),
    ('generate add user sun call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ADD_SUN,
                                                                           ctypes.pointer(args_sun_buie),
                                                                           ctypes.pointer(ctypes.c_double()),
                                                                           ctypes.pointer(ctypes.c_double()))),
    ('generate sun xyz call',                    stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SUN_XYZ, 608, 303, 1000)),
    ('generate sun userdata call',               stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SUN_USERDATA, 3, batch_angles, batch_intensities)),
    ('generate sim setup call',                  stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SIM_SETUP, dot_h.st_runner_type_t.NATIVE)),
    ('generate sim run v2 call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SIM_RUN_V2, )),
    ('generate sim report call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SIM_REPORT, 0)),
    ('generate write results csv call',          stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_WRITE_RESULTS_CSV, b'./batch_sample.csv')),
    ('generate locations call',                  stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_LOCATIONS, double_ptr, double_ptr, double_ptr)),
    ('generate cosines call',                    stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_COSINES, double_ptr, double_ptr, double_ptr)),
    ('generate elementmap call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_ELEMENTMAP, uint64_ptr)),
    ('generate stagemap call',                   stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_STAGEMAP, uint64_ptr)),
    ('generate raynumbers call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_RAYNUMBERS, uint64_ptr)),
    ('generate raynumbers call',                 stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_SUN_STATS,
                                                                           ctypes.pointer(c_double),
                                                                           ctypes.pointer(c_double),
                                                                           ctypes.pointer(c_double),
                                                                           ctypes.pointer(c_uint64))),
    ('generate get results data call',           stapi.generate_api_call, (dot_h.st_api_call.CALL_ST_GET_RESULTS_DATA, ctypes.pointer(results_args)))
]

def inner_delete_optic(_t: timer, count: int = 10):
    key = 'delete optic'
    stapi.reset()
    ids = [stapi.add_optical_properties_set(opt_set, front, back) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.delete_optic(i)
        _t.oc(key)
    return key

def inner_clear_optics(_t: timer, count: int = 10):
    key = 'clear optics'
    stapi.reset()
    for _ in range(count):
        for _ in range(10): stapi.add_optical_properties_set(opt_set, front, back)
        _t.ic(key)
        stapi.clear_optics()
        _t.oc(key)
    return key

def inner_add_element(_t: timer, count: int = 10):
    key = 'add element'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    for _ in range(count):
        _t.ic(key)
        stapi.add_element(el_args, opt_id, a_params, s_params)
        _t.oc(key)
    return key

def inner_delete_element(_t: timer, count: int = 10):
    key = 'delete element'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.delete_element(i)
        _t.oc(key)
    return key

def inner_clear_elements(_t: timer, count: int = 10):
    key = 'clear elements'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    for _ in range(count):
        for _ in range(10): stapi.add_element(el_args, opt_id, a_params, s_params)
        _t.ic(key)
        stapi.clear_elements()
        _t.oc(key)
    return key

def inner_element_enabled(_t: timer, count: int = 10):
    key = 'element enabled'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_enabled(i, True)
        _t.oc(key)
    return key

def inner_element_virtual(_t: timer, count: int = 10):
    key = 'element virtual'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_virtual(i, False)
        _t.oc(key)
    return key

def inner_element_xyz(_t: timer, count: int = 10):
    key = 'element xyz'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_xyz(i, 6.08, 6.08, 6.08)
        _t.oc(key)
    return key

def inner_element_aim(_t: timer, count: int = 10):
    key = 'element aim'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_aim(i, 6.08, 6.08, 6.08)
        _t.oc(key)
    return key

def inner_element_zrot(_t: timer, count: int = 10):
    key = 'element zrot'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_zrot(i, 6.08)
        _t.oc(key)
    return key

def inner_element_aperture(_t: timer, count: int = 10):
    key = 'element aperture'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_aperture(i, 'r', [6.08, 6.08])
        _t.oc(key)
    return key

def inner_element_surface(_t: timer, count: int = 10):
    key = 'element surface'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_surface(i, 's', [6.08])
        _t.oc(key)
    return key

def inner_element_optic(_t: timer, count: int = 10):
    key = 'element optic'
    stapi.reset()
    opt_id = stapi.add_optical_properties_set(opt_set, front, back)
    other_id = stapi.add_optical_properties_set(opt_set, front, back)
    ids = [stapi.add_element(el_args, opt_id, a_params, s_params) for _ in range(count)]
    for i in ids:
        _t.ic(key)
        stapi.element_optic(i, other_id)
        _t.oc(key)
    return key

def inner_add_sun_buie(_t: timer, count: int = 10):
    key = 'add sun buie'
    for _ in range(count):
        stapi.reset()
        _t.ic(key)
        stapi.add_sun(args_sun_buie)
        _t.oc(key)
    return key

def inner_add_sun_userdata(_t: timer, count: int = 10):
    key = 'add sun userdata'
    for _ in range(count):
        stapi.reset()
        _t.ic(key)
        stapi.add_sun(args_sun_user, _stjson.SUN_DEFAULT_USER_ANGLE, _stjson.SUN_DEFAULT_USER_INTENSITY)
        _t.oc(key)
    return key

def inner_check_success_code(_t: timer, count: int = 10):
    key = 'check success code'
    _, _, check_return_code = stapi.sneak()
    for _ in range(count):
        _t.ic(key)
        check_return_code(dot_h.st_return_code.SUCCESS)
        _t.oc(key)
    return key

def inner_check_error_code(_t: timer, count: int = 10):
    key = 'check error code'
    _, _, check_return_code = stapi.sneak()
    for _ in range(count):
        for c in range(1, dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE):
            try: 
                _t.ic(key)
                check_return_code(c)
            except: _t.oc(key)
    return key

stapi_func_calls = [
    ('read input json dict',       stapi.read_input_json,            (sample_json, )),
    ('read input json bytes',      stapi.read_input_json,            ('./sample.json', )),
    ('set simulation parameters',  stapi.set_simulation_parameters,  (sim_params, )),
    ('sim params',                 stapi.sim_params,                 (1, 100, True)),
    ('sim errors',                 stapi.sim_errors,                 (True, True)),
    ('sim location',               stapi.sim_location,               (35.962278, -106.5122622)),
    ('sim tolerance',              stapi.sim_tolerance,              (.1, )),
    ('num optics',                 stapi.num_optics,                 ()),
    ('add optical properties set', stapi.add_optical_properties_set, (opt_set, front, back)),
    ('',                           inner_delete_optic,               ()),
    ('',                           inner_clear_optics,               ()),
    ('num elements',               stapi.num_elements,               ()),
    ('',                           inner_add_element,                ()),
    ('',                           inner_delete_element,             ()),
    ('',                           inner_clear_elements,             ()),
    ('',                           inner_element_enabled,            ()),
    ('',                           inner_element_virtual,            ()),
    ('',                           inner_element_xyz,                ()),
    ('',                           inner_element_aim,                ()),
    ('',                           inner_element_zrot,               ()),
    ('',                           inner_element_aperture,           ()),
    ('',                           inner_element_surface,            ()),
    ('',                           inner_element_optic,              ()),
    ('',                           inner_add_sun_buie,               ()),
    ('',                           inner_add_sun_userdata,           ()),
    ('sun shape',                  stapi.sun_shape,                  ('b', .5)),
    ('sun xyz',                    stapi.sun_xyz,                    (6.08, 6.08, 6.08)),
    ('sun user data',              stapi.sun_userdata,               (len(_stjson.SUN_DEFAULT_USER_ANGLE),
                                                                      _stjson.SUN_DEFAULT_USER_ANGLE,
                                                                      _stjson.SUN_DEFAULT_USER_INTENSITY)),
    ('', inner_check_success_code, ()),
    ('', inner_check_error_code, ()),
]

def benchmark_simulation(runner_type):
    def inner(_t: timer, count: int = 10):
        keys = [f'set up {runner_type.name.lower()}',
                f'run {runner_type.name.lower()}',
                f'report {runner_type.name.lower()}',
                f'num intersections {runner_type.name.lower()}',
                f'locations {runner_type.name.lower()}',
                f'cosines {runner_type.name.lower()}',
                f'element map {runner_type.name.lower()}',
                f'stage map {runner_type.name.lower()}',
                f'ray numbers {runner_type.name.lower()}',
                f'sun stats {runner_type.name.lower()}',
                f'get results data {runner_type.name.lower()}']
        for _ in range(count):
            _stapi = STAPIv2(testing = True, benchmarking = True)
            _stapi.read_input_json('./sample.json')
            _t.ic(keys[0])
            _stapi.sim_setup(runner_type)
            _t.oc(keys[0])
            _t.ic(keys[1])
            _stapi.sim_run_v2()
            _t.oc(keys[1])
            _t.ic(keys[2])
            _stapi.sim_report()
            _t.oc(keys[2])
            _t.ic(keys[3])
            n = _stapi.num_intersections()
            _t.oc(keys[3])
            _t.ic(keys[4])
            _, _, _ = _stapi.locations(n)
            _t.oc(keys[4])
            _t.ic(keys[5])
            _, _, _ = _stapi.cosines(n)
            _t.oc(keys[5])
            _t.ic(keys[6])
            _ = _stapi.elementmap(n)
            _t.oc(keys[6])
            _t.ic(keys[7])
            _ = _stapi.stagemap(n)
            _t.oc(keys[7])
            _t.ic(keys[8])
            _ = _stapi.raynumbers(n)
            _t.oc(keys[8])
            _t.ic(keys[9])
            _, _, _, _ = _stapi.sun_stats()
            _t.oc(keys[9])
            _t.ic(keys[10])
            _ = _stapi.get_results_data(n)
            _t.oc(keys[10])
        # TODO: do variance controlled benchmarking on any/all of the variences here
        return [_t.summarize(k) for k in keys]
    return inner
    
skip_embree = 'embree' if stapi.is_runner_installed(dot_h.st_runner_type_t.EMBREE) else '_embree'
skip_optix  = 'optix' if stapi.is_runner_installed(dot_h.st_runner_type_t.OPTIX) else '_optix'

simulation_calls = [
    # ('native',    benchmark_simulation(dot_h.st_runner_type_t.NATIVE),  ()), # increase count -> (40, ) # ave ~ 1.51397166, comment out if don't want to wait
    (skip_embree, benchmark_simulation(dot_h.st_runner_type_t.EMBREE),  ()), # increase count -> (40, )
    (skip_optix,  benchmark_simulation(dot_h.st_runner_type_t.OPTIX),   ()), # increase count -> (40, ) # ave ~ .36015468, comment out if don't want to wait
]

def stash(t: timer):
    timed_keys, stats, _ = t.summary()
    # store average and standard deviation info
    stats = stats[:, 1:3]
    stats_cols = ['average', 'std']

    # store = benchmark_store().create(timed_keys, stats, stats_cols, datetime.now())
    store = benchmark_store().load('./benchmark_store.pickle')

    print(store.compare(timed_keys, stats, stats_cols))

    if input('store run? (y/other): ')[0].lower() == 'y':
        store.update(timed_keys, stats, stats_cols, datetime.now())
        store.dump('./benchmark_store.pickle')

if __name__ == '__main__':
    overall_t = timer()
    t = timer()
    results = []

    clean_bmf_name = lambda f: " ".join(f.__name__.split("_")[1:])

    # TODO: Point benchmarking

    overall_t.ic('stapi function calls')
    for key, f, args in stapi_func_calls:
        if key == None:
            print(f'skipping {clean_bmf_name(f)}...')
            continue
        print(f'benchmarking {key if len(key) else clean_bmf_name(f)}')
        results.append(do_var_ctrl_benchmark(t, generic_inner(key, f, args))
                       if len(key) else
                       do_var_ctrl_benchmark(t, f))
    overall_t.oc('stapi function calls')
    
    # for key, f, args in simulation_calls:
    #     if key[0] == '_':
    #         print(f'skipping {key[1:]}...')
    #         continue
    #     overall_t.ic(f'running sample {key}')
    #     print(f'benchmarking {key}')
    #     results.extend(f(t, *args))
    #     overall_t.oc(f'running sample {key}')

    # overall_t.ic('generate api calls')
    # for key, f, args in generate_api_func_args:
    #     results.append(do_var_ctrl_benchmark(t, generic_inner(key, f, args)))
    # overall_t.oc('generate api calls')

    print(f'\n\n{t}')
    print(f'\n\n{overall_t}')

    stash(t)