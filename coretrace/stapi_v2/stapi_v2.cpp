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

#define CONTEXT(p) st_context *cxt = reinterpret_cast<st_context_v2_t>(p);
#define RUNNER(p, type) {\
    CONTEXT(p); \
    if (type == st_runner_type_t::ST_RUNNER_OPTIX) \
        OptixRunner *runner = reinterpret_cast<OptixRunner*>(cxt->runner); \
    else if (type == st_runner_type_t::ST_RUNNER_EMBREE) \
        EmbreeRunner *runner = reinterpret_cast<EmbreeRunner*>(cxt->runner); \
    else \
        NativeRunner *runner = reinterpret_cast<NativeRunner*>(cxt->runner); \
}

STCORE_V2_API st_context_v2_t st_create_context()
{
	st_context_v2_t cxt = &st_context();
    cxt->p_data = &SimulationData();
    return cxt;
}
STCORE_V2_API int st_free_context(st_context_v2_t pcxt)
{
	CONTEXT(pcxt);
	delete cxt;
	return 1;
}