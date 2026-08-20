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
import ctypes
c_number = ctypes.c_double
from colorama import just_fix_windows_console, Fore, Back, Style # pyright: ignore[reportMissingModuleSource]
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
    def __init__(self, stapi_v2_dll_path: str = '', testing: bool = False):
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
        code = self.__pdll.st_create_context(ctypes.byref(ppcxt), self.__message_cb if not testing else self.__testing_cb)
        self.__check_return_code(code)
        self.__pcxt = ppcxt.value
        # TODO: self._finalizer = weakref.finalize(self, __free) might be better option
        atexit.register(self.__free)

        # keep the struct instances alive — ctypes.cast() does NOT keep a
        # reference, so if these get garbage collected the void* becomes dangling
        self.__stash_batch_args = []

        self.__testing = testing

    def __repr__(self):
        rt = f'STAPIv2 Object at ({id(self.__pdll):#x})'
        rt += '\n' + '-' * len(rt)
        max_key_len = max(len(str(k)) for k in self.__pdll.__dict__.keys())
        for k, v in self.__pdll.__dict__.items():
            rt += f'\n{str(k):<{max_key_len}}: {v}'
            if (isinstance(v, ctypes._CFuncPtr)):
                # str(f"{id(v):#x}")
                rt += f'\n{" " * max_key_len}: {v.argtypes}'
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

        self.__pdll.st_sim_params.argtypes = self.__get_argtypes(dot_h.args_st_sim_params)
        self.__pdll.st_sim_params.restype  = dot_h.st_return_t

        self.__pdll.st_sim_errors.argtypes = self.__get_argtypes(dot_h.args_st_sim_errors)
        self.__pdll.st_sim_errors.restype  = dot_h.st_return_t
        
        ##################################################
        # functions to add/remove/set optical properties #
        ##################################################

        self.__pdll.st_num_optics.argtypes = self.__get_argtypes(dot_h.args_st_num_optics)
        self.__pdll.st_num_optics.restype  = dot_h.st_return_t

        self.__pdll.st_add_optical_properties_set.argtypes = self.__get_argtypes(dot_h.args_st_add_optical_properties_set)
        self.__pdll.st_add_optical_properties_set.restype  = dot_h.st_return_t

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

        ############################################
        # functions for SolTrace runner management #
        ############################################

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

        ############################################
        # function for batching SolTrace API calls #
        ############################################

        self.__api_func_ptr = ctypes.CFUNCTYPE(dot_h.st_return_t, ctypes.c_void_p)
        self.__pdll.st_batch.argtypes = [ctypes.c_void_p,
                                         ctypes.POINTER(ctypes.c_void_p),
                                         ctypes.c_uint,
                                         ctypes.POINTER(ctypes.c_uint),
                                         ctypes.c_bool]
        self.__pdll.st_batch.restype  = dot_h.st_return_t

    def __free(self):
        code = self.__pdll.st_free_context(self.__pcxt)
        if not self.__testing:
            sys.stdout.write(f'Freed context ({self.__pcxt:#x}) with code ({code}) from SolTrace DLL ({self.__pdll})\n')

    def __check_return_code(self, code):
        if code > dot_h.st_return_code.SUCCESS and code < dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE:
            raise STAPIv2Exception(code, 
                                   _STC.ST_RETURN_CODE_NAME[code],
                                   _STC.ST_RETURN_CODE_ERROR_MSG[code] if code in _STC.ST_RETURN_CODE_ERROR_MSG else '')
        elif code >= dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE:
            STAPIv2Warning(code,
                           _STC.ST_RETURN_CODE_NAME[code],
                           _STC.ST_RETURN_CODE_WARNING_MSG[code] if code in _STC.ST_RETURN_CODE_WARNING_MSG else '')

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)
    def __message_cb(loc, msg):
        sys.stdout.write(f"{Fore.MAGENTA}[stapi_v2] - Message callback triggered by ({loc.decode('utf-8')}){Style.RESET_ALL}: {msg.decode('utf-8')}\n")
        return 0

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)
    def __testing_cb(loc, msg):
        # sys.stdout.write(f"{Fore.MAGENTA}[stapi_v2] - Message callback triggered by ({loc.decode('utf-8')}){Style.RESET_ALL}: {msg.decode('utf-8')}\n")
        return 0
    
    def sneak(self): return self.__pdll, self.__pcxt

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

    def sim_params(self,
                   raycount: int,
                   maxcount: int,
                   include_dynamic_group: int) -> None:
        code = self.__pdll.st_sim_params(self.__pcxt, 
                                         raycount,
                                         maxcount,
                                         include_dynamic_group)
        self.__check_return_code(code)

    def sim_errors(self,
                   include_sun_shape: int,
                   include_optics: int) -> None:
        code = self.__pdll.st_delete_optic(self.__pcxt,
                                           include_sun_shape,
                                           include_optics)
        self.__check_return_code(code)

    ##################################################
    # functions to add/remove/set optical properties #
    ##################################################

    def num_optics(self) -> int:
        num_optics = ctypes.c_uint64()
        code = self.__pdll.st_num_optics(self.__pcxt, ctypes.byref(num_optics))
        self.__check_return_code(code)
        return num_optics.value
    
    def add_optical_properties_set(self,
                                   opt_set: _STC.args_optical_properties_set,
                                   front: _STC.args_optical_properties_face,
                                   back: _STC.args_optical_properties_face) -> int:
        num_optics = ctypes.c_uint64()
        code = self.__pdll.st_add_optical_properties_set(self.__pcxt,
                                                         ctypes.byref(opt_set),
                                                         ctypes.byref(front),
                                                         ctypes.byref(back),
                                                         ctypes.byref(num_optics))
        self.__check_return_code(code)
        return num_optics.value

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
        code = self.__pdll.st_num_elements(self.__pcxt, ctypes.byref(pcount))
        self.__check_return_code(code)
        return pcount.value

    def add_element(self,
                    args: _STC.args_element,
                    opt_id: int,
                    a_params: list[float],
                    s_params: list[float]) -> int:
        _a_params = (ctypes.c_double * 8)(*a_params)
        _s_params = (ctypes.c_double * 8)(*s_params)
        pcount = ctypes.c_uint64()
        code = self.__pdll.st_add_element(self.__pcxt,
                                          ctypes.byref(args),
                                          opt_id,
                                          _a_params,
                                          _s_params,
                                          ctypes.byref(pcount))
        self.__check_return_code(code)
        return pcount.value

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
                angle: list[float],
                intensity: list[float]) -> None:
        args.npoints = len(angle)
        _angle     = (ctypes.c_double * len(angle))(*angle)
        _intensity = (ctypes.c_double * len(angle))(*intensity)
        code = self.__pdll.st_add_sun(self.__pcxt,
                                      ctypes.byref(args),
                                      _angle,
                                      _intensity)
        self.__check_return_code(code)

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
                                           ctypes.byref(px),
                                           ctypes.byref(py),
                                           ctypes.byref(pz))
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

    ############################################
    # functions for SolTrace runner management #
    ############################################

    def sim_setup(self, 
                  runner_type: Literal[0, 1, 2], 
                  num_threads: int = 8, 
                  seeds: list = None) -> None:
        num_seeds = 0
        # redefine seeds from list to C array
        _seeds = None
        if seeds:
            num_seeds = len(seeds)
            _seeds = (ctypes.c_uint * num_seeds)(*seeds)
        code = self.__pdll.st_sim_setup(self.__pcxt, runner_type, num_threads, _seeds, num_seeds)
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
        if not call_type < dot_h.st_api_call.API_CALL_COUNT: raise ValueError(f'Invalid st_api_v2 batch call ({call_type}).')

        _t = timer()

        _t.ic('generate set up')
        # TODO: test -> rt = dot_h.st_api_call_args(args) 
        rt = dot_h.st_api_call_args()
        rt.type = call_type
        args_name, args_cls = rt.payload._fields_[call_type]
        args_payload = getattr(rt.payload, args_name)
        _t.oc('generate set up')
        # print('\ngenerate')
        # print(args_name)
        # print(args_cls)
        # print(args_payload)
        # print(args_payload._fields_)
        # print(args)
        # args_payload = args_cls(*args)

        # args_payload.pcxt = self.__pcxt
        _t.ic('setattr')

        for i, arg in enumerate(args):
            setattr(args_payload, 
                    args_payload._fields_[i][0],
                    arg)
        _t.oc('setattr')

        # print(f'\n{_t}')
            
        # print('\nres')
        # for field in args_payload._fields_:
        #     temp_payload_attr = getattr(rt.payload, args_name)
        #     print(getattr(temp_payload_attr, field[0]))
        # print()

        return rt #ctypes.cast(ctypes.byref(rt), ctypes.c_void_p) #_STC.st_api_pair(self.__func_map[call_type], rt)

    def dump_batch_args(self):
        for args in self.__stash_batch_args: print(args)

    # TODO: include version that calls functions from python for debugging STAPIv2.generate_api_call
    def batch(self, api_calls: list[_STC.st_api_call_args], verbose: bool = False):
        _t = timer()

        _t.ic('set up')
        num_calls = len(api_calls)
        self.__stash_batch_args = api_calls
        _t.oc('set up')


        _t.ic('c args set up')
        # TODO: don't need to cast as void because all are st_api_call_args
        args_arr = (ctypes.c_void_p * num_calls)(*[
            ctypes.cast(ctypes.byref(c), ctypes.c_void_p) for c in api_calls
        ])
        fail_iteration = ctypes.c_uint(0)
        _t.oc('c args set up')

        _t.ic('batch call')
        code = self.__pdll.st_batch(self.__pcxt,
                                    # func_arr,
                                    args_arr,
                                    num_calls,
                                    ctypes.byref(fail_iteration),
                                    verbose)
        _t.oc('batch call')
        # print(f'\n{_t}')

        # TODO: raise new btach exception with fail_iteration
        self.__check_return_code(code)


