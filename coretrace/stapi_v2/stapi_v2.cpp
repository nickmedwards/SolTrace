#include <iostream>
#include "simulation_runner.hpp"
#include "native_runner.hpp"
#include "simulation_data_export.hpp"
#include "simulation_result_export.hpp"

#ifdef STAPI_V2_EMBREE_SUPPORT
#include "embree_runner.hpp"
#endif

#ifdef STAPI_V2_OPTIX_SUPPORT
#include "optix_runner.hpp"
#endif

#include "stapi_v2.h"

// DEFAULT_NUM_THREADS = 8;

/* macros for fetching pointers */
#define CONTEXT(p)                                                       \
    st_context *cxt = reinterpret_cast<st_context*>(p);                  \
    if (!cxt || cxt ==nullptr) return st_return_code::CONTEXT_NOT_FOUND;

#define DATA(cxt)                                                      \
    SimulationData *data = cxt->p_data;                                \
    if (!data || data ==nullptr) return st_return_code::DATA_NOT_FOUND;

#define RUNNER(cxt)                                                          \
    SimulationRunner *runner = cxt->p_runner;                                \
    if (!runner || runner ==nullptr) return st_return_code::RUNNER_NOT_FOUND;

#define RESULT(cxt)                                                          \
    SimulationResult *result = cxt->p_results;                               \
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

////////////////////////////////
// SolTrace Context Functions //
////////////////////////////////

/* functions for SolTrace context management */
STAPI_V2 st_return_t st_create_context(st_context_v2_t* pcxt, p_callback cb)
{
    st_context* cxt = new st_context();
    cxt->p_data = new SimulationData();
    cxt->p_cb = cb;
    *pcxt = reinterpret_cast<st_context_v2_t>(cxt);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_free_context(st_context_v2_t pcxt)
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

////////////////////////////////
// Simlulation Data Functions //
////////////////////////////////

/* functions for SolTrace data management */
STAPI_V2 st_return_t st_read_input_json(st_context_v2_t pcxt, const char *json)
{
	CONTEXT(pcxt);
    DATA(cxt);
    
    ST_WRAP_CB_TRY_CATCH(data->import_json_string(json), cxt->p_cb);
    return st_return_code::SUCCESS;
}

/* functions for SolTrace data information */
STAPI_V2 st_return_t st_num_elements(st_context_v2_t pcxt, int *num_elements)
{
    CONTEXT(pcxt);
    DATA(cxt);

    *num_elements = data->get_number_of_elements();
    return st_return_code::SUCCESS;
}

//////////////////////////////////
// Simlulation Runner Functions //
//////////////////////////////////

/* functions for SolTrace runner management */
STAPI_V2 st_return_t st_sim_setup(st_context_v2_t  pcxt, 
								  st_runner_type_t runner_type, 
								  uint_fast64_t    num_threads,
								  unsigned int 	   *seeds,
								  size_t		   num_seeds)
{
    CONTEXT(pcxt);
    DATA(cxt);

    if (cxt->p_runner) delete cxt->p_runner;

    bool use_embree = runner_type == st_runner_type_t::EMBREE;
    bool use_optix = runner_type == st_runner_type_t::OPTIX;

    RunnerStatus sts;
    st_return_t  rt;
    rt = st_return_code::SUCCESS;
    SimulationRunner *runner;

 #ifdef STAPI_V2_EMBREE_SUPPORT
    if (use_embree)
    {
        runner = new SolTrace::EmbreeRunner::EmbreeRunner();
    }
    else
 #endif
 #ifdef STAPI_V2_OPTIX_SUPPORT
        if (use_optix)
    {
        runner = new OptixRunner();
    }
    else
#endif
    {
#ifndef STAPI_V2_EMBREE_SUPPORT
        if (use_embree) 
        {
            rt = st_return_code::WARNING_FELLBACK_FROM_EMBREE;
            runner_type = st_runner_type_t::NATIVE;
        }
#endif
#ifndef STAPI_V2_OPTIX_SUPPORT
        if (use_optix) 
        {
            rt = st_return_code::WARNING_FELLBACK_FROM_OPTIX;
            runner_type = st_runner_type_t::NATIVE;
        }
#endif
        runner = new NativeRunner();
    }

    sts = (*runner).initialize();
    if (sts != RunnerStatus::SUCCESS) rt = st_return_code::RUNNER_INILIALIZE_FAILURE;
    else
    {
        /* optix doesn't use threads the way native/embree does, 
        and check if user requested optix but didn't build it,
        in either case, set the number of threads for the runner */
        if (!use_optix || rt == st_return_code::WARNING_FELLBACK_FROM_OPTIX)
        {
            NativeRunner *temp_native = reinterpret_cast<NativeRunner*>(runner);
            if (seeds != nullptr)
            {
                // ensures runtime_error won't be raised
                if (num_threads != num_seeds) rt = st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE;
                else 
                {
                    const std::vector<unsigned int> temp_seeds(seeds, seeds + num_seeds);
                    (*temp_native).set_number_of_threads(num_threads, temp_seeds);
                }
            }
            else
            {
                (*temp_native).set_number_of_threads(num_threads);
            }
        }
        // if using optix runner and requested threads, emit warning that it was ignored 
        else if (num_threads != DEFAULT_NUM_THREADS) rt = st_return_code::WARNING_ARGUMENT_IGNORED_BY_RUNNER;
        
        if (rt != st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE)
        {
            // auto t_setup_start = std::chrono::steady_clock::now();
            sts = (*runner).setup_simulation(data);
            // auto t_setup_end = std::chrono::steady_clock::now();
            if (sts != RunnerStatus::SUCCESS) rt = st_return_code::RUNNER_SETUP_FAILURE;
            else
            {
                cxt->runner_type = runner_type;
                cxt->p_runner = runner;
            }
        }
    }

    return rt;
}

STAPI_V2 st_return_t st_sim_run_v2(st_context_v2_t pcxt)
{
    CONTEXT(pcxt);
    RUNNER(cxt);

    RunnerStatus sts = runner->run_simulation();

    if (sts == RunnerStatus::CANCEL) return st_return_code::CANCEL;
    else if (sts != RunnerStatus::SUCCESS) return st_return_code::FAILURE;
    return st_return_code::SUCCESS;
}