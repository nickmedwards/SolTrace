"""
goal is get to something like geometry.Plant.batch_run + capabilities of PySolTrace

something like geometry.Plant.batch_run
---------------------------------------
import stapi_v2 as st

st.batch_run(
    scene_update_cb,
    results_location, (maybe cb)
    runner,
    report_level,
    verbose,
    timing
)

capabilities of PySolTrace
--------------------------
see luke's code for example.
"""

import atexit, os, pathlib, sys, warnings
import orjson # pyright: ignore[reportMissingImports]
from ctypes import *
c_number = c_double

enumify = lambda arr: { k: i for i, k in enumerate(arr) }
"""make a list of things an enum (ish)"""

# want to remove from the final version
# from timer import timer
# from test_NSTTF import TEST

# t = timer()

#########################
# st_return_code set up #
#########################
SUCCESS                                      = 'SUCCESS'
FAILURE                                      = 'FAILURE'
CANCEL                                       = 'CANCEL'
CONTEXT_NOT_FOUND                            = 'CONTEXT_NOT_FOUND'
DATA_NOT_FOUND                               = 'DATA_NOT_FOUND'
RUNNER_NOT_FOUND                             = 'RUNNER_NOT_FOUND'
RESULT_NOT_FOUND                             = 'RESULT_NOT_FOUND'
RUNNER_INILIALIZE_FAILURE                    = 'RUNNER_INILIALIZE_FAILURE'
RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE = 'RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE'
RUNNER_SETUP_FAILURE                         = 'RUNNER_SETUP_FAILURE'
RUNNER_NOT_READY                             = 'RUNNER_NOT_READY'
RUNTIME_ERROR                                = 'RUNTIME_ERROR'
WARNING_FELLBACK_FROM_EMBREE                 = 'WARNING_FELLBACK_FROM_EMBREE'
WARNING_FELLBACK_FROM_OPTIX                  = 'WARNING_FELLBACK_FROM_OPTIX'
WARNING_ARGUMENT_IGNORED_BY_RUNNER           = 'WARNING_ARGUMENT_IGNORED_BY_RUNNER'
RETURN_COUNT                                 = 'RETURN_COUNT'



# Callback to print command line progress messages
# callback_t = CFUNCTYPE(c_int, c_char_p, c_char_p)

@CFUNCTYPE(c_int, c_char_p, c_char_p)
def api_callback(loc, msg):
    print(loc.decode('utf-8') + ': ' + msg.decode('utf-8'))
    return 1

# c_api_callback = callback_t(api_callback)

class STAPIv2Exception(Exception):
    def __init__(self, code, name, msg) -> None:
        super().__init__(f'[stapi_v2] - Call returned with error code ({code}: {name}). {msg}')

STAPI_V2_WARNING_PREFIX = '[stapi_v2] - Call returned with warning code'
STAPIv2Warning = lambda code, name, msg: warnings.warn(
    f'{STAPI_V2_WARNING_PREFIX} ({code}: {name}). {msg}',
    stacklevel=2
)

