import ctypes
from typing import Literal

from pysoltrace import dot_h, soltrace_constants as _STC
from pysoltrace.api.utils import st_function
from pysoltrace.api.dll import context
from pysoltrace.api.utils import make_c_double_8

###########################################
# functions to add/remove/modify elements #
###########################################
class element(context):
    @st_function
    def num(self) -> int:
        num_elements = ctypes.c_uint64()
        code = self._pdll.st_num_elements(self._pcxt, 
                                        ctypes.byref(num_elements))
        return code, num_elements.value

    def __len__(self):
        if not self._pdll or not self._pcxt:
            return 0
        return self.num()
    # def num_elements(self) -> int:
    #     pcount = ctypes.c_uint64()
    #     code = self.__pdll.st_num_elements(self.__pcxt, ctypes.pointer(pcount))
    #     self.__check_return_code(code)
    #     return pcount.value

    # def add_element(self,
    #                 args: _STC.args_element,
    #                 opt_id: int,
    #                 a_params: list[float],
    #                 s_params: list[float]) -> int:
    #     _a_params = (ctypes.c_double * 8)(*a_params)
    #     _s_params = (ctypes.c_double * 8)(*s_params)
    #     pid = ctypes.c_uint64()
    #     code = self.__pdll.st_add_element(self.__pcxt,
    #                                       ctypes.pointer(args),
    #                                       opt_id,
    #                                       _a_params,
    #                                       _s_params,
    #                                       ctypes.pointer(pid))
    #     self.__check_return_code(code)
    #     return pid.value

    @st_function
    def add(self,
            args: _STC.args_element,
            opt_id: int,
            a_params: list[float],
            s_params: list[float]) -> int:
        _a_params = make_c_double_8(a_params)
        _s_params = make_c_double_8(s_params)
        pid = ctypes.c_uint64()
        code = self.__pdll.st_add_element(self.__pcxt,
                                                  ctypes.byref(args),
                                                  opt_id,
                                                  _a_params,
                                                  _s_params,
                                                  ctypes.byref(pid))
        return code, pid.value

    @st_function
    def get(self, id: int) -> tuple[_STC.args_element,
                                    int,
                                    list[float],
                                    list[float]]:
        args = dot_h.args_element()
        optic_id = ctypes.c_int64()
        a_params = make_c_double_8([0 for _ in range(8)])
        s_params = make_c_double_8([0 for _ in range(8)])
        code = self._pdll.st_get_element(self._pcxt,
                                        id,
                                        ctypes.byref(args),
                                        ctypes.byref(optic_id),
                                        ctypes.byref(a_params),
                                        ctypes.byref(s_params))
        return code, args.value, optic_id.value, a_params[:8], s_params[:8]
    
    # def get_element(self, id: int) -> tuple[_STC.args_element, 
    #                                         int, 
    #                                         list[float],
    #                                         list[float]]:
    #         args = dot_h.args_element()
    #         optic_id = ctypes.c_int64()
    #         a_params = (ctypes.c_double * 8)(*[0 for _ in range(8)])
    #         s_params = (ctypes.c_double * 8)(*[0 for _ in range(8)])
    #         code = self.__pdll.st_get_element(self.__pcxt,
    #                                           id,
    #                                           ctypes.pointer(args),
    #                                           ctypes.pointer(optic_id),
    #                                           ctypes.pointer(a_params),
    #                                           ctypes.pointer(s_params))
    #         self.__check_return_code(code)
    #         return args, optic_id.value, a_params[:8], s_params[:8]
    
    # def delete_element(self, idx: int) -> None:
    #     code = self.__pdll.st_delete_element(self.__pcxt, idx)
    #     self.__check_return_code(code)
        
    @st_function
    def delete(self, idx: int) -> None:
        return self._pdll.st_delete_element(self._pcxt, idx)

    @st_function
    def clear(self) -> None:
        return self._pdll.st_clear_elements(self._pcxt)

    # def clear_elements(self) -> None:
    #     code = self.__pdll.st_clear_elements(self.__pcxt)
    #     self.__check_return_code(code)

    
    ################################
    # functions to modify elements #
    ################################
    
    # def element_enabled(self,
    #                     idx: int,
    #                     enabled_flag: bool) -> None:
    #     code = self.__pdll.st_element_enabled(self.__pcxt,
    #                                           idx,
    #                                           enabled_flag)
    #     self.__check_return_code(code)

    @st_function
    def enabled(self, idx: int, enabled_flag: bool) -> None:
        return self._pdll.st_element_enabled(self._pcxt, idx, enabled_flag)

    # def element_virtual(self,
    #                     idx: int,
    #                     virtual_flag: bool) -> None:
    #     code = self.__pdll.st_element_virtual(self.__pcxt,
    #                                           idx,
    #                                           virtual_flag)
    #     self.__check_return_code(code)
    @st_function
    def virtual(self, idx: int, virtual_flag: bool) -> None:
        return self._pdll.st_element_virtual(self._pcxt, idx, virtual_flag)

    @st_function
    def xyz(self,
            idx: int,
            x: float, y: float, z: float) -> None:
        return self._pdll.st_element_xyz(self._pcxt, idx, x, y, z)

    # def element_xyz(self,
    #                 idx: int,
    #                 x: float,
    #                 y: float,
    #                 z: float) -> None:
    #     code = self.__pdll.st_element_xyz(self.__pcxt,
    #                                       idx,
    #                                       x,
    #                                       y,
    #                                       z)
    #     self.__check_return_code(code)

    # def element_aim(self,
    #                 idx: int,
    #                 ax: float,
    #                 ay: float,
    #                 az: float) -> None:
    #     code = self.__pdll.st_element_aim(self.__pcxt,
    #                                       idx,
    #                                       ax,
    #                                       ay,
    #                                       az)
    #     self.__check_return_code(code)

    @st_function
    def aim(self,
            idx: int, 
            ax: float, ay: float, az: float) -> None:
        return self._pdll.st_element_aim(self._pcxt, idx, ax, ay, az)

    @st_function
    def zrot(self, idx: int, zrot: float) -> None:
        return self._pdll.st_element_zrot(self._pcxt, idx, zrot)

    # def element_zrot(self,
    #                  idx: int,
    #                  zrot: float) -> None:
    #     code = self.__pdll.st_element_zrot(self.__pcxt,
    #                                        idx,
    #                                        zrot)
    #     self.__check_return_code(code)

    @st_function
    def aperture(self,
                 idx: int,
                 ap: bytes,
                 params: list[float]) -> None:
        assert isinstance(ap, bytes) and len(ap) == 1, \
            "Aperture type must be a single character byte string."
        
        _params = make_c_double_8(params)
        return self._pdll.st_element_aperture(self._pcxt, idx, ap, _params)

    # def element_aperture(self,
    #                      idx: int,
    #                      ap: str,
    #                      params: list[float]) -> None:
    #     _params = make_c_double_8(params)
    #     code = self.__pdll.st_element_aperture(self.__pcxt,
    #                                            idx,
    #                                            ap.encode(),
    #                                            _params)
    #     self.__check_return_code(code)

    # def element_surface(self,
    #                     idx: int,
    #                     surf: str,
    #                     params: list[float]) -> None:
    #     _params = make_c_double_8(params)
    #     code = self.__pdll.st_element_surface(self.__pcxt,
    #                                           idx,
    #                                           surf.encode(),
    #                                           _params)
    #     self.__check_return_code(code)

    @st_function
    def surface(self,
                idx: int,
                surf: bytes,
                params: list[float]) -> None:
        assert isinstance(surf, bytes) and len(surf) == 1, \
            "Surface type must be a single character byte string."

        _params = make_c_double_8(params)
        return self._pdll.st_element_surface(self._pcxt, idx, surf, _params)

    @st_function
    def optic(self, idx: int, opt_id: int) -> None:
        return self._pdll.st_element_optic(self._pcxt, idx, opt_id)

    # def element_optic(self,
    #                   idx: int,
    #                   opt_id: int) -> None:
    #     code = self.__pdll.st_element_optic(self.__pcxt,
    #                                         idx,
    #                                         opt_id)
    #     self.__check_return_code(code)