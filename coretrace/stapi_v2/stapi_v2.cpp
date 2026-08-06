#include <iostream>
#include "simulation_runner.hpp"
#include "native_runner.hpp"
#include "simulation_data_export.hpp"
#include "simulation_result_export.hpp"

#ifdef SOLTRACE_EMBREE_SUPPORT
#include "embree_runner.hpp"
#endif

#ifdef SOLTRACE_OPTIX_SUPPORT
#include "optix_runner.hpp"
#endif

#include "stapi_v2.h"

/* macros for fetching and casting pointers as SolTrace objects */
#define CONTEXT(p)                                                       \
    st_context *cxt = reinterpret_cast<st_context*>(p);                  \
    if (!cxt || cxt ==nullptr) return st_return_code::CONTEXT_NOT_FOUND;

#define DATA(cxt)                                                          \
    SimulationData *data = reinterpret_cast<SimulationData*>(cxt->p_data); \
    if (!data || data ==nullptr) return st_return_code::DATA_NOT_FOUND;

#define RUNNER(cxt)                                                                \
    SimulationRunner *runner = reinterpret_cast<SimulationRunner*>(cxt->p_runner); \
    if (!runner || runner ==nullptr) return st_return_code::RUNNER_NOT_FOUND;

#define RESULT(cxt)                                                                 \
    SimulationResult *result = reinterpret_cast<SimulationResult*>(cxt->p_results); \
    if (!result || result ==nullptr) return st_return_code::RESULT_NOT_FOUND;


// #define RUNNER(p, type) {\
//     CONTEXT(p); \
//     if (type == st_runner_type_t::ST_RUNNER_OPTIX) \
//         OptixRunner *runner = reinterpret_cast<OptixRunner*>(cxt->runner); \
//     else if (type == st_runner_type_t::ST_RUNNER_EMBREE) \
//         EmbreeRunner *runner = reinterpret_cast<EmbreeRunner*>(cxt->runner); \
//     else \
//         NativeRunner *runner = reinterpret_cast<NativeRunner*>(cxt->runner); \
// }

/* functions for SolTrace context management */
// STCORE_V2_API st_context_v2_t st_create_context(p_callback cb)
// {
// 	st_context* cxt = new st_context();
//     cxt->p_data = new SimulationData();
//     cxt->p_cb = cb;
//     return reinterpret_cast<st_context_v2_t>(cxt);
// }

STCORE_V2_API st_return_t st_create_context(st_context_v2_t* pcxt, p_callback cb)
{
    st_context* cxt = new st_context();
    cxt->p_data = new SimulationData();
    cxt->p_cb = cb;
    *pcxt = reinterpret_cast<st_context_v2_t>(cxt);
    return st_return_code::SUCCESS;
}

STCORE_V2_API st_return_t st_free_context(st_context_v2_t pcxt)
{
	CONTEXT(pcxt);
    // i think member class destructers will be called when cxt is deleted.

	// DATA(cxt);
	// RUNNER(cxt);
	// RESULT(cxt);
    // delete data;
    // delete runner;
    // delete result;
    delete cxt;
	return st_return_code::SUCCESS;
}

/* functions for SolTrace data management */
STCORE_V2_API st_return_t st_read_input_json(st_context_v2_t pcxt, const char *json)
{
	CONTEXT(pcxt);
    DATA(cxt);
    
    ST_WRAP_CB_TRY_CATCH(data->import_json_string(json), cxt->p_cb);
    return st_return_code::SUCCESS;
}

/* functions for SolTrace data information */
STCORE_V2_API st_return_t st_num_elements(st_context_v2_t pcxt, int *num_elements)
{
    CONTEXT(pcxt);
    DATA(cxt);

    *num_elements = data->get_number_of_elements();
    return st_return_code::SUCCESS;
}