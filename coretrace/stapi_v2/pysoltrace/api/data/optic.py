import ctypes
from typing import Literal

from pysoltrace import dot_h, soltrace_constants as _STC
from pysoltrace.api.utils import st_function
from pysoltrace.api.dll import context

##################################################
# functions to add/remove/set optical properties #
##################################################
class optic(context):
    @st_function
    def num(self) -> int:
        num_optics = ctypes.c_uint64()
        code = self._pdll.st_num_optics(self._pcxt, 
                                       ctypes.byref(num_optics))
        return code, num_optics.value

    def __len__(self):
        if not self._pdll or not self._pcxt:
            return 0
        return self.num()

    @st_function
    def add(self,
            opt_set: _STC.args_optical_properties_set,
            front:   _STC.args_optical_properties_face,
            back:    _STC.args_optical_properties_face) -> int:
        num_optics = ctypes.c_uint64()
        code = self._pdll.st_add_optical_properties_set(self._pcxt,
                                                       ctypes.byref(opt_set),
                                                       ctypes.byref(front),
                                                       ctypes.byref(back),
                                                       ctypes.byref(num_optics))
        return code, num_optics.value

    @st_function
    def get(self, optic_id: int) -> tuple[_STC.args_optical_properties_set, 
                                          _STC.args_optical_properties_face, 
                                          _STC.args_optical_properties_face]:
        opt_set = dot_h.args_optical_properties_set()
        front = dot_h.args_optical_properties_face()
        back = dot_h.args_optical_properties_face()
        code = self._pdll.st_get_optical_properties_set(self._pcxt,
                                                       optic_id,
                                                       ctypes.byref(opt_set),
                                                       ctypes.byref(front),
                                                       ctypes.byref(back))
        return code, opt_set.value, front.value, back.value

    @st_function
    def delete(self, idx: int) -> None:
        return self._pdll.st_delete_optic(self._pcxt, idx)

    @st_function
    def clear(self) -> None:
        return self._pdll.st_clear_optics(self._pcxt)
