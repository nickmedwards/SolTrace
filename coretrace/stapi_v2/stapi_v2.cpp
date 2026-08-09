#include <iostream>
#include "../simulation_runner/simulation_runner.hpp"
#include "../simulation_runner/native_runner/native_runner.hpp"
#include "../simulation_data/simulation_data_export.hpp"
#include "../simulation_results/simulation_result_export.hpp"

#ifdef STAPI_V2_EMBREE_SUPPORT
#include "../simulation_runner/embree_runner/embree_runner.hpp"
#endif

#ifdef STAPI_V2_OPTIX_SUPPORT
#include "../simulation_runner/optix_runner/optix_runner.hpp"
#endif

#include "stapi_v2.h"

/* macros for fetching pointers */
#define CONTEXT(p)                                                       \
    st_context *cxt = reinterpret_cast<st_context*>(p);                  \
    if (!cxt || cxt == nullptr) return st_return_code::CONTEXT_NOT_FOUND;

#define DATA(cxt)                                                       \
    SimulationData *data = cxt->p_data;                                 \
    if (!data || data == nullptr) return st_return_code::DATA_NOT_FOUND;

#define RUNNER(cxt)                                                           \
    SimulationRunner *runner = cxt->p_runner;                                 \
    if (!runner || runner == nullptr) return st_return_code::RUNNER_NOT_FOUND;

#define RESULT(cxt)                                                           \
    SimulationResult *result = cxt->p_results;                                \
    if (!result || result == nullptr) return st_return_code::RESULT_NOT_FOUND;

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

// TODO: renumber st_runner_type_t::NAME to 1 << idx
//       move ifdef stuff to a function that returns a sum based on enum 
//       call it get_built_runners() or something 
//       add another function to check if a runner is built 


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

    sts = runner->initialize();
    if (sts != RunnerStatus::SUCCESS) return st_return_code::RUNNER_INILIALIZE_FAILURE;

    /* optix doesn't use threads the way native/embree does, 
       and check if user requested optix but didn't build it,
       in either case, set the number of threads for the runner */
    if (!use_optix || rt == st_return_code::WARNING_FELLBACK_FROM_OPTIX)
    {
        NativeRunner *temp_native = reinterpret_cast<NativeRunner*>(runner);
        if (seeds != nullptr)
        {
            // ensures runtime_error won't be raised
            if (num_threads != num_seeds) return st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE;

            const std::vector<unsigned int> temp_seeds(seeds, seeds + num_seeds);
            temp_native->set_number_of_threads(num_threads, temp_seeds);
        }
        else
        {
            temp_native->set_number_of_threads(num_threads);
        }
        // by default disable stages
        temp_native->disable_stages();
    }
    // if using optix runner and requested threads, emit warning that it was ignored 
    else if (num_threads != DEFAULT_NUM_THREADS) rt = st_return_code::WARNING_ARGUMENT_IGNORED_BY_RUNNER;

    // auto t_setup_start = std::chrono::steady_clock::now();
    sts = runner->setup_simulation(data);
    // auto t_setup_end = std::chrono::steady_clock::now();
    if (sts != RunnerStatus::SUCCESS) return st_return_code::RUNNER_SETUP_FAILURE;
    
    cxt->runner_type = runner_type;
    cxt->p_runner = runner;

    return rt;
}

STAPI_V2 st_return_t st_sim_run_v2(st_context_v2_t pcxt)
{
    CONTEXT(pcxt);
    RUNNER(cxt);

    if (!runner->is_ready_to_run()) return st_return_code::RUNNER_NOT_READY;

    RunnerStatus sts = runner->run_simulation();

    if (sts == RunnerStatus::CANCEL) return st_return_code::CANCEL;
    else if (sts != RunnerStatus::SUCCESS) return st_return_code::FAILURE;
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_sim_report(st_context_v2_t pcxt, int level)
{
    CONTEXT(pcxt);
    RUNNER(cxt);

    if (!runner->is_ready_to_report()) return st_return_code::RUNNER_NOT_READY;

    cxt->p_results = new SimulationResult();
    RunnerStatus sts = runner->report_simulation(cxt->p_results, level);

    if (sts != RunnerStatus::SUCCESS) return st_return_code::FAILURE;
    return st_return_code::SUCCESS;
}

///////////////////////////////////
// Simlulation Results Functions //
///////////////////////////////////

STAPI_V2 st_return_t st_write_results_csv(st_context_v2_t pcxt, 
										  const char 	  *filename, 
										  int 			  precision)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    ST_WRAP_CB_TRY_CATCH(result->write_csv_file(filename, precision), cxt->p_cb);
    return st_return_code::SUCCESS;
}

