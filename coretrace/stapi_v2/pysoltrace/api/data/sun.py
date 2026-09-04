import ctypes
from typing import Literal

from pysoltrace import dot_h, Point, soltrace_constants as _STC
from pysoltrace.api.utils import st_function
from pysoltrace.api.dll import context

###################################
# functions to add/modify the sun #
###################################
class sun(context):
    # def add_sun(self,
    #             args: _STC.args_sun,
    #             angle: list[float] = [],
    #             intensity: list[float] = []) -> None:
    #     args.npoints = len(angle)
    #     _angle     = (ctypes.c_double * len(angle))(*angle)
    #     _intensity = (ctypes.c_double * len(angle))(*intensity)
    #     code = self.__pdll.st_add_sun(self.__pcxt,
    #                                   ctypes.pointer(args),
    #                                   _angle,
    #                                   _intensity)
    #     self.__check_return_code(code)

    @st_function
    def add(self,
            args: _STC.args_sun,
            angle: list[float] = [],
            intensity: list[float] = []) -> None:
        args.npoints = len(angle)
        _angle     = (ctypes.c_double * len(angle))(*angle)
        _intensity = (ctypes.c_double * len(angle))(*intensity)
        return self._pdll.st_add_sun(self._pcxt,
                                    ctypes.byref(args),
                                    _angle,
                                    _intensity)

    # def get_sun(self):
    #     args = dot_h.args_sun()
    #     angle = ctypes.c_double()
    #     intensity = ctypes.c_double()
    #     code = self.__pdll.st_get_sun(self.__pcxt,
    #                                    ctypes.pointer(args),
    #                                    ctypes.pointer(angle),
    #                                    ctypes.pointer(intensity))
    #     self.__check_return_code(code)
    #     return args, angle, intensity

    @st_function
    def get(self) -> tuple[_STC.args_sun, list[float], list[float]]:
        args = _STC.args_sun()
        angle = ctypes.c_double()
        intensity = ctypes.c_double()
        code = self._pdll.st_get_sun(self._pcxt,
                                    ctypes.byref(args),
                                    angle,
                                    intensity)
        return code, args.value, angle, intensity

    # def sun_shape(self,
    #             shape: str,
    #             sigma_halfwidth_csr: float) -> None:
    #     code = self.__pdll.st_sun_shape(self.__pcxt,
    #                                   shape.encode(),
    #                                   sigma_halfwidth_csr)
    #     self.__check_return_code(code)

    @st_function
    def shape(self,
              shape: bytes,
              sigma_halfwidth_csr: float) -> None:
        assert isinstance(shape, bytes) and len(shape) == 1, \
            "Sun shape type must be a single character byte string."
        return self._pdll.st_sun_shape(self._pcxt,
                                      shape,
                                      sigma_halfwidth_csr)
        
    # def sun_xyz(self,
    #             x: float,
    #             y: float,
    #             z: float) -> None:
    #     code = self.__pdll.st_sun_xyz(self.__pcxt, x, y, z)
    #     self.__check_return_code(code)

    @st_function
    def xyz(self, x: float, y: float, z: float) -> None:
        return self._pdll.st_sun_xyz(self._pcxt, x, y, z)

    # def sun_position(self,
    #                  lat: float,
    #                  day: float,
    #                  hour: float) -> Point:
    #     px = ctypes.c_double()
    #     py = ctypes.c_double()
    #     pz = ctypes.c_double()
    #     code = self.__pdll.st_sun_position(self.__pcxt,
    #                                        lat,
    #                                        day,
    #                                        hour,
    #                                        ctypes.pointer(px),
    #                                        ctypes.pointer(py),
    #                                        ctypes.pointer(pz))
    #     self.__check_return_code(code)
    #     return Point(px.value,
    #                  py.value,
    #                  pz.value)

    @st_function
    def position(self, lat: float, day: float, hour: float) -> Point:
        px = ctypes.c_double()
        py = ctypes.c_double()
        pz = ctypes.c_double()
        code = self.__pdll.st_sun_position(self.__pcxt,
                                           lat, day, hour,
                                           ctypes.byref(px),
                                           ctypes.byref(py),
                                           ctypes.byref(pz))
        return code, Point(px.value, py.value, pz.value)

    # def sun_userdata(self,
    #                  npoints:   int,
    #                  angle:     list[float],
    #                  intensity: list[float]) -> None:
    #     _angle     = (ctypes.c_double * npoints)(*angle)
    #     _intensity = (ctypes.c_double * npoints)(*intensity)
    #     code = self.__pdll.st_sun_userdata(self.__pcxt,
    #                                        npoints,
    #                                        _angle,
    #                                        _intensity)
    #     self.__check_return_code(code)

    @st_function
    def userdata(self,
                 npoints:   int,
                 angle:     list[float],
                 intensity: list[float]) -> None:
        assert len(angle) == npoints and len(intensity) == npoints, \
            f'Expected {npoints} angle and intensity values,' \
            f'got {len(angle)} and {len(intensity)}'
        _angle     = (ctypes.c_double * npoints)(*angle)
        _intensity = (ctypes.c_double * npoints)(*intensity)
        return self._pdll.st_sun_userdata(self._pcxt,
                                         npoints,
                                         _angle,
                                         _intensity)

    # def get_sun_az_zen(self,
    #                    calc: int,
    #                    loc:  _STC.args_sun_location,
    #                    dt:   _STC.args_sun_datetime) -> tuple[float, float]:
    #     az  = ctypes.c_double()
    #     zen = ctypes.c_double()
    #     code = self.__pdll.st_get_sun_az_zen(self.__pcxt,
    #                                          calc, 
    #                                          ctypes.pointer(loc),
    #                                          ctypes.pointer(dt),
    #                                          ctypes.pointer(az),
    #                                          ctypes.pointer(zen))
    #     self.__check_return_code(code)

    #     return az.value, zen.value

    @st_function
    def az_zen(self,
               calc: int,
               loc:  _STC.args_sun_location,
               dt:   _STC.args_sun_datetime) -> tuple[float, float]:
        az  = ctypes.c_double()
        zen = ctypes.c_double()
        code = self._pdll.st_get_sun_az_zen(self._pcxt,
                                           calc,
                                           ctypes.byref(loc),
                                           ctypes.byref(dt),
                                           ctypes.byref(az),
                                           ctypes.byref(zen))
        return code, az.value, zen.value

    # def get_sun_az_el(self,
    #                    calc: int,
    #                    loc:  _STC.args_sun_location,
    #                    dt:   _STC.args_sun_datetime) -> tuple[float, float]:
    #     az = ctypes.c_double()
    #     el = ctypes.c_double()
    #     code = self.__pdll.st_get_sun_az_el(self.__pcxt,
    #                                         calc, 
    #                                         ctypes.pointer(loc),
    #                                         ctypes.pointer(dt),
    #                                         ctypes.pointer(az),
    #                                         ctypes.pointer(el))
    #     self.__check_return_code(code)

    #     return az.value, el.value

    @st_function
    def az_el(self,
              calc: int,
              loc:  _STC.args_sun_location,
              dt:   _STC.args_sun_datetime) -> tuple[float, float]:
        az = ctypes.c_double()
        el = ctypes.c_double()
        code = self._pdll.st_get_sun_az_el(self._pcxt,
                                          calc,
                                          ctypes.byref(loc),
                                          ctypes.byref(dt),
                                          ctypes.byref(az),
                                          ctypes.byref(el))
        return code, az.value, el.value

    # def get_sun_vector(self,
    #                    calc: int,
    #                    loc:  _STC.args_sun_location,
    #                    dt:   _STC.args_sun_datetime) -> Point:
    #     sun_x = ctypes.c_double()
    #     sun_y = ctypes.c_double()
    #     sun_z = ctypes.c_double()
    #     code = self.__pdll.st_get_sun_vector(self.__pcxt,
    #                                          calc, 
    #                                          ctypes.pointer(loc),
    #                                          ctypes.pointer(dt),
    #                                          ctypes.pointer(sun_x),
    #                                          ctypes.pointer(sun_y),
    #                                          ctypes.pointer(sun_z))
    #     self.__check_return_code(code)

    #     return Point(sun_x.value, sun_y.value, sun_z.value)

    @st_function
    def vector(self,
               calc: int,
               loc:  _STC.args_sun_location,
               dt:   _STC.args_sun_datetime) -> Point:
        sun_x = ctypes.c_double()
        sun_y = ctypes.c_double()
        sun_z = ctypes.c_double()
        code = self._pdll.st_get_sun_vector(self._pcxt,
                                           calc,
                                           ctypes.byref(loc),
                                           ctypes.byref(dt),
                                           ctypes.byref(sun_x),
                                           ctypes.byref(sun_y),
                                           ctypes.byref(sun_z))
        return code, Point(sun_x.value, sun_y.value, sun_z.value)
