# Load the pysoltrace api from the parent directory ---
import ctypes, os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import STAPIv2

if __name__ == '__main__':
    stapi = STAPIv2()

    # print(STAPIv2.CALL_ST_READ_INPUT_JSON)
    f = open('../sample.json', mode='rb')

    pcount = ctypes.c_int()
    stapi.batch([
        stapi.generate_api_call(STAPIv2.CALL_ST_READ_INPUT_JSON, f.read()),
        stapi.generate_api_call(STAPIv2.CALL_ST_NUM_ELEMENTS, ctypes.pointer(pcount)),
        stapi.generate_api_call(STAPIv2.CALL_ST_SIM_SETUP, STAPIv2.ST_RUNNER_TYPE['OPTIX']),
        stapi.generate_api_call(STAPIv2.CALL_ST_SIM_RUN_V2),
    ])
    f.close()
    count = pcount.value
    print(count)
    

    # stapi.read_input_json('../sample.json')
    # count = stapi.num_elements()
    # print(count)