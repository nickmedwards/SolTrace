import ctypes
from typing import Literal

from pysoltrace import dot_h, soltrace_constants as _STC
from pysoltrace.api.utils import st_function

#####################################################
# functions for simulation data management directly #
#####################################################
class parameters:
    def __init__(self, pdll, pcxt):
        self.__pdll = pdll
        self.__pcxt = pcxt

    @st_function
    def set(self, params: _STC.args_simulation_parameters) -> None:
        return self.__pdll.st_set_simulation_parameters(self.__pcxt, ctypes.pointer(params))

    @st_function
    def rays(self,
             raycount: int,
             maxcount: int) -> None:
        return self.__pdll.st_sim_rays(self.__pcxt,
                                       raycount,
                                       maxcount)

    @st_function
    def power_tower(self,
                    is_power_tower: bool) -> None:
        return self.__pdll.st_sim_power_tower(self.__pcxt, is_power_tower)

    @st_function
    def errors(self,
               include_sun_shape: bool,
               include_optics: bool) -> None:
        return self.__pdll.st_sim_errors(self.__pcxt,
                                         include_sun_shape,
                                         include_optics)

    @st_function
    def location(self,
                 latitude: float,
                 longitude: float) -> None:
        return self.__pdll.st_sim_location(self.__pcxt,
                                           latitude,
                                           longitude)

    @st_function
    def tolerance(self, tolerance: float) -> None:
        return self.__pdll.st_sim_tolerance(self.__pcxt, tolerance)

    @st_function
    def get_simulation_parameters(self) -> _STC.args_simulation_parameters:
        params = _STC.args_simulation_parameters()
        code = self.__pdll.st_get_simulation_parameters(self.__pcxt,
                                                        ctypes.byref(params))
        return code, params.value
