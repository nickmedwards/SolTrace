import ctypes, os, sys
from pysoltrace import dot_h

def __get_argtypes(args_struct: ctypes.Structure) -> list:
    return [dot_h.st_context_v2_t, *[args[1] for args in args_struct._fields_]]

def setup_dll(path: str = ''):
    if not os.path.exists(path):
        raise FileNotFoundError(f'Could not find DLL at {path}')

    if sys.platform == "win32":
        os.add_dll_directory(str(path).rsplit(os.sep, maxsplit=1)[0])
        pdll = ctypes.WinDLL(path, winmode=0)
    else: pdll = ctypes.CDLL(path)

    #############################################
    # functions for SolTrace context management #
    #############################################

    # warning that: "The function "POINTER" is deprecated ctypes.POINTER with string"
    # dot_h.st_context_v2_t is <class 'ctypes.c_void_p'> which is not deprecated
    # see ctypes entry for more information on the following Python docs page
    # here: https://docs.python.org/3/whatsnew/3.14.html#new-deprecations 
    pdll.st_create_context.argtypes = [ctypes.POINTER(dot_h.st_context_v2_t),
                                       ctypes.CFUNCTYPE(ctypes.c_int,
                                                        ctypes.c_char_p,
                                                        ctypes.c_char_p)]
    pdll.st_create_context.restype  = dot_h.st_return_t

    pdll.st_reset_context.argtypes = [ctypes.c_void_p]
    pdll.st_reset_context.restype  = dot_h.st_return_t

    pdll.st_free_context.argtypes = [ctypes.c_void_p]
    pdll.st_free_context.restype  = dot_h.st_return_t

    #########################################################
    # creates ctypes function pointers for each of the      #
    # structs defined in stapi_v2.h starting with "args_st" #
    # these functions do:                                   #
    # - SolTrace data management                            #
    #   - thru json strings                                 #
    #   - directly                                          #
    #     - set simulation parameters                       #
    #     - add/remove/set optical properties               #
    #     - add/remove/modify elements                      #
    #     - add/modify the sun                              #
    # - input files for SolTrace writing                    #
    # - SolTrace runner management                          #
    # - SolTrace results management                         #
    #   - thru writing files                                #
    #   - directly                                          #
    #########################################################
    for k, v in vars(dot_h).items():
        if k.startswith("args_st_"):
            func_name = k.replace("args_", "")
            func = getattr(pdll, func_name)
            func.argtypes = __get_argtypes(v)
            func.restype  = dot_h.st_return_t
        
    ############################################
    # function for batching SolTrace API calls #
    ############################################
    
    pdll.st_batch.argtypes = [ctypes.c_void_p,
                              ctypes.POINTER(ctypes.c_void_p),
                              ctypes.c_uint,
                              ctypes.POINTER(ctypes.c_uint),
                              ctypes.c_bool]
    pdll.st_batch.restype  = dot_h.st_return_t
    return pdll