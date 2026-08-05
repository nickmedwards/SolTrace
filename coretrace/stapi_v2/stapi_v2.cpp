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

#define CONTEXT(p)  st_context* cxt = reinterpret_cast<st_context*>(p);
#define DATA(cxt)   SimulationData *data = reinterpret_cast<SimulationData*>(cxt->p_data);
#define RUNNER(cxt) SimulationRunner *runner = reinterpret_cast<SimulationRunner*>(cxt->p_runner);
#define RESULT(cxt) SimulationResult *result = reinterpret_cast<SimulationResult*>(cxt->p_results);

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
STCORE_V2_API st_context_v2_t st_create_context(p_callback cb)
{
	st_context* cxt = new st_context();
    cxt->p_data = new SimulationData();
    cxt->p_cb = cb;
    return reinterpret_cast<st_context_v2_t>(cxt);
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
	return 0;
}

/* functions for SolTrace data management */
STCORE_V2_API st_return_t st_read_input_json(st_context_v2_t pcxt, const char *json)
{
	CONTEXT(pcxt);
    DATA(cxt);
    if (!data || data == nullptr) return 1;

    char * hard_code = "{\"schema_version\": \"2025.11.12\"}";

    // std::cout << json << std::endl;
    // std::cout << hard_code << std::endl;
    try {
        data->import_json_string(json);
    }
    catch (const std::runtime_error& e) {
        if (cxt->p_cb) cxt->p_cb("st_read_input_json", e.what());
        return 1;
    }
    return 0;
}

/* functions for SolTrace data information */
STCORE_V2_API int st_num_elements(st_context_v2_t pcxt)
{
    CONTEXT(pcxt);
    DATA(cxt);
    return data->get_number_of_elements();
}