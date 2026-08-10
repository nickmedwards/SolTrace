"""
goal is get to something like geometry.Plant.batch_run + capabilities of pysoltrace

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

capabilities of pysoltrace
--------------------------
see luke's code for example.
"""

import atexit, os, pathlib, sys, warnings
from dataclasses import dataclass
from typing import Literal
import orjson # pyright: ignore[reportMissingImports]
# from ctypes import *
import ctypes
c_number = ctypes.c_double
from colorama import just_fix_windows_console, Fore, Back, Style
just_fix_windows_console()

from . import soltrace_constants as _STC

enumify = lambda arr: { k: i for i, k in enumerate(arr) }
"""make a list of things an enum (ish)"""

# want to remove from the final version
# from timer import timer
# from test_NSTTF import TEST

# t = timer()

###################################
# exception and warning reporting #
###################################
class STAPIv2Exception(Exception):
    def __init__(self, code, name, msg) -> None:
        super().__init__(f'{Fore.RED}[stapi_v2] - Call returned with error code ({code}: {name}).{Style.RESET_ALL}\n  {msg}')

STAPI_V2_WARNING_PREFIX = '[stapi_v2] - Call returned with warning code'
STAPIv2Warning = lambda code, name, msg: warnings.warn(
    f'{Fore.YELLOW}{STAPI_V2_WARNING_PREFIX} ({code}: {name}).{Style.RESET_ALL}\n  {msg}',
    stacklevel=4
)

