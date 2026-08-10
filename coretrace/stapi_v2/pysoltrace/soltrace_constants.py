import ctypes
from dataclasses import dataclass

# TODO: maybe fetch enums from include/SolTrace/stapi_v2/stapi_v2.h?

#########################
# st_return_code set up #
#########################

# success code
SUCCESS                                      = 0
# error codes
FAILURE                                      = 1
CANCEL                                       = 2
CONTEXT_NOT_FOUND                            = 3
DATA_NOT_FOUND                               = 4
RUNNER_NOT_FOUND                             = 5
RESULT_NOT_FOUND                             = 6
RUNNER_INILIALIZE_FAILURE                    = 7
RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE = 8
RUNNER_SETUP_FAILURE                         = 9
RUNNER_NOT_READY                             = 10
RUNTIME_ERROR                                = 11
# warning codes
WARNING_FELLBACK_FROM_EMBREE                 = 12
WARNING_FELLBACK_FROM_OPTIX                  = 13
WARNING_ARGUMENT_IGNORED_BY_RUNNER           = 14
# sentinel (not a valid return type)
RETURN_COUNT                                 = 15 


ST_RETURN_CODE_NAME = {
    # success code
    SUCCESS:                                      'SUCCESS',
    # error codes
    FAILURE:                                      'FAILURE',
    CANCEL:                                       'CANCEL',
    CONTEXT_NOT_FOUND:                            'CONTEXT_NOT_FOUND',
    DATA_NOT_FOUND:                               'DATA_NOT_FOUND',
    RUNNER_NOT_FOUND:                             'RUNNER_NOT_FOUND',
    RESULT_NOT_FOUND:                             'RESULT_NOT_FOUND',
    RUNNER_INILIALIZE_FAILURE:                    'RUNNER_INILIALIZE_FAILURE',
    RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE: 'RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE',
    RUNNER_SETUP_FAILURE:                         'RUNNER_SETUP_FAILURE',
    RUNNER_NOT_READY:                             'RUNNER_NOT_READY',
    RUNTIME_ERROR:                                'RUNTIME_ERROR',
    # warning codes
    WARNING_FELLBACK_FROM_EMBREE:                 'WARNING_FELLBACK_FROM_EMBREE',
    WARNING_FELLBACK_FROM_OPTIX:                  'WARNING_FELLBACK_FROM_OPTIX',
    WARNING_ARGUMENT_IGNORED_BY_RUNNER:           'WARNING_ARGUMENT_IGNORED_BY_RUNNER',
}

# ST_RETURN_CODES = [
#     # success code
#     SUCCESS,
#     # error codes
#     FAILURE,
#     CANCEL,
#     CONTEXT_NOT_FOUND,
#     DATA_NOT_FOUND,
#     RUNNER_NOT_FOUND,
#     RESULT_NOT_FOUND,
#     RUNNER_INILIALIZE_FAILURE,
#     RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE,
#     RUNNER_SETUP_FAILURE,
#     RUNNER_NOT_READY,
#     RUNTIME_ERROR,
#     # warning codes
#     WARNING_FELLBACK_FROM_EMBREE,
#     WARNING_FELLBACK_FROM_OPTIX,
#     WARNING_ARGUMENT_IGNORED_BY_RUNNER
# ]

# messages for return codes
ST_RETURN_CODE_ERROR_MSG = {
    FAILURE:                                      '',
    CANCEL:                                       'Simulation canceled.',
    CONTEXT_NOT_FOUND:                            'Context pointer could not be cast as context.',
    DATA_NOT_FOUND:                               'SimulationData pointer could not be found in context.',
    RUNNER_NOT_FOUND:                             'SimulationRunner pointer could not be found in context.',
    RESULT_NOT_FOUND:                             'SimulationResult pointer could not be found in context.',
    RUNNER_INILIALIZE_FAILURE:                    'SimulationRunner could not be initialized.',
    RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE: 'Number of threads requested and length of seeds list are not equal. Include the number of seeds as threads requested.',
    RUNNER_SETUP_FAILURE:                         'SimulationRunner could not be set up based on SimulationData provided.',
    RUNNER_NOT_READY:                             'SimulationRunner is not ready for operation. Set up the SimulationRunner or run the simulation.',
    RUNTIME_ERROR:                                'RuntimeError raised. Check validity of JSON against SolTrace schema version used.',
}
ST_RETURN_CODE_WARNING_MSG = {
    WARNING_FELLBACK_FROM_EMBREE:       'Requested EmbreeRunner, but is not installed. Fellback to NativeRunner.',
    WARNING_FELLBACK_FROM_OPTIX:        'Requested OptixRunner, but is not installed. Fellback to NativeRunner.',
    WARNING_ARGUMENT_IGNORED_BY_RUNNER: 'Requested a number of threads for OptixRunner. The arguement does not apply to this runner type and was ignored.',
}

