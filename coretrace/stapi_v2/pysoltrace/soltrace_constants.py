import ctypes
from dataclasses import dataclass


# chedder finds constants defined in stapi_v2.h and exposes
# them as dot_h. soltrace_constants holds constant information
# for the Python side of SolTrace, i.e. names of enum values
# that aren't from IntEnums, error/warning messages, or types
# defined in stapi_v2.h that are used in type hinting.
try:
    from chedder import dot_h
except ImportError:
    from .chedder import dot_h

######################################
# st_return_code name/message set up #
######################################

ST_RETURN_CODE_NAME = { code: code.name for code in dot_h.st_return_code }

# messages for return codes
ST_RETURN_CODE_ERROR_MSG = {
    dot_h.st_return_code.FAILURE:                                      '',
    dot_h.st_return_code.CANCEL:                                       'Simulation canceled.',
    dot_h.st_return_code.CONTEXT_NOT_FOUND:                            'Context pointer could not be cast as context.',
    dot_h.st_return_code.DATA_NOT_FOUND:                               'SimulationData pointer could not be found in context.',
    dot_h.st_return_code.RUNNER_NOT_FOUND:                             'SimulationRunner pointer could not be found in context.',
    dot_h.st_return_code.RESULT_NOT_FOUND:                             'SimulationResult pointer could not be found in context.',
    dot_h.st_return_code.RUNNER_INILIALIZE_FAILURE:                    'SimulationRunner could not be initialized.',
    dot_h.st_return_code.RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE: 'Number of threads requested and length of seeds list are not equal. Include the number of seeds as threads requested.',
    dot_h.st_return_code.RUNNER_SETUP_FAILURE:                         'SimulationRunner could not be set up based on SimulationData provided.',
    dot_h.st_return_code.RUNNER_NOT_READY:                             'SimulationRunner is not ready for operation. Set up the SimulationRunner or run the simulation.',
    dot_h.st_return_code.EXCEPTION:                                    'Exception raised. Check validity of the arguments passed to the function called or of the JSON against SolTrace schema version used.',
}
ST_RETURN_CODE_WARNING_MSG = {
    dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE:       'Requested EmbreeRunner, but is not installed. Fellback to NativeRunner.',
    dot_h.st_return_code.WARNING_FELLBACK_FROM_OPTIX:        'Requested OptixRunner, but is not installed. Fellback to NativeRunner.',
    dot_h.st_return_code.WARNING_ARGUMENT_IGNORED_BY_RUNNER: 'Requested a number of threads for OptixRunner. The arguement does not apply to this runner type and was ignored.',
    dot_h.st_return_code.WARNING_NOT_FOUND:                  'Requested an item that was not found.',
}

# reexport structs in constants so it can be used in type hinting
class args_optical_properties_set(dot_h.args_optical_properties_set): pass
class args_optical_properties_face(dot_h.args_optical_properties_face): pass
class st_api_call_args(dot_h.st_api_call_args): pass

@dataclass
class st_api_pair():
    func: ctypes._CFuncPtr
    args: st_api_call_args
