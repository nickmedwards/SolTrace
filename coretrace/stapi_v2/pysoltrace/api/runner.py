import ctypes
from typing import Literal

from pysoltrace import dot_h
from pysoltrace.api.utils import st_function

class runner:
    def __init__(self, pdll, pcxt):
        self.__pdll = pdll
        self.__pcxt = pcxt

    @st_function
    def get_installed(self) -> dict[str, bool]:
        installed = ctypes.c_ubyte()
        code = self.__pdll.st_get_installed_runners(self.__pcxt,
                                                    ctypes.pointer(installed))
        return code, {
            dot_h.st_runner_type_t.NATIVE.name: bool(installed.value & (1 << dot_h.st_runner_type_t.NATIVE.value)),
            dot_h.st_runner_type_t.EMBREE.name: bool(installed.value & (1 << dot_h.st_runner_type_t.EMBREE.value)),
            dot_h.st_runner_type_t.OPTIX.name:  bool(installed.value & (1 << dot_h.st_runner_type_t.OPTIX.value)),
        }
    
    @st_function
    def is_installed(self, runner: int) -> bool:
        installed = ctypes.c_bool()
        code = self.__pdll.st_is_runner_installed(self.__pcxt,
                                                    runner,
                                                    ctypes.pointer(installed))
        return code, installed.value

    @st_function
    def setup(self,
              runner_type: Literal[0, 1, 2],
              num_threads: int = 8,
              seeds:       list = None) -> None:
        num_seeds = 0
        # redefine seeds from list to C array
        _seeds = None
        if seeds and len(seeds):
            num_seeds = len(seeds)
            _seeds = (ctypes.c_uint * num_seeds)(*seeds)
        return self.__pdll.st_sim_setup(self.__pcxt,
                                        runner_type,
                                        num_threads,
                                        _seeds,
                                        num_seeds)

    @st_function
    def run(self) -> None:
        return self.__pdll.st_sim_run_v2(self.__pcxt)

    @st_function
    def report(self, level: int = 0) -> None:
        return self.__pdll.st_sim_report(self.__pcxt, level)