if __name__ == "__main__":
    print(f'\n\n\n\n{found_in(dot_h)}\n\n\n\n')

    username = os.environ.get('USERNAME') # f'C:\\Users\\{username}\\build-soltrace\\soltrace\\coretrace\\stapi_v2\\RelWithDebInfo\\stapi_v2.dll'
    stapi = STAPIv2()

    print(dot_h.args_optical_properties_set)
    test_opt_set = dot_h.args_optical_properties_set("test".encode('utf-8'), 1.1, 1.1, 0)
    test_front   = dot_h.args_optical_properties_face(.5, .5, 5, 5, 'g'.encode('utf-8'))
    test_back    = dot_h.args_optical_properties_face(.25, .25, 2, 2, 'g'.encode('utf-8'))

    print(test_opt_set)
    print(test_front)
    print(test_back)

    count = stapi.add_optical_properties_set(test_opt_set, test_front, test_back)
    print(count)

    print(stapi.num_optics())

    count = stapi.add_optical_properties_set(test_opt_set, test_front, test_back)
    print(count)

    print(stapi.num_optics())
    print("added elements")

    stapi.delete_optic(2)
    print(stapi.num_optics())
    stapi.delete_optic(1)
    print(stapi.num_optics())
    stapi.clear_optics()
    print(stapi.num_optics())

    # stapi.read_input_json('./sample.json')
    # count = stapi.num_elements()
    # print(count)
    # stapi.sim_setup(_STC.NATIVE)
    # stapi.sim_run_v2()
    # stapi.sim_report()
    # stapi.write_results_csv('./sample.csv')


    # currently not building Embrre - emits warning
    # stapi.sim_setup(EMBREE)
    # raises STAPIv2Exception
    # stapi.sim_setup(NATIVE, 8, [608, 303])
