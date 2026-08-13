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

#ifdef __cplusplus
extern "C" {
#endif

#ifndef M_PI
	#define M_PI 3.141592653589793238462643
#endif


#define ST_WRAP_CB_TRY_CATCH(call, cb) 	  \
	try { (call); } 					  \
	catch (const std::exception& e) {     \
		if (cb) cb(#call, e.what()); 	  \
		return st_return_code::EXCEPTION; \
	} 									  \

using SolTrace::Runner::SimulationRunner;
using SolTrace::Runner::RunnerStatus;
using SolTrace::NativeRunner::NativeRunner;

typedef unsigned int st_uint_t;

/* changing return code convention from v1
   to be in line with industry convention.
   i.e. 0 for success, non-zero for failure. */
typedef st_uint_t st_return_t;

typedef enum st_return_code : st_return_t {
	SUCCESS = 0,
	FAILURE,
	CANCEL,
	CONTEXT_NOT_FOUND,
	DATA_NOT_FOUND,
	RUNNER_NOT_FOUND,
	RESULT_NOT_FOUND,
	DATA_INSERTION_FAILURE,
	RUNNER_INILIALIZE_FAILURE,
	RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE,
	RUNNER_SETUP_FAILURE,
	RUNNER_NOT_READY,
	EXCEPTION,
	UKNOWN_BATCH_API_CALL_FAILURE,

	WARNING_FELLBACK_FROM_EMBREE,
	WARNING_FELLBACK_FROM_OPTIX,
	WARNING_ARGUMENT_IGNORED_BY_RUNNER,
	WARNING_SUN_SHAPE_IGNORED,

	RETURN_COUNT /* sentinel (not a valid return type) */
} st_return_code;

#ifndef DEFAULT_NUM_THREADS
#define DEFAULT_NUM_THREADS 8
#endif

typedef enum st_runner_type_t : st_uint_t {
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

// functions for SolTrace context management
STAPI_V2 st_return_t st_create_context(st_context_v2_t* pcxt, p_callback cb = nullptr);
STAPI_V2 st_return_t st_free_context(st_context_v2_t pcxt);

////////////////////////////////
// Simlulation Data Functions //
////////////////////////////////

// functions for SolTrace data management
// functions to add/remove optical properties
STAPI_V2 st_return_t st_num_optics(st_context_v2_t pcxt);
STAPI_V2 st_return_t st_add_optic(st_context_v2_t pcxt, const char *name);
STAPI_V2 st_return_t st_delete_optic(st_context_v2_t pcxt, st_uint_t idx);
STAPI_V2 st_return_t st_clear_optics(st_context_v2_t pcxt);
STAPI_V2 st_return_t st_optic(st_context_v2_t pcxt,
							  st_uint_t 	  idx,
							  int       	  fb, /* 1=front,2=back */
							  char      	  dist,
							  int       	  optnum,
							  int       	  apgr,
							  int       	  order,
							  double    	  rreal,
							  double    	  rimag,
							  double    	  ref,
							  double    	  tra,
							  double    	  gratingab12[3],
							  double    	  rmsslope,
							  double    	  rmsspec,
							  int       	  userefltable,
							  int       	  refl_npoints,
							  double    	  *refl_angles,
							  double    	  *refls,
							  int       	  usetranstable,
							  int       	  trans_npoints,
							  double    	  *trans_angles,
							  double    	  *transs);


// sun functions
STAPI_V2 st_return_t st_sun(st_context_v2_t pcxt,
							int    			point_source,
							char   			shape, 
							double 			sigma_halfwidth_csr);
STAPI_V2 st_return_t st_sun_xyz(st_context_v2_t pcxt,
								double 			x,
								double 			y,
								double 			z);
STAPI_V2 st_return_t st_sun_position(st_context_v2_t pcxt,
									 double  		 lat,
									 double  		 day,
									 double  		 hour,
									 double* 		 x,
									 double* 		 y,
									 double* 		 z);
STAPI_V2 st_return_t st_sun_userdata(st_context_v2_t pcxt,
									 st_uint_t 		 npoints,
									 double 		 angle[],
									 double 		 intensity[]);

// functions for simulation data management thru json strings
STAPI_V2 st_return_t st_read_input_json(st_context_v2_t pcxt, const char *json);

// functions for SolTrace data information
STAPI_V2 st_return_t st_num_elements(st_context_v2_t pcxt, int *num_elements);

//////////////////////////////////
// Simlulation Runner Functions //
//////////////////////////////////

// functions for SolTrace runner management
STAPI_V2 st_return_t st_sim_setup(st_context_v2_t  pcxt, 
								  st_runner_type_t runner_type, 
								  uint_fast64_t    num_threads = DEFAULT_NUM_THREADS,
								  st_uint_t 	   *seeds = nullptr,
								  size_t		   num_seeds = 0);

STAPI_V2 st_return_t st_sim_run_v2(st_context_v2_t pcxt);

STAPI_V2 st_return_t st_sim_report(st_context_v2_t pcxt, int level);

///////////////////////////////////
// Simlulation Results Functions //
///////////////////////////////////

// TODO: add st_write_results_json once element_groups pr is merged
STAPI_V2 st_return_t st_write_results_csv(st_context_v2_t pcxt, 
										  const char 	  *filename, 
										  int 			  precision = 12);

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
	run    					  -> int st_sim_run_v2(st_context_v2_t pcxt, st_uint_t seed, int (*callback)(...), void *data);
	report 					  -> int st_sim_report(st_context_v2_t pcxt, int level);

- simulation results
	write csv  				  -> int st_write_results_csv(st_context_v2_t pcxt, const char *filename);
	write json 				  -> int st_write_results_json(st_context_v2_t pcxt, const char *filename);*/

///////////////////////
// Batch caller work //
///////////////////////

// enum defining all calls available to batch together
typedef enum st_api_call : st_uint_t {
	// Simlulation Data Functions
	// sun functions
	CALL_ST_SUN = 0,
	CALL_ST_SUN_XYZ,
	CALL_ST_SUN_POSITION,
	CALL_ST_SUN_USERDATA,
	// functions for simulation data management thru json strings
    CALL_ST_READ_INPUT_JSON,
	// functions for SolTrace data information
    CALL_ST_NUM_ELEMENTS,
	// Simlulation Runner Functions
	CALL_ST_SIM_SETUP,
	CALL_ST_SIM_RUN_V2,
	// Simlulation Results Functions

	API_CALL_COUNT			// sentinal
} st_api_call;

typedef struct empty_args {} empty_args;

// argument layouts — one per function signature

// Simlulation Data Functions

// sun functions
typedef struct args_st_sun {
	int    point_source;
	char   shape;
	double sigma_halfwidth_csr;
} args_st_sun;

typedef struct args_st_sun_xyz {
	double x;
	double y;
	double z;
} args_st_sun_xyz;

typedef struct args_st_sun_position {
	double  lat;
	double  day;
	double  hour;
	double* x;
	double* y;
	double* z;
} args_st_sun_position;

typedef struct args_st_sun_userdata {
	st_uint_t npoints;
	double*	  angle;
	double*	  intensity;
} args_st_sun_userdata;

// functions for simulation data management thru json strings
typedef struct args_st_read_input_json {
	const char *json;
} args_st_read_input_json;

// functions for SolTrace data information
typedef struct args_st_num_elements {
	int *num_elements;
} args_st_num_elements;

// Simlulation Runner Functions
typedef struct args_st_sim_setup {
	st_runner_type_t runner_type;
	uint_fast64_t    num_threads = DEFAULT_NUM_THREADS;
	st_uint_t 	 	 *seeds = nullptr;
	size_t		     num_seeds = 0;
} args_st_sim_setup;

typedef empty_args args_st_sim_run_v2;

// Simlulation Results Functions

/* Every argument layout passed through the generic arrays is one of
 * these: a tag telling us which payload is active, plus the payload
 * itself. This is what a void* in the "arguments" array actually
 * points to. */
typedef struct st_api_call_args {
    st_api_call type;
    union {
		// Simlulation Data Functions
		// sun functions
		args_st_sun 		 sun_args;
		args_st_sun_xyz 	 sun_xyz_args;
		args_st_sun_position sun_position_args;
		args_st_sun_userdata sun_userdata_args;
		// functions for simulation data management thru json strings
        args_st_read_input_json read_input_json_args;
		// functions for SolTrace data information
        args_st_num_elements 	num_elements_args;
		// Simlulation Runner Functions
		args_st_sim_setup		sim_setup_args;
		args_st_sim_run_v2		sim_run_v2_args;
		// Simlulation Results Functions
    } payload;
} st_api_call_args;

/* Generic function pointer type used to store heterogeneous function
 * pointers in the "functions" array. Each one gets cast back to its
 * real signature right before it's invoked. */
typedef st_return_t (*st_api_func_ptr)(void);

/* ------------------------------------------------------------------ */
/* The function containing the loop for batching stapi_v2 calls.      */
/*                                                                    */
/* functions : array of function pointers (stored generically)        */
/* arguments : array of void* pointers, each actually pointing at a   */
/*             st_api_call_args struct                                */
/* count     : number of calls to make                                */
/*                                                                    */
/* For each call, the void* function pointer and void* argument       */
/* pointer are cast back to their real, concrete types inside the 	  */
/* loop, based on the st_api_call tag carried in st_api_call_args.    */
/* Error codes break the loop, and warning codes are ignored.         */
/* ------------------------------------------------------------------ */
STAPI_V2 st_return_t st_batch(st_context_v2_t pcxt,
							  void** 	 	  arguments, 
							  st_uint_t  	  count,
                              st_uint_t* 	  fail_iteration,
                              bool 			  verbose);

#ifdef __cplusplus
} /* extern "C" */
#endif

#endif