#############################################################################
# STAPIv2 Class: wraps stapi_v2.{dll, so, dylib} with more Python-ish calls #
#############################################################################
class STAPIv2:
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
        print(f'{id(self.__pdll):#x}')
        max_key_len = max(len(str(k)) for k in self.__pdll.__dict__.keys())
        for k, v in self.__pdll.__dict__.items():
            print(f'\n{str(k):<{max_key_len}}: {v}')
            if (isinstance(v, ctypes._CFuncPtr)):
                print(f'{id(v):#x}')
                # for arg_t in v.argtypes: print(arg_t.__dict__)
                print(v.argtypes)

        ppcxt = ctypes.c_void_p()
        code = self.__pdll.st_create_context(ctypes.byref(ppcxt), self.__message_cb)
        self.__check_return_code(code)
        self.__pcxt = ppcxt.value
        atexit.register(self.__free)

        # keep the struct instances alive — ctypes.cast() does NOT keep a
        # reference, so if these get garbage collected the void* becomes dangling
        self.__stash_batch_args = []

    ##########################################
    # internal functions for CDLL management #
    ##########################################

    @staticmethod
    def __get_argtypes(args_struct: ctypes.Structure) -> list:
        return [_STC.ST_CONTEXT_V2_T, *[args[1] for args in args_struct._fields_]]

    def __setup_dll(self, _lib_path: str = ''):
        if not os.path.exists(_lib_path):
            raise FileNotFoundError(f'Could not find DLL at {_lib_path}')

        self.__pdll = ctypes.CDLL(_lib_path)
        self.__func_map = {}

        #############################################
        # functions for SolTrace context management #
        #############################################

        self.__pdll.st_create_context.argtypes = [ctypes.POINTER(_STC.ST_CONTEXT_V2_T),
                                                  ctypes.CFUNCTYPE(ctypes.c_int,
                                                                   ctypes.c_char_p,
                                                                   ctypes.c_char_p)]
        self.__pdll.st_create_context.restype = _STC.ST_RETURN_T

        self.__pdll.st_free_context.argtypes = [ctypes.c_void_p]
        self.__pdll.st_free_context.restype = _STC.ST_RETURN_T

        ##########################################
        # functions for SolTrace data management #
        ##########################################

        self.__pdll.st_read_input_json.argtypes = self.__get_argtypes(_STC.args_st_read_input_json)
        self.__pdll.st_read_input_json.restype = _STC.ST_RETURN_T
        self.__func_map[_STC.CALL_ST_READ_INPUT_JSON] = self.__pdll.st_read_input_json

        ###########################################
        # functions for SolTrace data information #
        ###########################################

        self.__pdll.st_num_elements.argtypes = self.__get_argtypes(_STC.args_st_num_elements)
        self.__pdll.st_num_elements.restype = _STC.ST_RETURN_T
        self.__func_map[_STC.CALL_ST_NUM_ELEMENTS] = self.__pdll.st_num_elements

        ############################################
        # functions for SolTrace runner management #
        ############################################

        self.__pdll.st_sim_setup.argtypes = self.__get_argtypes(_STC.args_st_sim_setup)
        self.__pdll.st_sim_setup.restype = _STC.ST_RETURN_T
        self.__func_map[_STC.CALL_ST_SIM_SETUP] = self.__pdll.st_sim_setup

        self.__pdll.st_sim_run_v2.argtypes = self.__get_argtypes(_STC.args_st_sim_run_v2)
        self.__pdll.st_sim_run_v2.restype = _STC.ST_RETURN_T
        self.__func_map[_STC.CALL_ST_SIM_RUN_V2] = self.__pdll.st_sim_run_v2

        # TODO: include enum-ish of reporting levels
        self.__pdll.st_sim_report.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.__pdll.st_sim_report.restype = _STC.ST_RETURN_T

        #############################################
        # functions for SolTrace results management #
        #############################################

        self.__pdll.st_write_results_csv.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.__pdll.st_write_results_csv.restype = _STC.ST_RETURN_T

        ############################################
        # function for batching SolTrace API calls #
        ############################################

        self.__api_func_ptr = ctypes.CFUNCTYPE(_STC.ST_RETURN_T, ctypes.c_void_p)
        self.__pdll.st_batch.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(ctypes.c_void_p),
                                         ctypes.POINTER(ctypes.c_void_p),
                                         ctypes.c_uint,
                                         ctypes.POINTER(ctypes.c_uint)]
        self.__pdll.st_batch.restype = _STC.ST_RETURN_T

    def __free(self):
        code = self.__pdll.st_free_context(self.__pcxt)
        sys.stdout.write(f'Freed context ({self.__pcxt:#x}) with code ({code}) from SolTrace DLL ({self.__pdll})\n')

    def __check_return_code(self, st_return_code):
        if st_return_code in _STC.ST_RETURN_CODE_ERROR_MSG:
            raise STAPIv2Exception(st_return_code, 
                                   _STC.ST_RETURN_CODE_NAME[st_return_code],
                                   _STC.ST_RETURN_CODE_ERROR_MSG[st_return_code])
        elif st_return_code in _STC.ST_RETURN_CODE_WARNING_MSG:
            STAPIv2Warning(st_return_code,
                           _STC.ST_RETURN_CODE_NAME[st_return_code],
                           _STC.ST_RETURN_CODE_WARNING_MSG[st_return_code])

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)
    def __message_cb(loc, msg):
        sys.stdout.write(f"{Fore.MAGENTA}[stapi_v2] - Message callback triggered by ({loc.decode('utf-8')}){Style.RESET_ALL}: {msg.decode('utf-8')}\n")
        return 0
    
    def sneak(self): return self.__pdll, self.__pcxt

    """Python handles for st_ functions"""

    ##########################################
    # functions for SolTrace data management #
    ##########################################

    def read_input_json(self, input_json: str | dict) -> None:
        # TODO: togglable validity check?
        if isinstance(input_json, str):
            f = open(input_json, mode='rb')
            code = self.__pdll.st_read_input_json(self.__pcxt, f.read())
            f.close()
        else:
            code = self.__pdll.st_read_input_json(self.__pcxt, orjson.dumps(input_json))
        self.__check_return_code(code)

    ###########################################
    # functions for SolTrace data information #
    ###########################################

    def num_elements(self) -> int:
        pcount = ctypes.c_int()
        code = self.__pdll.st_num_elements(self.__pcxt, ctypes.byref(pcount))
        self.__check_return_code(code)
        return pcount.value

    ############################################
    # functions for SolTrace runner management #
    ############################################

    def sim_setup(self, 
                  runner_type: Literal[0, 1, 2], 
                  num_threads: int = 8, 
                  seeds: list = None) -> None:
        num_seeds = 0
        # redefine seeds from list to C array
        if seeds:
            num_seeds = len(seeds)
            seeds = (ctypes.c_uint * num_seeds)(*seeds)
        code = self.__pdll.st_sim_setup(self.__pcxt, runner_type, num_threads, seeds, num_seeds)
        self.__check_return_code(code)

    def sim_run_v2(self) -> None:
        code = self.__pdll.st_sim_run_v2(self.__pcxt)
        self.__check_return_code(code)

    def sim_report(self, level: int = 0) -> None:
        code = self.__pdll.st_sim_report(self.__pcxt, level)
        self.__check_return_code(code)

    #############################################
    # functions for SolTrace resutls management #
    #############################################

    def write_results_csv(self, filename: str, precision: int = 12) -> None:
        code = self.__pdll.st_write_results_csv(self.__pcxt, filename.encode('utf-8'), precision)
        self.__check_return_code(code)

    #####################
    # Batch caller work #
    #####################

    def generate_api_call(self, call_type: int, *args):
        if not call_type < _STC.API_CALL_COUNT: raise ValueError(f'Invalid st_api_v2 batch call ({call_type}).')
        print(f'\n\n{_STC.ST_API_CALL_NAME[call_type]}')
        # call_type = STAPIv2.ST_API_CALL[call_name]
        rt = _STC.st_api_call_args()
        rt.type = call_type
        args_name, args_cls = rt.payload._fields_[call_type]
        args_payload = getattr(rt.payload, args_name)
        # print(args_name)
        # print(args_cls)
        # print(args_payload)
        # print(args_payload._fields_)
        # print(args)

        args_payload.pcxt = self.__pcxt
        for i, arg in enumerate(args):
            setattr(args_payload, 
                    args_payload._fields_[i][0],
                    arg)
            
        # print('\nres')
        # for field in args_payload._fields_:
        #     temp_payload_attr = getattr(rt.payload, args_name)
        #     print(getattr(temp_payload_attr, field[0]))
        # print()

        return _STC.st_api_pair(self.__func_map[call_type], rt)

    def dump_batch_args(self):
        for args in self.__stash_batch_args: print(args)

    # TODO: include version that calls functions from python for debugging STAPIv2.generate_api_call
    def batch(self, api_pairs: list[_STC.st_api_pair]):
        num_calls = len(api_pairs)
        # unzip pairs
        func_addrs = []
        call_args = []
        for pair in api_pairs:
            # print(pair.func)
            # print(f'{id(pair.func):#x}')
            func_addrs.append(ctypes.cast(pair.func, ctypes.c_void_p).value)
            call_args.append(pair.args)
        for addr in func_addrs: print(f'{addr:#x}')
        print(call_args)
        self.__stash_batch_args = call_args

        func_arr = (ctypes.c_void_p * num_calls)(*func_addrs)
        args_arr = (ctypes.c_void_p * num_calls)(*[
            ctypes.cast(ctypes.byref(c), ctypes.c_void_p) for c in call_args
        ])

        fail_iteration = ctypes.c_uint(0)

        code = self.__pdll.st_batch(self.__pcxt,
                                    func_arr,
                                    args_arr,
                                    num_calls,
                                    ctypes.byref(fail_iteration))
        # TODO: raise new btach exception with fail_iteration
        self.__check_return_code(code)


if __name__ == "__main__":
    username = os.environ.get('USERNAME') # f'C:\\Users\\{username}\\build-soltrace\\soltrace\\coretrace\\stapi_v2\\RelWithDebInfo\\stapi_v2.dll'
    stapi = STAPIv2()
    stapi.read_input_json('./sample.json')
    count = stapi.num_elements()
    print(count)
    # stapi.sim_setup(NATIVE)
    # stapi.sim_run_v2()
    # stapi.sim_report()
    # stapi.write_results_csv('./sample.csv')


    # currently not building Embrre - emits warning
    # stapi.sim_setup(EMBREE)
    # raises STAPIv2Exception
    # stapi.sim_setup(NATIVE, 8, [608, 303])


"""

"""