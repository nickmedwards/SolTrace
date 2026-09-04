import atexit, os, pathlib, sys, warnings, weakref
from typing import Literal
import orjson
import ctypes
from functools import partial
from colorama import just_fix_windows_console, Fore, Back, Style
just_fix_windows_console()

from pysoltrace.api.dll import context, setup_dll as _setup_dll
from pysoltrace import soltrace_constants as _STC
from pysoltrace.api.utils import check_return_code, st_function, STAPIv2Exception, STAPIv2Warning
from pysoltrace.api.runner import runner
from pysoltrace.api.data import data

def free(dll, pcxt, testing: bool = False):
    code = dll.st_free_context(pcxt)
    if not testing:
        sys.stdout.write(f'Freed context ({pcxt:#x}) with code ({code}) from SolTrace DLL ({dll})\n')

#############################################################################
# STAPIv2 Class: wraps stapi_v2.{dll, so, dylib} with more Python-ish calls #
#############################################################################
class STAPIv2:
    def __init__(self, override_path: str = '', testing: bool = False, benchmarking: bool = False):
        self.__pdll, self.__pcxt = self.__create(override_path, testing)

        atexit.register(free, self.__pdll, self.__pcxt, testing)

        self.data = data(self.__pdll, self.__pcxt)
        self.runner = runner(self.__pdll, self.__pcxt)

        # keep the struct instances alive — ctypes.cast() does NOT keep a
        # reference, so if these get garbage collected the void* becomes dangling
        self.__stash_batch_args = []

        self.__testing = testing
        self.__benchmarking = benchmarking

    def __repr__(self):
        rt = f'STAPIv2 Object at ({id(self.__pdll):#x})'
        rt += '\n' + '-' * len(rt) + '\n'

        runners = self.runner.get_installed()
        rt += f'Installed Runners: ' + ', '.join([k for k, v in runners.items() if v]) + '\n'
        max_key_len = max(len(str(k)) for k in self.__pdll.__dict__.keys())
        for k, v in self.__pdll.__dict__.items():
            rt += f'\n{str(k):<{max_key_len}}: {v}'
            if (isinstance(v, ctypes._CFuncPtr)):
                rt += f'\n{" " * max_key_len}: {[_STC._CTYPES_RE.search(str(arg)).group() for arg in v.argtypes]}'
        return rt

    @st_function
    def __create(self, override_path: str = '', testing: bool = False):
        if len(override_path): pdll = _setup_dll(override_path)
        else:
            _here = pathlib.Path(__file__).parent.parent.resolve()
            
            # 2. Determine the shared library filename based on the OS
            if sys.platform == "win32":
                _lib_name = "stapi_v2.dll"
            elif sys.platform == "darwin":
                _lib_name = "stapi_v2.dylib"
            else:
                _lib_name = "stapi_v2.so" # Note: CMake typically prepends "lib" on Linux/macOS
    
            _lib_path = _here / _lib_name
            pdll = _setup_dll(_lib_path)

        ppcxt = ctypes.c_void_p()
        code = pdll.st_create_context(ctypes.byref(ppcxt), self.__message_cb if not testing else self.__testing_cb)
        return code, pdll, ppcxt.value

    def reset(self):
        code = self.__pdll.st_reset_context(self.__pcxt)
        check_return_code(code)
        if not self.__benchmarking:
            sys.stdout.write(f'Reset context ({self.__pcxt:#x})\n')

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)
    def __message_cb(loc, msg):
        sys.stdout.write(f"{Fore.MAGENTA}[stapi_v2] - Message callback triggered by ({loc.decode('utf-8')}){Style.RESET_ALL}: {msg.decode('utf-8')}\n")
        return 0

    @ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_char_p, ctypes.c_char_p)
    def __testing_cb(loc, msg): return 0
    
    def sneak(self): return self.__pdll, self.__pcxt, check_return_code