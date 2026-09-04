import ctypes
from typing import Literal

from pysoltrace import dot_h
from pysoltrace.api.utils import st_function

class legacy:
    def __init__(self, pdll, pcxt):
        self.__pdll = pdll
        self.__pcxt = pcxt

    @st_function    
    def sim_params(self,
                   raycount: int,
                   maxcount: int,
                   include_dynamic_group: bool) -> None:
        return self.__pdll.st_sim_params(self.__pcxt, 
                                         raycount,
                                         maxcount,
                                         include_dynamic_group)