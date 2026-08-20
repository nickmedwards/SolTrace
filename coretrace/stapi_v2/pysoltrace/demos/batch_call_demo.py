# Load the pysoltrace api from the parent directory ---
import ctypes, os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import STAPIv2, dot_h, found_in

from pysoltrace.timer import timer

t = timer()

if __name__ == '__main__':
    stapi = STAPIv2()
    # print(f'\n\n\n\n{found_in(dot_h)}\n\n\n\n')
    dummy_array = (ctypes.c_double * 0)(*[])
    test = stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_SUN,
                                  ctypes.pointer(dot_h.args_sun(0, 608, 303, 1000, 5, 'g'.encode())),
                                  ctypes.pointer(ctypes.c_double()),
                                  ctypes.pointer(ctypes.c_double()))
    print(test)
    print(test.payload._fields_[test.type])
    arg_name = test.payload._fields_[test.type][0]

    for field in getattr(test.payload, arg_name)._fields_:
        temp_payload_attr = getattr(test.payload, test.payload._fields_[test.type][0])
        print(getattr(temp_payload_attr, field[0]).value)
    # print(dummy_list)
    # print('timing comparison')
    # for _ in range(10):
    #     t.ic('NO batch')
    #     stapi.read_input_json('../sample.json')
    #     count = stapi.num_elements()
    #     stapi.sim_setup(dot_h.st_runner_type_t.OPTIX)
    #     stapi.sim_run_v2()
    #     t.oc('NO batch')

    # for _ in range(10):
    #     f = open('../sample.json', mode='rb')
    #     t.ic('batch')
    #     pcount = ctypes.c_uint64()
    #     stapi.batch([
    #         stapi.generate_api_call(dot_h.st_api_call.CALL_ST_READ_INPUT_JSON, f.read()),
    #         stapi.generate_api_call(dot_h.st_api_call.CALL_ST_NUM_ELEMENTS, ctypes.pointer(pcount)),
    #         stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_SETUP, dot_h.st_runner_type_t.OPTIX),
    #         stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_RUN_V2),
    #     ])
    #     t.oc('batch')

    #     f.close()
    #     count = pcount.value
    # print(count)
    # print(t)