################
# runner types #
################
NATIVE = 0
OPTIX  = 1
EMBREE = 2
# sentinel (not a valid runner type)
RUNNER_COUNT = 3 

ST_RUNNER_NAME = {
    NATIVE: 'NATIVE',
    OPTIX:  'OPTIX',
    EMBREE: 'EMBREE',
}

# ST_RUNNER_TYPES = [NATIVE, OPTIX, EMBREE]

#######################
# batchable api calls #
#######################
ST_RETURN_T = ctypes.c_uint

CALL_ST_READ_INPUT_JSON = 0
CALL_ST_NUM_ELEMENTS    = 1
CALL_ST_SIM_SETUP       = 2
CALL_ST_SIM_RUN_V2      = 3
# sentinal (not valid api call code)
API_CALL_COUNT          = 4

ST_API_CALL_NAME = {
    CALL_ST_READ_INPUT_JSON: 'CALL_ST_READ_INPUT_JSON',
    CALL_ST_NUM_ELEMENTS:    'CALL_ST_NUM_ELEMENTS',
    CALL_ST_SIM_SETUP:       'CALL_ST_SIM_SETUP',
    CALL_ST_SIM_RUN_V2:      'CALL_ST_SIM_RUN_V2',
}

############################################
# function argument classes mirroring      #
# stucts named st_* (wildcard not pointer) # 
############################################

ST_CONTEXT_V2_T = ctypes.c_void_p  # typedef void* st_context_v2_t;

# classes mirroring structs with name args_st_*
class empty_args(ctypes.Structure):
    _fields_ = []

# simlulation data functions

class args_st_read_input_json(ctypes.Structure):
    _fields_ = [
        ('json', ctypes.c_char_p)
    ]

class args_st_num_elements(ctypes.Structure):
    _fields_ = [
        ('num_elements', ctypes.POINTER(ctypes.c_int))
    ]

# simlulation runner functions

class args_st_sim_setup(ctypes.Structure):
    _fields_ = [
        ('runner_type', ctypes.c_uint),
        ('num_threads', ctypes.c_uint64),
        ('seeds', ctypes.POINTER(ctypes.c_uint)),
        ('num_seeds', ctypes.c_size_t)
    ]

    def __init__(self, runner_type, num_threads = 8, seeds = None, num_seeds = 0):
        super().__init__(runner_type, num_threads, seeds, num_seeds)

class args_st_sim_run_v2(empty_args): pass

# simlulation results functions

print(empty_args)
print(empty_args._fields_)
print(args_st_read_input_json)
print(args_st_read_input_json._fields_)
print(args_st_num_elements)
print(args_st_num_elements._fields_)
print(args_st_sim_setup)
print(args_st_sim_setup._fields_)
print(args_st_sim_run_v2)
print(args_st_sim_run_v2._fields_)


#########################################
# classes for modeling st_api_call_args #
#########################################

# setting up st_api_call enum
_ST_API_CALL_T = ctypes.c_uint        # enum st_api_call : unsigned int

class _payload(ctypes.Union):
    _fields_ = [
        # simlulation data functions
        ('read_input_json_args', args_st_read_input_json),
        ('num_elements_args',    args_st_num_elements),
        # simlulation runner functions
        ('sim_setup_args',  args_st_sim_setup),
        ('sim_run_v2_args', args_st_sim_run_v2),
        # simlulation results functions
    ]

class st_api_call_args(ctypes.Structure):
    _fields_ = [
        ('type',    _ST_API_CALL_T),
        ('payload', _payload),
    ]

@dataclass
class st_api_pair():
    func: ctypes._CFuncPtr
    args: st_api_call_args

ST_API_CALL_ARGS = {
    CALL_ST_READ_INPUT_JSON: args_st_read_input_json,
    CALL_ST_NUM_ELEMENTS:    args_st_num_elements,
    CALL_ST_SIM_SETUP:       args_st_sim_setup,
    CALL_ST_SIM_RUN_V2:      args_st_num_elements,
}
