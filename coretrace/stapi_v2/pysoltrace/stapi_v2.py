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
import orjson
import ctypes
c_number = ctypes.c_double
from colorama import just_fix_windows_console, Fore, Back, Style
just_fix_windows_console()

try:
    from chedder import dot_h, found_in
    import soltrace_constants as _STC
    from point import Point
    from timer import timer # pyright: ignore[reportMissingModuleSource]
except ImportError:
    from .chedder import dot_h, found_in
    from . import soltrace_constants as _STC
    from .point import Point
    from .timer import timer

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
        self.code = code
        self.name = name
        self.message = msg

STAPI_V2_WARNING_PREFIX = '[stapi_v2] - Call returned with warning code'
STAPIv2Warning = lambda code, name, msg: warnings.warn(
    f'{Fore.YELLOW}{STAPI_V2_WARNING_PREFIX} ({code}: {name}).{Style.RESET_ALL}\n  {msg}',
    stacklevel=4
)

#############################################################################
# STAPIv2 Class: wraps stapi_v2.{dll, so, dylib} with more Python-ish calls #
#############################################################################
class STAPIv2:
    def __init__(self, stapi_v2_dll_path: str = '', testing: bool = False, benchmarking: bool = False):
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

        ppcxt = ctypes.c_void_p()
        code = self.__pdll.st_create_context(ctypes.pointer(ppcxt), self.__message_cb if not testing else self.__testing_cb)
        self.__check_return_code(code)
        self.__pcxt = ppcxt.value
        # TODO: self._finalizer = weakref.finalize(self, __free) might be better option
        atexit.register(self.__free)

        # keep the struct instances alive — ctypes.cast() does NOT keep a
        # reference, so if these get garbage collected the void* becomes dangling
        self.__stash_batch_args = []

        self.__testing = testing
        self.__benchmarking = benchmarking

    def __repr__(self):
        rt = f'STAPIv2 Object at ({id(self.__pdll):#x})'
        rt += '\n' + '-' * len(rt) + '\n'

        runners = self.get_installed_runners()
        rt += f'Installed Runners: ' + ', '.join([k for k, v in runners.items() if v]) + '\n'
        max_key_len = max(len(str(k)) for k in self.__pdll.__dict__.keys())
        for k, v in self.__pdll.__dict__.items():
            rt += f'\n{str(k):<{max_key_len}}: {v}'
            if (isinstance(v, ctypes._CFuncPtr)):
                rt += f'\n{" " * max_key_len}: {[_STC._CTYPES_RE.search(str(arg)).group() for arg in v.argtypes]}'
        return rt

    ##########################################
    # internal functions for CDLL management #
    ##########################################

    @staticmethod
    def __get_argtypes(args_struct: ctypes.Structure) -> list:
        return [dot_h.st_context_v2_t, *[args[1] for args in args_struct._fields_]]

    def __setup_dll(self, _lib_path: str = ''):
        if not os.path.exists(_lib_path):
            raise FileNotFoundError(f'Could not find DLL at {_lib_path}')

        if sys.platform == "win32":
            os.add_dll_directory(str(_lib_path).rsplit(os.sep, maxsplit=1)[0])
            self.__pdll = ctypes.WinDLL(_lib_path, winmode=0)
        else: self.__pdll = ctypes.CDLL(_lib_path)
        self.__func_map = {}

        #############################################
        # functions for SolTrace context management #
        #############################################

        # warning that: "The function "POINTER" is deprecated ctypes.POINTER with string"
        # dot_h.st_context_v2_t is <class 'ctypes.c_void_p'> which is not deprecated
        # see ctypes entry for more information on the following Python docs page
        # here: https://docs.python.org/3/whatsnew/3.14.html#new-deprecations 
        self.__pdll.st_create_context.argtypes = [ctypes.POINTER(dot_h.st_context_v2_t),
                                                  ctypes.CFUNCTYPE(ctypes.c_int,
                                                                   ctypes.c_char_p,
                                                                   ctypes.c_char_p)]
        self.__pdll.st_create_context.restype  = dot_h.st_return_t

        self.__pdll.st_reset_context.argtypes = [ctypes.c_void_p]
        self.__pdll.st_reset_context.restype  = dot_h.st_return_t

        self.__pdll.st_free_context.argtypes = [ctypes.c_void_p]
        self.__pdll.st_free_context.restype  = dot_h.st_return_t

        ##########################################
        # functions for SolTrace data management #
        ##########################################
        
        ##############################################################
        # functions for simulation data management thru json strings #
        ##############################################################

        self.__pdll.st_read_input_json.argtypes = self.__get_argtypes(dot_h.args_st_read_input_json)
        self.__pdll.st_read_input_json.restype  = dot_h.st_return_t
        self.__func_map[dot_h.st_api_call.CALL_ST_READ_INPUT_JSON] = self.__pdll.st_read_input_json

        #####################################################
        # functions for simulation data management directly #
        #####################################################

        self.__pdll.st_set_simulation_parameters.argtypes = self.__get_argtypes(dot_h.args_st_set_simulation_parameters)
        self.__pdll.st_set_simulation_parameters.restype  = dot_h.st_return_t

        self.__pdll.st_sim_params.argtypes = self.__get_argtypes(dot_h.args_st_sim_params)
        self.__pdll.st_sim_params.restype  = dot_h.st_return_t

        self.__pdll.st_sim_errors.argtypes = self.__get_argtypes(dot_h.args_st_sim_errors)
        self.__pdll.st_sim_errors.restype  = dot_h.st_return_t

        self.__pdll.st_sim_location.argtypes = self.__get_argtypes(dot_h.args_st_sim_location)
        self.__pdll.st_sim_location.restype  = dot_h.st_return_t

        self.__pdll.st_sim_tolerance.argtypes = self.__get_argtypes(dot_h.args_st_sim_tolerance)
        self.__pdll.st_sim_tolerance.restype  = dot_h.st_return_t

        self.__pdll.st_get_simulation_parameters.argtypes = self.__get_argtypes(dot_h.args_st_get_simulation_parameters)
        self.__pdll.st_get_simulation_parameters.restype  = dot_h.st_return_t
        
        ##################################################
        # functions to add/remove/set optical properties #
        ##################################################

        self.__pdll.st_num_optics.argtypes = self.__get_argtypes(dot_h.args_st_num_optics)
        self.__pdll.st_num_optics.restype  = dot_h.st_return_t

        self.__pdll.st_add_optical_properties_set.argtypes = self.__get_argtypes(dot_h.args_st_add_optical_properties_set)
        self.__pdll.st_add_optical_properties_set.restype  = dot_h.st_return_t
        
        self.__pdll.st_get_optical_properties_set.argtypes = self.__get_argtypes(dot_h.args_st_get_optical_properties_set)
        self.__pdll.st_get_optical_properties_set.restype  = dot_h.st_return_t

        self.__pdll.st_delete_optic.argtypes = self.__get_argtypes(dot_h.args_st_delete_optic)
        self.__pdll.st_delete_optic.restype  = dot_h.st_return_t

        self.__pdll.st_clear_optics.argtypes = self.__get_argtypes(dot_h.args_st_clear_optics)
        self.__pdll.st_clear_optics.restype  = dot_h.st_return_t

        ####################################
        # functions to add/remove elements #
        ####################################

        self.__pdll.st_num_elements.argtypes = self.__get_argtypes(dot_h.args_st_num_elements)
        self.__pdll.st_num_elements.restype  = dot_h.st_return_t
        self.__func_map[dot_h.st_api_call.CALL_ST_NUM_ELEMENTS] = self.__pdll.st_num_elements

        self.__pdll.st_add_element.argtypes = self.__get_argtypes(dot_h.args_st_add_element)
        self.__pdll.st_add_element.restype  = dot_h.st_return_t
        
        self.__pdll.st_get_element.argtypes = self.__get_argtypes(dot_h.args_st_get_element)
        self.__pdll.st_get_element.restype  = dot_h.st_return_t

        self.__pdll.st_delete_element.argtypes = self.__get_argtypes(dot_h.args_st_delete_element)
        self.__pdll.st_delete_element.restype  = dot_h.st_return_t

        self.__pdll.st_clear_elements.argtypes = self.__get_argtypes(dot_h.args_st_clear_elements)
        self.__pdll.st_clear_elements.restype  = dot_h.st_return_t

        ################################
        # functions to modify elements #
        ################################

        self.__pdll.st_element_enabled.argtypes = self.__get_argtypes(dot_h.args_st_element_enabled)
        self.__pdll.st_element_enabled.restype  = dot_h.st_return_t

        self.__pdll.st_element_virtual.argtypes = self.__get_argtypes(dot_h.args_st_element_virtual)
        self.__pdll.st_element_virtual.restype  = dot_h.st_return_t

        self.__pdll.st_element_xyz.argtypes = self.__get_argtypes(dot_h.args_st_element_xyz)
        self.__pdll.st_element_xyz.restype  = dot_h.st_return_t

        self.__pdll.st_element_aim.argtypes = self.__get_argtypes(dot_h.args_st_element_aim)
        self.__pdll.st_element_aim.restype  = dot_h.st_return_t

        self.__pdll.st_element_zrot.argtypes = self.__get_argtypes(dot_h.args_st_element_zrot)
        self.__pdll.st_element_zrot.restype  = dot_h.st_return_t

        self.__pdll.st_element_aperture.argtypes = self.__get_argtypes(dot_h.args_st_element_aperture)
        self.__pdll.st_element_aperture.restype  = dot_h.st_return_t

        self.__pdll.st_element_surface.argtypes = self.__get_argtypes(dot_h.args_st_element_surface)
        self.__pdll.st_element_surface.restype  = dot_h.st_return_t

        self.__pdll.st_element_optic.argtypes = self.__get_argtypes(dot_h.args_st_element_optic)
        self.__pdll.st_element_optic.restype  = dot_h.st_return_t
        
        #################
        # sun functions #
        #################

        self.__pdll.st_add_sun.argtypes = self.__get_argtypes(dot_h.args_st_add_sun)
        self.__pdll.st_add_sun.restype  = dot_h.st_return_t
        
        self.__pdll.st_get_sun.argtypes = self.__get_argtypes(dot_h.args_st_get_sun)
        self.__pdll.st_get_sun.restype  = dot_h.st_return_t

        self.__pdll.st_sun_shape.argtypes = self.__get_argtypes(dot_h.args_st_sun_shape)
        self.__pdll.st_sun_shape.restype  = dot_h.st_return_t
        
        self.__pdll.st_sun_xyz.argtypes = self.__get_argtypes(dot_h.args_st_sun_xyz)
        self.__pdll.st_sun_xyz.restype  = dot_h.st_return_t
        self.__func_map[dot_h.st_api_call.CALL_ST_SUN_XYZ] = self.__pdll.st_sun_xyz

        self.__pdll.st_sun_position.argtypes = self.__get_argtypes(dot_h.args_st_sun_position)
        self.__pdll.st_sun_position.restype  = dot_h.st_return_t
        self.__func_map[dot_h.st_api_call.CALL_ST_SUN_POSITION] = self.__pdll.st_sun_position

        self.__pdll.st_sun_userdata.argtypes = self.__get_argtypes(dot_h.args_st_sun_userdata)
        self.__pdll.st_sun_userdata.restype  = dot_h.st_return_t
        self.__func_map[dot_h.st_api_call.CALL_ST_SUN_USERDATA] = self.__pdll.st_sun_userdata

        self.__pdll.st_get_sun_az_zen.argtypes = self.__get_argtypes(dot_h.args_st_get_sun_az_zen)
        self.__pdll.st_get_sun_az_zen.restype  = dot_h.st_return_t
                
        self.__pdll.st_get_sun_az_el.argtypes = self.__get_argtypes(dot_h.args_st_get_sun_az_el)
        self.__pdll.st_get_sun_az_el.restype  = dot_h.st_return_t
                
        self.__pdll.st_get_sun_vector.argtypes = self.__get_argtypes(dot_h.args_st_get_sun_vector)
        self.__pdll.st_get_sun_vector.restype  = dot_h.st_return_t

        ##################################################
        # functions for writing input files for SolTrace #
        ##################################################

        self.__pdll.st_export_json_file.argtypes = self.__get_argtypes(dot_h.args_st_export_json_file)
        self.__pdll.st_export_json_file.restype  = dot_h.st_return_t

        ############################################
        # functions for SolTrace runner management #
        ############################################

        self.__pdll.st_get_installed_runners.argtypes = self.__get_argtypes(dot_h.args_st_get_installed_runners)
        self.__pdll.st_get_installed_runners.restype  = dot_h.st_return_t

        self.__pdll.st_is_runner_installed.argtypes = self.__get_argtypes(dot_h.args_st_is_runner_installed)
        self.__pdll.st_is_runner_installed.restype  = dot_h.st_return_t

        self.__pdll.st_sim_setup.argtypes = self.__get_argtypes(dot_h.args_st_sim_setup)
        self.__pdll.st_sim_setup.restype  = dot_h.st_return_t
        self.__func_map[dot_h.st_api_call.CALL_ST_SIM_SETUP] = self.__pdll.st_sim_setup

        self.__pdll.st_sim_run_v2.argtypes = self.__get_argtypes(dot_h.args_st_sim_run_v2)
        self.__pdll.st_sim_run_v2.restype  = dot_h.st_return_t
        self.__func_map[dot_h.st_api_call.CALL_ST_SIM_RUN_V2] = self.__pdll.st_sim_run_v2

        # TODO: include enum-ish of reporting levels
        self.__pdll.st_sim_report.argtypes = [ctypes.c_void_p, ctypes.c_int]
        self.__pdll.st_sim_report.restype  = dot_h.st_return_t

        #############################################
        # functions for SolTrace results management #
        #############################################

        self.__pdll.st_write_results_csv.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_int]
        self.__pdll.st_write_results_csv.restype  = dot_h.st_return_t

        #####################################
        # functions to get results directly #
        #####################################

        self.__pdll.st_num_intersections.argtypes = self.__get_argtypes(dot_h.args_st_num_intersections)
        self.__pdll.st_num_intersections.restype  = dot_h.st_return_t
        
        self.__pdll.st_locations.argtypes = self.__get_argtypes(dot_h.args_st_locations)
        self.__pdll.st_locations.restype  = dot_h.st_return_t
        
        self.__pdll.st_cosines.argtypes = self.__get_argtypes(dot_h.args_st_cosines)
        self.__pdll.st_cosines.restype  = dot_h.st_return_t
        
        self.__pdll.st_elementmap.argtypes = self.__get_argtypes(dot_h.args_st_elementmap)
        self.__pdll.st_elementmap.restype  = dot_h.st_return_t
        
        self.__pdll.st_stagemap.argtypes = self.__get_argtypes(dot_h.args_st_stagemap)
        self.__pdll.st_stagemap.restype  = dot_h.st_return_t
        
        self.__pdll.st_raynumbers.argtypes = self.__get_argtypes(dot_h.args_st_raynumbers)
        self.__pdll.st_raynumbers.restype  = dot_h.st_return_t
        
        self.__pdll.st_sun_stats.argtypes = self.__get_argtypes(dot_h.args_st_sun_stats)
        self.__pdll.st_sun_stats.restype  = dot_h.st_return_t
        
        self.__pdll.st_get_results_data.argtypes = self.__get_argtypes(dot_h.args_st_get_results_data)
        self.__pdll.st_get_results_data.restype  = dot_h.st_return_t

        ############################################
        # function for batching SolTrace API calls #
        ############################################

        self.__api_func_ptr = ctypes.CFUNCTYPE(dot_h.st_return_t, ctypes.c_void_p)
        self.__pdll.st_batch.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(ctypes.c_void_p),
                                        #  ctypes.POINTER(ctypes.POINTER(dot_h.st_api_call_args)),
                                         ctypes.c_uint,
                                         ctypes.POINTER(ctypes.c_uint),
                                         ctypes.c_bool]
        self.__pdll.st_batch.restype  = dot_h.st_return_t

    def __free(self):
        # print(self.__pdll)
        code = self.__pdll.st_free_context(self.__pcxt)
        if not self.__testing:
            sys.stdout.write(f'Freed context ({self.__pcxt:#x}) with code ({code}) from SolTrace DLL ({self.__pdll})\n')

    def reset(self):
        code = self.__pdll.st_reset_context(self.__pcxt)
        self.__check_return_code(code)
        if not self.__benchmarking:
            sys.stdout.write(f'Reset context ({self.__pcxt:#x})\n')


    def __check_return_code(self, code):
        if code > dot_h.st_return_code.SUCCESS and code < dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE:
            raise STAPIv2Exception(code, 
                                   _STC.ST_RETURN_CODE_NAME[code],
                                   _STC.ST_RETURN_CODE_ERROR_MSG[code] if code in _STC.ST_RETURN_CODE_ERROR_MSG else '')
        elif code >= dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE and code < dot_h.st_return_code.RETURN_COUNT:
            STAPIv2Warning(code,
                           _STC.ST_RETURN_CODE_NAME[code],
                           _STC.ST_RETURN_CODE_WARNING_MSG[code] if code in _STC.ST_RETURN_CODE_WARNING_MSG else '')
        elif code >= dot_h.st_return_code.RETURN_COUNT:
            raise STAPIv2Exception(code,  'UNKNOWN', 'Unknown return code received.')

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)
    def __message_cb(loc, msg):
        sys.stdout.write(f"{Fore.MAGENTA}[stapi_v2] - Message callback triggered by ({loc.decode('utf-8')}){Style.RESET_ALL}: {msg.decode('utf-8')}\n")
        return 0

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)
    def __testing_cb(loc, msg):
        # sys.stdout.write(f"{Fore.MAGENTA}[stapi_v2] - Message callback triggered by ({loc.decode('utf-8')}){Style.RESET_ALL}: {msg.decode('utf-8')}\n")
        return 0
    
    def sneak(self): return self.__pdll, self.__pcxt, self.__check_return_code

    """Python handles for st_ functions"""

    ##########################################
    # functions for SolTrace data management #
    ##########################################
    
    ##############################################################
    # functions for simulation data management thru json strings #
    ##############################################################
    
    def read_input_json(self, input_json: str | dict) -> None:
        # TODO: togglable validity check?
        if isinstance(input_json, str):
            f = open(input_json, mode='rb')
            code = self.__pdll.st_read_input_json(self.__pcxt, f.read())
            f.close()
        else:
            code = self.__pdll.st_read_input_json(self.__pcxt, orjson.dumps(input_json))
        self.__check_return_code(code)

    #####################################################
    # functions for simulation data management directly #
    #####################################################

    def set_simulation_parameters(self, params: _STC.args_simulation_parameters) -> None:
        code = self.__pdll.st_set_simulation_parameters(self.__pcxt, ctypes.pointer(params))
        self.__check_return_code(code)

    def sim_params(self,
                   raycount: int,
                   maxcount: int,
                   include_dynamic_group: bool) -> None:
        code = self.__pdll.st_sim_params(self.__pcxt, 
                                         raycount,
                                         maxcount,
                                         include_dynamic_group)
        self.__check_return_code(code)

    def sim_errors(self,
                   include_sun_shape: bool,
                   include_optics: bool) -> None:
        code = self.__pdll.st_sim_errors(self.__pcxt,
                                         include_sun_shape,
                                         include_optics)
        self.__check_return_code(code)

    def sim_location(self,
                        latitude: float,
                        longitude: float) -> None:
        code = self.__pdll.st_sim_location(self.__pcxt,
                                           latitude,
                                           longitude)
        self.__check_return_code(code)

    def sim_tolerance(self, tolerance: float) -> None:
        code = self.__pdll.st_sim_tolerance(self.__pcxt, tolerance)
        self.__check_return_code(code)

    def get_simulation_parameters(self) -> _STC.args_simulation_parameters:
        params = dot_h.args_simulation_parameters()
        code = self.__pdll.st_get_simulation_parameters(self.__pcxt, ctypes.pointer(params))
        self.__check_return_code(code)
        return params

    ##################################################
    # functions to add/remove/set optical properties #
    ##################################################

    def num_optics(self) -> int:
        num_optics = ctypes.c_uint64()
        code = self.__pdll.st_num_optics(self.__pcxt, ctypes.pointer(num_optics))
        self.__check_return_code(code)
        return num_optics.value
    
    def add_optical_properties_set(self,
                                   opt_set: _STC.args_optical_properties_set,
                                   front: _STC.args_optical_properties_face,
                                   back: _STC.args_optical_properties_face) -> int:
        num_optics = ctypes.c_uint64()
        code = self.__pdll.st_add_optical_properties_set(self.__pcxt,
                                                         ctypes.pointer(opt_set),
                                                         ctypes.pointer(front),
                                                         ctypes.pointer(back),
                                                         ctypes.pointer(num_optics))
        self.__check_return_code(code)
        return num_optics.value

    def get_optical_properties_set(self, optic_id: int) -> tuple[_STC.args_optical_properties_set, 
                                                                 _STC.args_optical_properties_face, 
                                                                 _STC.args_optical_properties_face]:
        opt_set = dot_h.args_optical_properties_set()
        front = dot_h.args_optical_properties_face()
        back = dot_h.args_optical_properties_face()
        code = self.__pdll.st_get_optical_properties_set(self.__pcxt,
                                                         optic_id,
                                                         ctypes.pointer(opt_set),
                                                         ctypes.pointer(front),
                                                         ctypes.pointer(back))
        self.__check_return_code(code)
        return opt_set, front, back

    def delete_optic(self, idx: int) -> None:
        code = self.__pdll.st_delete_optic(self.__pcxt, idx)
        self.__check_return_code(code)

    def clear_optics(self) -> None:
        code = self.__pdll.st_clear_optics(self.__pcxt)
        self.__check_return_code(code)

    ####################################
    # functions to add/remove elements #
    ####################################

    def num_elements(self) -> int:
        pcount = ctypes.c_uint64()
        code = self.__pdll.st_num_elements(self.__pcxt, ctypes.pointer(pcount))
        self.__check_return_code(code)
        return pcount.value

    def add_element(self,
                    args: _STC.args_element,
                    opt_id: int,
                    a_params: list[float],
                    s_params: list[float]) -> int:
        _a_params = (ctypes.c_double * 8)(*a_params)
        _s_params = (ctypes.c_double * 8)(*s_params)
        pid = ctypes.c_uint64()
        code = self.__pdll.st_add_element(self.__pcxt,
                                          ctypes.pointer(args),
                                          opt_id,
                                          _a_params,
                                          _s_params,
                                          ctypes.pointer(pid))
        self.__check_return_code(code)
        return pid.value

    def get_element(self, id: int) -> tuple[_STC.args_element, 
                                            int, 
                                            list[float],
                                            list[float]]:
            args = dot_h.args_element()
            optic_id = ctypes.c_int64()
            a_params = (ctypes.c_double * 8)(*[0 for _ in range(8)])
            s_params = (ctypes.c_double * 8)(*[0 for _ in range(8)])
            code = self.__pdll.st_get_element(self.__pcxt,
                                              id,
                                              ctypes.pointer(args),
                                              ctypes.pointer(optic_id),
                                              ctypes.pointer(a_params),
                                              ctypes.pointer(s_params))
            self.__check_return_code(code)
            return args, optic_id.value, a_params[:8], s_params[:8]
    
    def delete_element(self, idx: int) -> None:
        code = self.__pdll.st_delete_element(self.__pcxt, idx)
        self.__check_return_code(code)

    def clear_elements(self) -> None:
        code = self.__pdll.st_clear_elements(self.__pcxt)
        self.__check_return_code(code)

    ################################
    # functions to modify elements #
    ################################
    
    def element_enabled(self,
                        idx: int,
                        enabled_flag: bool) -> None:
        code = self.__pdll.st_element_enabled(self.__pcxt,
                                              idx,
                                              enabled_flag)
        self.__check_return_code(code)

    def element_virtual(self,
                        idx: int,
                        virtual_flag: bool) -> None:
        code = self.__pdll.st_element_virtual(self.__pcxt,
                                              idx,
                                              virtual_flag)
        self.__check_return_code(code)

    def element_xyz(self,
                    idx: int,
                    x: float,
                    y: float,
                    z: float) -> None:
        code = self.__pdll.st_element_xyz(self.__pcxt,
                                          idx,
                                          x,
                                          y,
                                          z)
        self.__check_return_code(code)

    def element_aim(self,
                    idx: int,
                    ax: float,
                    ay: float,
                    az: float) -> None:
        code = self.__pdll.st_element_aim(self.__pcxt,
                                          idx,
                                          ax,
                                          ay,
                                          az)
        self.__check_return_code(code)

    def element_zrot(self,
                     idx: int,
                     zrot: float) -> None:
        code = self.__pdll.st_element_zrot(self.__pcxt,
                                           idx,
                                           zrot)
        self.__check_return_code(code)

    def element_aperture(self,
                         idx: int,
                         ap: str,
                         params: list[float]) -> None:
        _params = (ctypes.c_double * 8)(*params)
        code = self.__pdll.st_element_aperture(self.__pcxt,
                                               idx,
                                               ap.encode(),
                                               _params)
        self.__check_return_code(code)

    def element_surface(self,
                        idx: int,
                        surf: str,
                        params: list[float]) -> None:
        _params = (ctypes.c_double * 8)(*params)
        code = self.__pdll.st_element_surface(self.__pcxt,
                                              idx,
                                              surf.encode(),
                                              _params)
        self.__check_return_code(code)

    def element_optic(self,
                      idx: int,
                      opt_id: int) -> None:
        code = self.__pdll.st_element_optic(self.__pcxt,
                                            idx,
                                            opt_id)
        self.__check_return_code(code)
    
    #################
    # sun functions #
    #################
    
    def add_sun(self,
                args: _STC.args_sun,
                angle: list[float] = [],
                intensity: list[float] = []) -> None:
        args.npoints = len(angle)
        _angle     = (ctypes.c_double * len(angle))(*angle)
        _intensity = (ctypes.c_double * len(angle))(*intensity)
        code = self.__pdll.st_add_sun(self.__pcxt,
                                      ctypes.pointer(args),
                                      _angle,
                                      _intensity)
        self.__check_return_code(code)

    def get_sun(self):
        args = dot_h.args_sun()
        angle = ctypes.c_double()
        intensity = ctypes.c_double()
        code = self.__pdll.st_get_sun(self.__pcxt,
                                       ctypes.pointer(args),
                                       ctypes.pointer(angle),
                                       ctypes.pointer(intensity))
        self.__check_return_code(code)
        return args, angle, intensity

    def sun_shape(self,
                shape: str,
                sigma_halfwidth_csr: float) -> None:
        code = self.__pdll.st_sun_shape(self.__pcxt,
                                      shape.encode(),
                                      sigma_halfwidth_csr)
        self.__check_return_code(code)

    def sun_xyz(self,
                x: float,
                y: float,
                z: float) -> None:
        code = self.__pdll.st_sun_xyz(self.__pcxt, x, y, z)
        self.__check_return_code(code)

    def sun_position(self,
                     lat: float,
                     day: float,
                     hour: float) -> Point:
        px = ctypes.c_double()
        py = ctypes.c_double()
        pz = ctypes.c_double()
        code = self.__pdll.st_sun_position(self.__pcxt,
                                           lat,
                                           day,
                                           hour,
                                           ctypes.pointer(px),
                                           ctypes.pointer(py),
                                           ctypes.pointer(pz))
        self.__check_return_code(code)
        return Point(px.value,
                     py.value,
                     pz.value)

    def sun_userdata(self,
                     npoints:   int,
                     angle:     list[float],
                     intensity: list[float]) -> None:
        _angle     = (ctypes.c_double * npoints)(*angle)
        _intensity = (ctypes.c_double * npoints)(*intensity)
        code = self.__pdll.st_sun_userdata(self.__pcxt,
                                           npoints,
                                           _angle,
                                           _intensity)
        self.__check_return_code(code)

    def get_sun_az_zen(self,
                       calc: int,
                       loc:  _STC.args_sun_location,
                       dt:   _STC.args_sun_datetime) -> tuple[float, float]:
        az  = ctypes.c_double()
        zen = ctypes.c_double()
        code = self.__pdll.st_get_sun_az_zen(self.__pcxt,
                                             calc, 
                                             ctypes.pointer(loc),
                                             ctypes.pointer(dt),
                                             ctypes.pointer(az),
                                             ctypes.pointer(zen))
        self.__check_return_code(code)

        return az.value, zen.value
        
    def get_sun_az_el(self,
                       calc: int,
                       loc:  _STC.args_sun_location,
                       dt:   _STC.args_sun_datetime) -> tuple[float, float]:
        az = ctypes.c_double()
        el = ctypes.c_double()
        code = self.__pdll.st_get_sun_az_el(self.__pcxt,
                                            calc, 
                                            ctypes.pointer(loc),
                                            ctypes.pointer(dt),
                                            ctypes.pointer(az),
                                            ctypes.pointer(el))
        self.__check_return_code(code)

        return az.value, el.value

    def get_sun_vector(self,
                       calc: int,
                       loc:  _STC.args_sun_location,
                       dt:   _STC.args_sun_datetime) -> Point:
        sun_x = ctypes.c_double()
        sun_y = ctypes.c_double()
        sun_z = ctypes.c_double()
        code = self.__pdll.st_get_sun_vector(self.__pcxt,
                                             calc, 
                                             ctypes.pointer(loc),
                                             ctypes.pointer(dt),
                                             ctypes.pointer(sun_x),
                                             ctypes.pointer(sun_y),
                                             ctypes.pointer(sun_z))
        self.__check_return_code(code)

        return Point(sun_x.value, sun_y.value, sun_z.value)
    
    ##################################################
    # functions for writing input files for SolTrace #
    ##################################################
    
    def export_json_file(self, filename: str):
        code = self.__pdll.st_export_json_file(self.__pcxt, filename.encode())
        self.__check_return_code(code)
    
    ############################################
    # functions for SolTrace runner management #
    ############################################

    def get_installed_runners(self) -> dict[str, bool]:
        installed = ctypes.c_ubyte()
        code = self.__pdll.st_get_installed_runners(self.__pcxt,
                                                    ctypes.pointer(installed))
        self.__check_return_code(code)
        return {
            dot_h.st_runner_type_t.NATIVE.name: installed.value & (1 << dot_h.st_runner_type_t.NATIVE.value),
            dot_h.st_runner_type_t.EMBREE.name: installed.value & (1 << dot_h.st_runner_type_t.EMBREE.value),
            dot_h.st_runner_type_t.OPTIX.name: installed.value & (1 << dot_h.st_runner_type_t.OPTIX.value),
        }

    def is_runner_installed(self, runner: int) -> bool:
        installed = ctypes.c_bool()
        code = self.__pdll.st_is_runner_installed(self.__pcxt,
                                                  runner,
                                                  ctypes.pointer(installed))
        self.__check_return_code(code)
        return installed.value

    def sim_setup(self,
                  runner_type: Literal[0, 1, 2],
                  num_threads: int = 8,
                  seeds: list = None) -> None:
        num_seeds = 0
        # redefine seeds from list to C array
        _seeds = None
        if seeds and len(seeds):
            num_seeds = len(seeds)
            _seeds = (ctypes.c_uint * num_seeds)(*seeds)
        code = self.__pdll.st_sim_setup(self.__pcxt,
                                        runner_type,
                                        num_threads,
                                        _seeds,
                                        num_seeds)
        self.__check_return_code(code)

    def sim_run_v2(self) -> None:
        code = self.__pdll.st_sim_run_v2(self.__pcxt)
        self.__check_return_code(code)

    def sim_report(self, level: int = 0) -> None:
        code = self.__pdll.st_sim_report(self.__pcxt, level)
        self.__check_return_code(code)

    #############################################
    # functions for SolTrace results management #
    #############################################

    def write_results_csv(self, filename: str, precision: int = 12) -> None:
        code = self.__pdll.st_write_results_csv(self.__pcxt, filename.encode(), precision)
        self.__check_return_code(code)

    #####################################
    # functions to get results directly #
    #####################################

    def num_intersections(self):
        pcount = ctypes.c_uint64()
        code = self.__pdll.st_num_intersections(self.__pcxt, ctypes.pointer(pcount))
        self.__check_return_code(code)
        return pcount.value
    
    def locations(self, n_intersections: int):
        loc_x = (ctypes.c_double * n_intersections)()
        loc_y = (ctypes.c_double * n_intersections)()
        loc_z = (ctypes.c_double * n_intersections)()
        code = self.__pdll.st_locations(self.__pcxt,
                                        loc_x,
                                        loc_y,
                                        loc_z)
        self.__check_return_code(code)
        return loc_x, loc_y, loc_z
    
    def cosines(self, n_intersections: int):
        coz_x = (ctypes.c_double * n_intersections)()
        coz_y = (ctypes.c_double * n_intersections)()
        coz_z = (ctypes.c_double * n_intersections)()
        code = self.__pdll.st_cosines(self.__pcxt,
                                      coz_x,
                                      coz_y,
                                      coz_z)
        self.__check_return_code(code)
        return coz_x, coz_y, coz_z
    
    def elementmap(self, n_intersections: int):
        element_map = (ctypes.c_uint64 * n_intersections)()
        code = self.__pdll.st_elementmap(self.__pcxt, element_map)
        self.__check_return_code(code)
        return element_map

    def stagemap(self, n_intersections: int):
        stage_map = (ctypes.c_uint64 * n_intersections)()
        code = self.__pdll.st_stagemap(self.__pcxt, stage_map)
        self.__check_return_code(code)
        return stage_map

    def raynumbers(self, n_intersections: int):
        ray_numbers = (ctypes.c_uint64 * n_intersections)()
        code = self.__pdll.st_raynumbers(self.__pcxt, ray_numbers)
        self.__check_return_code(code)
        return ray_numbers

    def sun_stats(self):
        width    = ctypes.c_double()
        height   = ctypes.c_double()
        area     = ctypes.c_double()
        nsunrays = ctypes.c_uint64()
        self.__batch_toggle(True, self.__pdll.st_sun_stats, dot_h.st_api_call.CALL_ST_SUN_STATS, 
                            (ctypes.pointer(width),
                             ctypes.pointer(height),
                             ctypes.pointer(area),
                             ctypes.pointer(nsunrays)))
        code = self.__pdll.st_sun_stats(self.__pcxt,
                                        ctypes.pointer(width),
                                        ctypes.pointer(height),
                                        ctypes.pointer(area),
                                        ctypes.pointer(nsunrays))
        self.__check_return_code(code)
        return width.value, height.value, area.value, nsunrays.value
    
    def get_results_data(self, n_intersections: int):
        loc_x = (ctypes.c_double * n_intersections)()
        loc_y = (ctypes.c_double * n_intersections)()
        loc_z = (ctypes.c_double * n_intersections)()
        coz_x = (ctypes.c_double * n_intersections)()
        coz_y = (ctypes.c_double * n_intersections)()
        coz_z = (ctypes.c_double * n_intersections)()
        element_map = (ctypes.c_uint64 * n_intersections)()
        stage_map   = (ctypes.c_uint64 * n_intersections)()
        ray_numbers = (ctypes.c_uint64 * n_intersections)()
        args = dot_h.args_results_data(loc_x,
                                       loc_y,
                                       loc_z,
                                       coz_x,
                                       coz_y,
                                       coz_z,
                                       element_map,
                                       stage_map,
                                       ray_numbers)
        code = self.__pdll.st_get_results_data(self.__pcxt, ctypes.pointer(args))
        self.__check_return_code(code)
        return args

    #####################
    # Batch caller work #
    #####################
    __default_f_return_func = lambda args: (arg.value if hasattr(arg, 'value') else arg for arg in args)
    __default_b_return_func = lambda args: args
    def __batch_toggle(self,
                       toggle:    bool,
                       st_func:   callable,
                       call_type: int,
                       args:      tuple,
                       f_return:  callable = __default_f_return_func,
                       b_return:  callable = __default_b_return_func):
        print(*f_return(args))
        print(*b_return(args))
            
        pass

    def generate_api_call(self, call_type: int, *args):
        if not call_type < dot_h.st_api_call.API_CALL_COUNT: raise ValueError(f'Invalid st_api_v2 batch call ({call_type}).')

        # _t = timer()

        # _t.ic('generate set up')
        rt = dot_h.st_api_call_args()
        rt.type = call_type
        args_name, args_cls = rt.payload._fields_[call_type]
        args_payload = getattr(rt.payload, args_name)
        # print(args_name)
        # print(args_cls)
        # print(dot_h.st_api_call_args.payload)
        # print(dot_h.st_api_call_args.payload.type._fields_)
        # test_name, test_cls = dot_h.st_api_call_args.payload.type._fields_[call_type]
        # print(test_name)
        # print(test_cls)

        # test = dot_h.st_api_call_args.payload.type(**{test_name: getattr(dot_h, test_cls.__name__)(*args)})
        # for f in test._fields_:
        #     print(getattr(test, f[0]))
        # temp = dot_h.st_api_call_args(test, call_type)
        # for f in temp._fields_:
        #     print(getattr(temp, f[0]))

        # get class that is actually intantiated in union memeber
        rt.payload = dot_h.st_api_call_args.payload.type(**{
            args_name: getattr(dot_h, args_cls.__name__)(*args)
        })
        # rt = dot_h.st_api_call_args(
        #     dot_h.st_api_call_args.payload.type(**{
        #         test_name: getattr(dot_h, test_cls.__name__)(*args)
        #     }),
        #     call_type
        # )

        # _t.oc('generate set up')
        # print('\ngenerate')
        # print(call_type)
        # if len(args) < len(args_cls._fields_):
        #     base_cls = getattr(dot_h, args_cls.__name__)
        #     # _t.ic('extend args')
        #     offset = len(base_cls._fields_) - len(base_cls._field_defaults_)
        #     _args = args + tuple(base_cls._field_defaults_.values())[(len(args) - offset):]
        #     # _t.oc('extend args')
        # else:
        #     _args = args
        # if not call_type == dot_h.st_api_call.CALL_ST_READ_INPUT_JSON:
        #     print(args_name)
        #     print(args_cls.__name__) #.rsplit('.', maxsplit=1)[1]
        #     print(getattr(dot_h, args_cls.__name__)._field_defaults_)
        #     offset = len(base_cls._fields_) - len(base_cls._field_defaults_)
        #     print(offset)
        #     temp = args + tuple(base_cls._field_defaults_.values())[(len(args) - offset):]
        #     print(temp)
        # print(args_cls)
        # print(args_payload)
        # print(args_payload._fields_)
        # print(args)z
        # args_payload = args_cls(*args)
        # print(args_payload)

        # args_payload.pcxt = self.__pcxt
        # _t.ic('setattr')
        # print(args_name, args)
        # for i, arg in enumerate(args):
        #     # if call_type == dot_h.st_api_call.CALL_ST_WRITE_RESULTS_CSV:
        #     #     print(i, arg, args_payload._fields_[i][0], args_payload._field_defaults_[i][0])
        #     setattr(args_payload, 
        #             args_payload._fields_[i][0],
        #             arg)
        # r = range(len(args), len(args_cls._fields_))
        # print(r)
        # if r:
        #     base_cls = getattr(dot_h, args_cls.__name__)
        #     print(len(args))
        #     print(len(base_cls._fields_))
        #     print(len(base_cls._field_defaults_))
        #     print(len(args) - (len(base_cls._fields_) - len(base_cls._field_defaults_)))
        #     temp = [*base_cls._field_defaults_.values()][(len(args) - (len(base_cls._fields_) - len(base_cls._field_defaults_))):]
        #     print(temp)
        #     for i in r:
        #         setattr(args_payload, 
        #                 base_cls._fields_[i][0],
        #                 temp[i - len(args)])
        # _t.oc('setattr')
        # args_payload = getattr(dot_h, args_cls.__name__)(*args)

        # print(f'\n{_t}')
        # if call_type == dot_h.st_api_call.CALL_ST_WRITE_RESULTS_CSV:
        #     print('\nres')
        #     test = getattr(dot_h, test_cls.__name__)(*args)
        #     print(test._field_defaults_)
        #     for field in getattr(rt.payload, test_name)._fields_:
        #         temp_payload_attr = getattr(rt.payload, test_name)
        #         print(getattr(temp_payload_attr, field[0]))
        #         print(getattr(test, field[0]))
        #     print()

        return rt #ctypes.cast(ctypes.byref(rt), ctypes.c_void_p) #_STC.st_api_pair(self.__func_map[call_type], rt)

    def dump_batch_args(self):
        for args in self.__stash_batch_args: print(args)

    ##################################
    # wrappers for generate_api_call #
    ##################################

    # functions for simulation data management directly
    
    # functions to add/remove/set optical properties
    
    # functions to add/remove elements
    
    # functions to modify elements
    
    # sun functions
    
    # functions for SolTrace runner management

    # functions for SolTrace results management


    # TODO: include version that calls functions from python for debugging STAPIv2.generate_api_call
    def batch(self, api_calls: list[_STC.st_api_call_args], verbose: bool = False):
        _t = timer()

        _t.ic('set up')
        num_calls = len(api_calls)
        self.__stash_batch_args = api_calls
        _t.oc('set up')


        _t.ic('c args set up')
        # TODO: don't need to cast as void because all are st_api_call_args
        # p_st_api_call_args = ctypes.POINTER(dot_h.st_api_call_args)
        # args_arr = (p_st_api_call_args * num_calls)(*[
        #     ctypes.cast(ctypes.b yref(c), p_st_api_call_args) for c in api_calls
        # ])
        # NOTE: might not actually help that much
        args_arr = (ctypes.c_void_p * num_calls)(*[
            ctypes.cast(ctypes.pointer(c), ctypes.c_void_p) for c in api_calls
        ])
        fail_iteration = ctypes.c_uint(0)
        _t.oc('c args set up')

        _t.ic('batch call')
        code = self.__pdll.st_batch(self.__pcxt,
                                    args_arr,
                                    num_calls,
                                    ctypes.pointer(fail_iteration),
                                    verbose)
        _t.oc('batch call')
        # print(f'\n{_t}')

        # TODO: raise new btach exception with fail_iteration
        self.__check_return_code(code)