class STAPIv2:
    ST_RETURN_CODES = [
        SUCCESS,
        FAILURE,
        CANCEL,
        CONTEXT_NOT_FOUND,
        DATA_NOT_FOUND,
        RUNNER_NOT_FOUND,
        RESULT_NOT_FOUND,
        RUNNER_INILIALIZE_FAILURE,
        RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE,
        RUNNER_SETUP_FAILURE,
        RUNNER_NOT_READY,
        RUNTIME_ERROR,
        WARNING_FELLBACK_FROM_EMBREE,
        WARNING_FELLBACK_FROM_OPTIX,
        WARNING_ARGUMENT_IGNORED_BY_RUNNER,
        RETURN_COUNT
    ]
    ST_RETURN_CODE = enumify(ST_RETURN_CODES)
    ST_RETURN_CODE_ERROR_MSGS = {
        ST_RETURN_CODE[FAILURE]:                                      '',
        ST_RETURN_CODE[CANCEL]:                                       'Simulation canceled.',
        ST_RETURN_CODE[CONTEXT_NOT_FOUND]:                            'Context pointer could not be cast as context.',
        ST_RETURN_CODE[DATA_NOT_FOUND]:                               'SimulationData pointer could not be found in context.',
        ST_RETURN_CODE[RUNNER_NOT_FOUND]:                             'SimulationRunner pointer could not be found in context.',
        ST_RETURN_CODE[RESULT_NOT_FOUND]:                             'SimulationResult pointer could not be found in context.',
        ST_RETURN_CODE[RUNNER_INILIALIZE_FAILURE]:                    'SimulationRunner could not be initialized.',
        ST_RETURN_CODE[RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE]: 'Number of threads requested and length of seeds list are not equal. Include the number of seeds as threads requested.',
        ST_RETURN_CODE[RUNNER_SETUP_FAILURE]:                         'SimulationRunner could not be set up based on SimulationData provided.',
        ST_RETURN_CODE[RUNNER_NOT_READY]:                             'SimulationRunner is not ready for operation. Set up the SimulationRunner or run the simulation.',
        ST_RETURN_CODE[RUNTIME_ERROR]:                                'RuntimeError raised. Check validity of JSON against SolTrace schema version used.',
    }
    ST_RETURN_CODE_WARNING_MSGS = {
        ST_RETURN_CODE[WARNING_FELLBACK_FROM_EMBREE]: 'Requested EmbreeRunner, but is not installed. Fellback to NativeRunner.',
        ST_RETURN_CODE[WARNING_FELLBACK_FROM_OPTIX]: 'Requested OptixRunner, but is not installed. Fellback to NativeRunner.',
        ST_RETURN_CODE[WARNING_ARGUMENT_IGNORED_BY_RUNNER]: 'Requested a number of threads for OptixRunner. The arguement does not apply to this runner type and was ignored.',
    }

    def __init__(self, stapi_v2_dll_path: str = ''):
        if len(stapi_v2_dll_path): self.__setup_dll(stapi_v2_dll_path)
        else:
            _here = pathlib.Path(__file__).parent.resolve()
            
            # 2. Determine the shared library filename based on the OS
            if sys.platform == "win32":
                _lib_name = "stapi_v2.dll"
            elif sys.platform == "darwin":
                _lib_name = "stapi_v2.dylib"
            else:
                _lib_name = "stapi_v2.so" # Note: CMake typically prepends "lib" on Linux/macOS
    
            _lib_path = _here / _lib_name
            self.__setup_dll(_lib_path)

        # print(self.__pdll.__dict__)
        max_key_len = max(len(str(k)) for k in self.__pdll.__dict__.keys())
        for k, v in self.__pdll.__dict__.items():
            print(f'{str(k):<{max_key_len}}: {v}')

        ppcxt = c_void_p()
        code = self.__pdll.st_create_context(byref(ppcxt), api_callback)
        self.__check_return_code(code)
        self.__pcxt = ppcxt.value
        print(self.__pcxt)
        atexit.register(self.__free)

    def __setup_dll(self, _lib_path: str = ''):
        if not os.path.exists(_lib_path):
            raise FileNotFoundError(f'Could not find DLL at {_lib_path}')

        self.__pdll = CDLL(_lib_path)

        #############################################
        # functions for SolTrace context management #
        #############################################

        self.__pdll.st_create_context.argtypes = [POINTER(c_void_p), CFUNCTYPE(c_int, c_char_p, c_char_p)]
        self.__pdll.st_create_context.restype = c_int

        self.__pdll.st_free_context.argtypes = [c_void_p]
        self.__pdll.st_free_context.restype = c_int

        ##########################################
        # functions for SolTrace data management #
        ##########################################

        self.__pdll.st_read_input_json.argtypes = [c_void_p, c_char_p]
        self.__pdll.st_read_input_json.restype = c_int

        ###########################################
        # functions for SolTrace data information #
        ###########################################

        self.__pdll.st_num_elements.argtypes = [c_void_p]
        self.__pdll.st_num_elements.restype = c_int

    def __free(self):
        code = self.__pdll.st_free_context(self.__pcxt)
        print(f'Freed context ({self.__pcxt:#x}) with code ({code}) from SolTrace DLL ({self.__pdll})')

    def __check_return_code(self, st_return_code):
        if st_return_code in STAPIv2.ST_RETURN_CODE_ERROR_MSGS:
            raise STAPIv2Exception(st_return_code, 
                                   STAPIv2.ST_RETURN_CODES[st_return_code],
                                   STAPIv2.ST_RETURN_CODE_ERROR_MSGS[st_return_code])
        elif st_return_code in STAPIv2.ST_RETURN_CODE_WARNING_MSGS:
            STAPIv2Warning(st_return_code,
                           STAPIv2.ST_RETURN_CODES[st_return_code],
                           STAPIv2.ST_RETURN_CODE_WARNING_MSGS[st_return_code])

    def read_input_json(self, input_json: str | dict):
        # TODO: togglable validity check?
        if isinstance(input_json, str):
            f = open(input_json, mode='rb')
            code = self.__pdll.st_read_input_json(self.__pcxt, f.read())
            f.close()
        else:
            code = self.__pdll.st_read_input_json(self.__pcxt, orjson.dumps(input_json))
        self.__check_return_code(code)

    def num_elements(self):
        pcount = c_int()
        code = self.__pdll.st_num_elements(self.__pcxt, byref(pcount))
        self.__check_return_code(code)
        return pcount.value

    def sneak(self): return self.__pdll, self.__pcxt

if __name__ == "__main__":
    api = STAPIv2()
    api.read_input_json('./sample.json')
    count = api.num_elements()
    print(count)
