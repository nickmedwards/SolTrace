import ctypes
from typing import Literal

from pysoltrace import dot_h
from pysoltrace.api.utils import st_function
from pysoltrace.api.dll import context
from pysoltrace.api.result.csv import csv

#############################################
# functions for SolTrace results management #
#############################################
class result(context):
    def __init__(self, pdll, pcxt):
        super().__init__(pdll, pcxt)
        self.csv = csv(pdll, pcxt)

    @st_function
    def num(self):
        pcount = ctypes.c_uint64()
        code = self._pdll.st_num_intersections(self._pcxt, 
                                               ctypes.byref(pcount))
        return code, pcount.value

    def __len__(self):
        if not self._pdll or not self._pcxt:
            return 0
        return self.num()

    @st_function    
    def locations(self, n: int):
        loc_x = (ctypes.c_double * n)()
        loc_y = (ctypes.c_double * n)()
        loc_z = (ctypes.c_double * n)()
        code = self._pdll.st_locations(self._pcxt,
                                       loc_x, loc_y, loc_z)
        return code, loc_x[:n], loc_y[:n], loc_z[:n]

    @st_function
    def cosines(self, n: int):
        coz_x = (ctypes.c_double * n)()
        coz_y = (ctypes.c_double * n)()
        coz_z = (ctypes.c_double * n)()
        code = self._pdll.st_cosines(self._pcxt,
                                     coz_x, coz_y, coz_z)
        return code, coz_x[:n], coz_y[:n], coz_z[:n]
    
    @st_function
    def elementmap(self, n: int):
        element_map = (ctypes.c_uint64 * n)()
        code = self._pdll.st_elementmap(self._pcxt, element_map)
        return code, element_map[:n]

    @st_function
    def stagemap(self, n: int):
        stage_map = (ctypes.c_uint64 * n)()
        code = self._pdll.st_stagemap(self._pcxt, stage_map)
        return code, stage_map[:n]

    @st_function
    def raynumbers(self, n: int):
        ray_numbers = (ctypes.c_uint64 * n)()
        code = self._pdll.st_raynumbers(self._pcxt, ray_numbers)
        return code, ray_numbers[:n]

    @st_function
    def sun_stats(self):
        width    = ctypes.c_double()
        height   = ctypes.c_double()
        area     = ctypes.c_double()
        nsunrays = ctypes.c_uint64()
        code = self._pdll.st_sun_stats(self._pcxt,
                                       ctypes.byref(width),
                                       ctypes.byref(height),
                                       ctypes.byref(area),
                                       ctypes.byref(nsunrays))
        return code, width.value, height.value, area.value, nsunrays.value

    @st_function
    def get(self, n: int):
        loc_x = (ctypes.c_double * n)()
        loc_y = (ctypes.c_double * n)()
        loc_z = (ctypes.c_double * n)()
        coz_x = (ctypes.c_double * n)()
        coz_y = (ctypes.c_double * n)()
        coz_z = (ctypes.c_double * n)()
        element_map = (ctypes.c_uint64 * n)()
        stage_map   = (ctypes.c_uint64 * n)()
        ray_numbers = (ctypes.c_uint64 * n)()
        args = dot_h.args_results_data(loc_x, loc_y, loc_z,
                                       coz_x, coz_y, coz_z,
                                       element_map,
                                       stage_map,
                                       ray_numbers)
        code = self._pdll.st_get_results_data(self._pcxt, ctypes.byref(args))
        return code, args.value

__all__ = ['result']