if __name__ == "__main__":
    print(f'\n\n\n\n{found_in(dot_h)}\n\n\n\n')

    username = os.environ.get('USERNAME') # f'C:\\Users\\{username}\\build-soltrace\\soltrace\\coretrace\\stapi_v2\\RelWithDebInfo\\stapi_v2.dll'
    stapi = STAPIv2()
    print(stapi)

    for i in range(dot_h.st_runner_type_t.RUNNER_COUNT):
        print(i, stapi.is_runner_installed(i))

    # stapi.read_input_json('./sample.json')
    # stapi.sim_params(1000, 10000, False)
    # stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)
    # stapi.sim_run_v2()
    # stapi.sim_report()
    # n_intersections = stapi.num_intersections()
    # res = stapi.get_results_data(n_intersections)
    # print(len(list(res.loc_x)))
    # print(res.loc_x[:n_intersections])


    # stapi.read_input_json('./sample.json')
    # count = stapi.num_elements()
    # print(count)
    # stapi.sim_setup(dot_h.st_runner_type_t.OPTIX)
    # stapi.sim_run_v2()
    # stapi.sim_report()
    # stapi.write_results_csv('./sample.csv')


    # currently not building Embrre - emits warning
    # stapi.sim_setup(EMBREE)
    # raises STAPIv2Exception
    # stapi.sim_setup(NATIVE, 8, [608, 303])
