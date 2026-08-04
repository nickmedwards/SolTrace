/*
STCORE_API: version 2
functions for interacting with new SimulationData/Runner/Results structure through json
*/

#ifndef __soltraceapi_v2_h
#define __soltraceapi_v2_h

#ifdef _STCORE_V2DLL_
	#ifdef STCORE_V2_API_EXPORTS
	#define STCORE_V2_API __declspec(dllexport)
	#else
	#define STCORE_V2_API __declspec(dllimport)
	#endif
#else
	#define STCORE_V2_API
#endif

#ifndef STCORE_V2_API
#define STCORE_V2_API
#endif

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

#ifdef __cplusplus
extern "C" {
#endif

using SolTrace::Runner::SimulationRunner;

typedef enum st_runner_type_t {
	ST_RUNNER_NATIVE = 0,       /* 0 */
	ST_RUNNER_OPTIX,            /* 1 */
	ST_RUNNER_EMBREE,			/* 2 */
	ST_RUNNER_COUNT             /* sentinel (not a valid runner) */
} st_runner_type_t;


typedef struct st_context {
	SimulationData*   p_data;
	SimulationRunner* p_runner;
	SimulationResult* p_results;
} st_context;

typedef void* st_context_v2_t;

/* functions for SolTrace context management */
STCORE_V2_API st_context_v2_t st_create_context();
STCORE_V2_API int st_free_context(st_context_v2_t pcxt);

/* functions for SolTrace data management */
STCORE_V2_API int st_read_input_json(st_context_v2_t pcxt, const char *json);

/* functions for SolTrace data information */
STCORE_V2_API int st_num_elements(st_context_v2_t pcxt);


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
