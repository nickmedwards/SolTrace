# Load the pysoltrace api from the parent directory ---
import ctypes, os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import STAPIv2, soltrace_constants as STC

from pysoltrace.timer import timer

t = timer()

if __name__ == '__main__':
    stapi = STAPIv2()

    for _ in range(10):
        t.ic('NO batch')
        stapi.read_input_json('../sample.json')
        count = stapi.num_elements()
        stapi.sim_setup(STC.OPTIX)
        stapi.sim_run_v2()
        t.oc('NO batch')

    for _ in range(10):
        f = open('../sample.json', mode='rb')
        t.ic('batch')
        pcount = ctypes.c_int()
        stapi.batch([
            stapi.generate_api_call(STC.CALL_ST_READ_INPUT_JSON, f.read()),
            stapi.generate_api_call(STC.CALL_ST_NUM_ELEMENTS, ctypes.pointer(pcount)),
            stapi.generate_api_call(STC.CALL_ST_SIM_SETUP, STC.OPTIX),
            stapi.generate_api_call(STC.CALL_ST_SIM_RUN_V2),
        ])
        t.oc('batch')

        f.close()
        count = pcount.value
    # print(count)
    


    print(t)