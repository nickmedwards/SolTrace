/*
STCORE_API: version 2
functions for interacting with new SimulationData/Runner/Results structure through json
*/

#ifndef __soltraceapi_v2_h
#define __soltraceapi_v2_h

#ifdef _STAPI_V2_DLL_
	#ifdef STAPI_V2_EXPORTS
	#define STAPI_V2 __declspec(dllexport)
	#else
	#define STAPI_V2 __declspec(dllimport)
	#endif
#else
	#define STAPI_V2
#endif

#ifndef STAPI_V2
#define STAPI_V2
#endif

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

#ifdef __cplusplus
extern "C" {
#endif

#define ST_WRAP_CB_TRY_CATCH(call, cb) 		      \
	if (!cb) (call); 						      \
	else { 									      \
		try { (call); } 					      \
		catch (const std::runtime_error& e) {     \
			cb(#call, e.what()); 			      \
			return st_return_code::RUNTIME_ERROR; \
		} 									      \
	}

using SolTrace::Runner::SimulationRunner;
using SolTrace::Runner::RunnerStatus;
using SolTrace::NativeRunner::NativeRunner;

/* changing return code convention from v1
   to be in line with industry convention.
   i.e. 0 for success, non-zero for failure. */
typedef unsigned int st_return_t;

enum st_return_code : st_return_t {
	SUCCESS = 0,
	FAILURE,
	CANCEL,
	CONTEXT_NOT_FOUND,
	DATA_NOT_FOUND,
	RUNNER_NOT_FOUND,
	RESULT_NOT_FOUND,
	RUNNER_INILIALIZE_FAILURE,
	RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE,
	RUNNER_SETUP_FAILURE,
	RUNNER_NOT_READY,
	RUNTIME_ERROR,

	WARNING_FELLBACK_FROM_EMBREE,
	WARNING_FELLBACK_FROM_OPTIX,
	WARNING_ARGUMENT_IGNORED_BY_RUNNER,

	RETURN_COUNT /* sentinel (not a valid return type) */
};

#ifndef DEFAULT_NUM_THREADS
#define DEFAULT_NUM_THREADS 8
#endif

typedef enum st_runner_type_t {
	NATIVE = 0,   /* 0 */
	OPTIX,        /* 1 */
	EMBREE,		  /* 2 */
	RUNNER_COUNT         /* sentinel (not a valid runner) */
} st_runner_type_t;

typedef int (*p_callback)(char* loc, const char* msg);

typedef struct st_context {
	SimulationData*   p_data;
	st_runner_type_t  runner_type;
	SimulationRunner* p_runner;
	SimulationResult* p_results;
	p_callback		  p_cb;
} st_context;

typedef void* st_context_v2_t;

////////////////////////////////
// SolTrace Context Functions //
////////////////////////////////

/* functions for SolTrace context management */
STAPI_V2 st_return_t st_create_context(st_context_v2_t* pcxt, p_callback cb = nullptr);
STAPI_V2 st_return_t st_free_context(st_context_v2_t pcxt);

////////////////////////////////
// Simlulation Data Functions //
////////////////////////////////

/* functions for SolTrace data management */
STAPI_V2 st_return_t st_read_input_json(st_context_v2_t pcxt, const char *json);

/* functions for SolTrace data information */
STAPI_V2 st_return_t st_num_elements(st_context_v2_t pcxt, int *num_elements);

//////////////////////////////////
// Simlulation Runner Functions //
//////////////////////////////////

/* functions for SolTrace runner management */
STAPI_V2 st_return_t st_sim_setup(st_context_v2_t  pcxt, 
								  st_runner_type_t runner_type, 
								  uint_fast64_t    num_threads = DEFAULT_NUM_THREADS,
								  unsigned int 	   *seeds = nullptr,
								  size_t		   num_seeds = 0);

STAPI_V2 st_return_t st_sim_run_v2(st_context_v2_t pcxt);

/*
create simualtion information -> st_context_v2_t st_create_context_v2();
free simualtion information   -> int st_free_context_v2(st_context_v2_t pcxt):

- simulation parameter setup
	set threads 			  -> int st_num_threads(st_context_v2_t pcxt, int n);
	set verbose 			  -> int st_verbose(st_context_v2_t pcxt, bool v);

- simlulation data set up
	read json 			      -> int st_read_input_json(st_context_v2_t pcxt, const char *json);

  - ray sources set up
	  add sun 			  	  -> int st_sun_v2(st_context_v2_t pcxt, const char *json);

  - optical property sets
	  add optical set  		  -> int st_add_optical_set(st_context_v2_t pcxt, const char *json);
	  add optical face 		  -> int st_add_optical_face(st_context_v2_t pcxt, const char *json);
  
  - no longer continuing support for stages
  
  - elements
	  add element  			  -> int st_add_element_v2(st_context_v2_t pcxt, const char *json);
	  add elements 			  -> int st_add_elements_v2(st_context_v2_t pcxt, const char *json);

- simulation runner
	setup  					  -> int st_sim_setup(st_context_v2_t pcxt, st_runner_type_t runner_type);
	run    					  -> int st_sim_run_v2(st_context_v2_t pcxt, unsigned int seed, int (*callback)(...), void *data);
	report 					  -> int st_sim_report(st_context_v2_t pcxt, int level);

- simulation results
	write csv  				  -> int st_write_results_csv(st_context_v2_t pcxt, const char *filename);
	write json 				  -> int st_write_results_json(st_context_v2_t pcxt, const char *filename);*/

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif
