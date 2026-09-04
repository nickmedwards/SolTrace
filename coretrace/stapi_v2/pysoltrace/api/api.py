import atexit, os, pathlib, sys, warnings
from typing import Literal
import orjson
import ctypes
from colorama import just_fix_windows_console, Fore, Back, Style
just_fix_windows_console()

from pysoltrace.api.dll import setup_dll as _setup_dll
from pysoltrace import soltrace_constants as _STC

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
    def __init__(self, override_path: str = '', testing: bool = False, benchmarking: bool = False):
        if len(override_path): self.__pdll = _setup_dll(override_path)
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
            self.__pdll = _setup_dll(_lib_path)

        # ppcxt = ctypes.c_void_p()
        # code = self.__pdll.st_create_context(ctypes.pointer(ppcxt), self.__message_cb if not testing else self.__testing_cb)
        # self.__check_return_code(code)
        # self.__pcxt = ppcxt.value
        # # TODO: self._finalizer = weakref.finalize(self, __free) might be better option
        # atexit.register(self.__free)

        # # keep the struct instances alive — ctypes.cast() does NOT keep a
        # # reference, so if these get garbage collected the void* becomes dangling
        # self.__stash_batch_args = []

        # self.__testing = testing
        # self.__benchmarking = benchmarking

    def __repr__(self):
        rt = f'STAPIv2 Object at ({id(self.__pdll):#x})'
        rt += '\n' + '-' * len(rt) + '\n'

        # runners = self.get_installed_runners()
        # rt += f'Installed Runners: ' + ', '.join([k for k, v in runners.items() if v]) + '\n'
        max_key_len = max(len(str(k)) for k in self.__pdll.__dict__.keys())
        for k, v in self.__pdll.__dict__.items():
            rt += f'\n{str(k):<{max_key_len}}: {v}'
            if (isinstance(v, ctypes._CFuncPtr)):
                rt += f'\n{" " * max_key_len}: {[_STC._CTYPES_RE.search(str(arg)).group() for arg in v.argtypes]}'
        return rt