// idea for batching function calls in a callbackable way for scripting
// /*
//  * call_dispatcher.cpp
//  *
//  * Demonstrates a generic call dispatcher:
//  *   - a list of function pointers to call
//  *   - a list of void* argument bundles to pass to those functions
//  *   - a count of how many calls to make
//  *
//  * Because the target functions have different signatures, each argument
//  * bundle is tagged with a CallType so the loop function knows how to cast
//  * the void* function pointer and void* argument pointer back to their real
//  * types. That casting happens inline, inside the function that contains
//  * the loop (execute_calls), not inside the target functions themselves.
//  *
//  * Compiled as C++ (so we get things like extern "C" linkage control),
//  * but the exported symbol is given C linkage so it can be called from
//  * plain C code / declared in a C header.
//  */

// #include <cstdio>

// extern "C" {

// /* ------------------------------------------------------------------ */
// /* Two example functions with different call signatures               */
// /* ------------------------------------------------------------------ */

// /* Signature A: (int, int) -> void */
// void add_and_print(int a, int b) {
//     printf("add_and_print: %d + %d = %d\n", a, b, a + b);
// }

// /* Signature B: (const char*, float) -> void */
// void greet_with_score(const char* name, float score) {
//     printf("greet_with_score: Hello %s, your score is %.2f\n", name, score);
// }

// /* ------------------------------------------------------------------ */
// /* Tag identifying which real signature/argument layout a call uses    */
// /* ------------------------------------------------------------------ */

// typedef enum {
//     CALL_ADD_AND_PRINT,
//     CALL_GREET_WITH_SCORE
// } CallType;

// /* Packed argument layouts — one per distinct function signature */
// typedef struct {
//     int a;
//     int b;
// } AddArgs;

// typedef struct {
//     const char* name;
//     float score;
// } GreetArgs;

// /* Every argument bundle passed through the generic arrays is one of
//  * these: a tag telling us which payload is active, plus the payload
//  * itself. This is what a void* in the "arguments" array actually
//  * points to. */
// typedef struct {
//     CallType type;
//     union {
//         AddArgs  add;
//         GreetArgs greet;
//     } payload;
// } CallArgs;

// /* Generic function pointer type used to store heterogeneous function
//  * pointers in the "functions" array. Each one gets cast back to its
//  * real signature right before it's invoked. */
// typedef void (*GenericFunc)(void);

// # C equivalent: int (*func_ptr)(int, int)
// MyFuncType = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_int)

// /* ------------------------------------------------------------------ */
// /* The function containing the loop.                                   */
// /*                                                                      */
// /* functions : array of function pointers (stored generically)         */
// /* arguments : array of void* pointers, each actually pointing at a     */
// /*             CallArgs struct                                         */
// /* count     : number of calls to make                                 */
// /*                                                                      */
// /* For each call, the void* function pointer and void* argument        */
// /* pointer are cast back to their real, concrete types right here,     */
// /* inside the loop, based on the CallType tag carried in CallArgs.     */
// /* ------------------------------------------------------------------ */
// void execute_calls(GenericFunc* functions, void** arguments, int count) {
//     for (int i = 0; i < count; ++i) {
//         /* cast the generic void* argument pointer back to its real type
//          * so we can inspect the tag and reach the right payload */
//         CallArgs* call_args = (CallArgs*)arguments[i];

//         switch (call_args->type) {
//             case CALL_ADD_AND_PRINT: {
//                 /* cast the generic function pointer back to signature A */
//                 void (*fn)(int, int) = (void (*)(int, int))functions[i];
//                 fn(call_args->payload.add.a, call_args->payload.add.b);
//                 break;
//             }
//             case CALL_GREET_WITH_SCORE: {
//                 /* cast the generic function pointer back to signature B */
//                 void (*fn)(const char*, float) =
//                     (void (*)(const char*, float))functions[i];
//                 fn(call_args->payload.greet.name, call_args->payload.greet.score);
//                 break;
//             }
//             default:
//                 fprintf(stderr, "execute_calls: unknown call type at index %d\n", i);
//                 break;
//         }
//     }
// }

// } /* extern "C" */

// /* ------------------------------------------------------------------ */
// /* Demonstration                                                       */
// /* ------------------------------------------------------------------ */
// #ifdef CALL_DISPATCHER_DEMO
// int main(void) {
//     /* Build the argument bundles */
//     CallArgs args1;
//     args1.type = CALL_ADD_AND_PRINT;
//     args1.payload.add.a = 3;
//     args1.payload.add.b = 4;

//     CallArgs args2;
//     args2.type = CALL_GREET_WITH_SCORE;
//     args2.payload.greet.name = "Ada";
//     args2.payload.greet.score = 97.5f;

//     CallArgs args3;
//     args3.type = CALL_ADD_AND_PRINT;
//     args3.payload.add.a = 10;
//     args3.payload.add.b = -2;

//     /* Build the parallel arrays */
//     GenericFunc functions[3] = {
//         (GenericFunc)add_and_print,
//         (GenericFunc)greet_with_score,
//         (GenericFunc)add_and_print
//     };

//     void* arguments[3] = { &args1, &args2, &args3 };

//     execute_calls(functions, arguments, 3);

//     return 0;
// }
// #endif