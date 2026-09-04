import warnings
from colorama import just_fix_windows_console, Fore, Back, Style
just_fix_windows_console()

from pysoltrace import soltrace_constants as _STC
from pysoltrace import dot_h

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

def check_return_code(code):
    if code == dot_h.st_return_code.SUCCESS: return
    elif code > dot_h.st_return_code.SUCCESS and code < dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE:
        raise STAPIv2Exception(code, 
                                _STC.ST_RETURN_CODE_NAME[code],
                                _STC.ST_RETURN_CODE_ERROR_MSG[code] if code in _STC.ST_RETURN_CODE_ERROR_MSG else '')
    elif code >= dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE and code < dot_h.st_return_code.RETURN_COUNT:
        STAPIv2Warning(code,
                        _STC.ST_RETURN_CODE_NAME[code],
                        _STC.ST_RETURN_CODE_WARNING_MSG[code] if code in _STC.ST_RETURN_CODE_WARNING_MSG else '')
    elif code >= dot_h.st_return_code.RETURN_COUNT:
        raise STAPIv2Exception(code,  'UNKNOWN', 'Unknown return code received.')

def st_function(func):
    def wrapper(*args, **kwargs):
        code, *rt = func(*args, **kwargs)
        check_return_code(code)
        return rt[0] if len(rt) == 1 else tuple(rt) if len(rt) > 1 else None
    return wrapper