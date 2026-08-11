#include <iostream>
#include <vector>

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

    delete cxt->p_data;
    delete cxt->p_runner;
    delete cxt->p_results;

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

// functions for SolTrace data management
// functions to add/remove optical properties
STAPI_V2 st_return_t st_num_optics(st_context_v2_t pcxt, int *num_optics)
{
    CONTEXT(pcxt);
    DATA(cxt);

    *num_optics = data->get_number_of_optocal_property_sets();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_add_optic(st_context_v2_t pcxt, const char *name, int *num_optics)
{
    CONTEXT(pcxt);
    DATA(cxt);

    OpticalPropertySet opt(InteractionType::REFLECTION, std::string(name));
    OpticalPropertySetReference res = data->add_optical_property_set(opt);

    if (res.id < 0) return st_return_code::DATA_INSERTION_FAILURE;

    *num_optics = data->get_number_of_optocal_property_sets();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_delete_optic(st_context_v2_t pcxt, st_uint_t idx)
{
    return st_return_code::RETURN_COUNT;
}

STAPI_V2 st_return_t st_clear_optics(st_context_v2_t pcxt)
{
    return st_return_code::RETURN_COUNT;
}

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
							  double    	  *transs)
{
return st_return_code::RETURN_COUNT;
}

// sun functions
std::shared_ptr<Sun> get_or_create_sun(SimulationData *data)
{
    if (!data->get_number_of_ray_sources())
        data->add_ray_source(make_ray_source<Sun>());
    
    ray_source_ptr sun_ptr = data->get_ray_source(0);
    return std::dynamic_pointer_cast<Sun>(sun_ptr);
}

STAPI_V2 st_return_t st_sun(st_context_v2_t pcxt,
							int             point_source,
							char            shape, 
							double          sigma_halfwidth_csr)
{
    CONTEXT(pcxt);
    DATA(cxt);

    st_return_t code = st_return_code::SUCCESS; 
    SunShape sun_shape = SunShape::GAUSSIAN;

    switch (shape)
    {
        /* default to gaussian shape, 
           using default to add warning */
        case 'g':
        case 'G':
            // sun_shape = SunShape::GAUSSIAN;
            break;
        case 'p':
        case 'P':
            sun_shape = SunShape::PILLBOX;
            break;
        /* currently no set_limbdarkend_distribution
           function is implemented, so ignore and 
           emit warning
        case 'l':
        case 'L':
        {
            sun_shape = SunShape::LIMBDARKENED;
            break;
        }                                           */
        case 'b':
        case 'B':
            sun_shape = SunShape::BUIE_CSR;
            break;
        /* user defined sun shape goes thru same 
           Sun::set_shape, emit warning because not 
           enough information from this signiture, 
           maybe add defaults?                      
           case 'u':
           case 'U':                             */
    default:
        // warning code default to gaussian, default sigma = 4.65
        sun_shape = SunShape::GAUSSIAN;
        sigma_halfwidth_csr = 4.65;
        code = st_return_code::WARNING_SUN_SHAPE_IGNORED;
        break;
    }

    auto sun = get_or_create_sun(data);
    sun->set_shape(sun_shape, 
                    sigma_halfwidth_csr,
                    sigma_halfwidth_csr,
                    sigma_halfwidth_csr);
    return code;
}

STAPI_V2 st_return_t st_sun_xyz(st_context_v2_t pcxt,
								double          x,
								double          y,
								double          z)
{
    CONTEXT(pcxt);
    DATA(cxt);
    
    auto sun = get_or_create_sun(data);
    sun->set_position(x, y, z);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_sun_position(st_context_v2_t pcxt,
									 double          lat,
									 double          day,
									 double          hour,
									 double*         x,
									 double*         y,
									 double*         z)
{
    /* TODO: make st_sun_position_v2 that take a 
	computes the sun vector xyz given arguments
	lat : [deg] latitude 
	day : [] day of the year 
	hour : [hour] solar time. 12.00 corresponds to sun at maximum elevation and does not necessarily match local time

	xyz coordinate system:
		x: +west
		y: +zenith
		z: +north
	*/

	double Declination, HourAngle, Elevation, Azimuth;

	Declination = 180 / M_PI * asin(0.39795 * cos(0.98563 * M_PI / 180 * (day - 173)));
	HourAngle = 15 * (hour - 12);
	Elevation = 180 / M_PI * asin(sin(Declination * M_PI / 180) * sin(lat * M_PI / 180) + cos(Declination * M_PI / 180) * cos(HourAngle * M_PI / 180) * cos(lat * M_PI / 180));
	Azimuth = 180 / M_PI * acos((sin(M_PI / 180 * Declination) * cos(M_PI / 180 * lat) - cos(M_PI / 180 * Declination) * sin(M_PI / 180 * lat) * cos(M_PI / 180 * HourAngle)) / cos(M_PI / 180 * Elevation) + 0.0000000001);
	if (sin(HourAngle * M_PI / 180) > 0.0)
		Azimuth = 360 - Azimuth;
	*x = -sin(Azimuth * M_PI / 180) * cos(Elevation * M_PI / 180);
	*y = sin(Elevation * M_PI / 180);
	*z = cos(Azimuth * M_PI / 180) * cos(Elevation * M_PI / 180);

	return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_sun_userdata(st_context_v2_t pcxt,
									 st_uint_t 		 npoints,
									 double 		 angle[],
									 double 		 intensity[])
{
    CONTEXT(pcxt);
    DATA(cxt);

    std::vector<double> v_angle(angle, angle + npoints);
    std::vector<double> v_intensity(intensity, intensity + npoints);
    auto sun = get_or_create_sun(data);
    ST_WRAP_CB_TRY_CATCH(sun->set_shape(SunShape::USER_DEFINED,
                                        0, 0, 0,
                                        v_angle, 
                                        v_intensity),
                        cxt->p_cb);
    return st_return_code::SUCCESS;
}

// functions for simulation data management thru json strings
STAPI_V2 st_return_t st_read_input_json(st_context_v2_t pcxt, const char *json)
{
	CONTEXT(pcxt);
    DATA(cxt);
    
    ST_WRAP_CB_TRY_CATCH(data->import_json_string(json), cxt->p_cb);
    return st_return_code::SUCCESS;
}

// functions for SolTrace data information
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
								  st_uint_t 	   *seeds,
								  size_t		   num_seeds)
{
    CONTEXT(pcxt);
    DATA(cxt);

    delete cxt->p_runner;
    delete cxt->p_results;

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

            const std::vector<st_uint_t> temp_seeds(seeds, seeds + num_seeds);
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

/////////////////////////
// Batch api call work //
/////////////////////////

bool is_error(st_return_t code)
{
    return code > st_return_code::SUCCESS && code < st_return_code::WARNING_FELLBACK_FROM_EMBREE;
}

STAPI_V2 st_return_t st_batch(st_context_v2_t pcxt,
                              st_api_func_ptr* functions, 
							  void** arguments, 
							  st_uint_t num_calls,
                              st_uint_t* fail_iteration)
{
    CONTEXT(pcxt);

    st_return_t code = st_return_code::SUCCESS;
    
    // wrapping in try catch for runtime errors
    try {
        // for each pair of function and arguments, determine which function to call
        for (int i = 0; i < num_calls; ++i) {
            // cast the generic void* argument pointer back to its real type
            // so we can inspect the tag and reach the right payload
            st_api_call_args* call_args = (st_api_call_args*)arguments[i];
            
            if (cxt->p_cb) 
            {
                std::string msg = "batch call " + std::to_string(i);
                // TODO: magic_enum
                cxt->p_cb(msg.data(), std::to_string(call_args->type).c_str());
            }
            
            // based on the type of call, cast the generic function pointer
            // to the specific function pointer and signature.
            switch (call_args->type) {
        		// Simlulation Data Functions
                // sun functions
                case st_api_call::CALL_ST_SUN:
                {
                    // st_sun signature
                    // -> st_context_v2_t pcxt,
                    //    int    		  point_source,
                    //    char   		  shape, 
                    //    double 		  sigma_halfwidth_csr
                    st_return_t (*fn)(st_context_v2_t,
                                      int,
                                      char,
                                      double) = 
                        (st_return_t (*)(st_context_v2_t,
                                         int,
                                         char,
                                         double))functions[i];
                    code = fn(pcxt,
                              call_args->payload.sun_args.point_source,
                              call_args->payload.sun_args.shape,
                              call_args->payload.sun_args.sigma_halfwidth_csr);
                    break;
                }
                case st_api_call::CALL_ST_SUN_XYZ:
                {
                    // st_sun_xyz signature
                    // -> st_context_v2_t pcxt,
                    //    double 		  x,
                    //    double 		  y,
                    //    double 		  z
                    st_return_t (*fn)(st_context_v2_t,
                                      double,
                                      double,
                                      double) = 
                        (st_return_t (*)(st_context_v2_t,
                                         double,
                                         double,
                                         double))functions[i];
                    code = fn(pcxt,
                              call_args->payload.sun_xyz_args.x,
                              call_args->payload.sun_xyz_args.y,
                              call_args->payload.sun_xyz_args.z);
                    break;
                }
                case st_api_call::CALL_ST_SUN_POSITION:
                {
                    // st_sun_position signature
                    // -> st_context_v2_t pcxt,
                    //    double   		  lat,
                    //    double   		  day,
                    //    double   		  hour,
                    //    double*  		  x,
                    //    double*  		  y,
                    //    double*  		  z
                    st_return_t (*fn)(st_context_v2_t,
                                      double,
                                      double,
                                      double,
                                      double*,
                                      double*,
                                      double*) = 
                        (st_return_t (*)(st_context_v2_t,
                                         double,
                                         double,
                                         double,
                                         double*,
                                         double*,
                                         double*))functions[i];
                    code = fn(pcxt,
                              call_args->payload.sun_position_args.lat,
                              call_args->payload.sun_position_args.day,
                              call_args->payload.sun_position_args.hour,
                              call_args->payload.sun_position_args.x,
                              call_args->payload.sun_position_args.y,
                              call_args->payload.sun_position_args.z);
                    break;
                }
                case st_api_call::CALL_ST_SUN_USERDATA:
                {
                    // st_sun_userdata signature
                    // -> st_context_v2_t pcxt,
                    //    st_uint_t 	  npoints,
                    //    double 		  angle[],
                    //    double 		  intensity[]
                    st_return_t (*fn)(st_context_v2_t,
                                      st_uint_t,
                                      double[],
                                      double[]) =
                        (st_return_t (*)(st_context_v2_t,
                                      st_uint_t,
                                      double[],
                                      double[]))functions[i];
                    code = fn(pcxt,
                              call_args->payload.sun_userdata_args.npoints,
                              call_args->payload.sun_userdata_args.angle,
                              call_args->payload.sun_userdata_args.intensity);
                    break;
                }
        		// functions for simulation data management thru json strings
                case st_api_call::CALL_ST_READ_INPUT_JSON:
                {
                    // st_read_input_json signature
                    // -> st_context_v2_t pcxt, const char *json
                    st_return_t (*fn)(st_context_v2_t, const char *) = 
                        (st_return_t (*)(st_context_v2_t, const char *))functions[i];
                    code = fn(pcxt, call_args->payload.read_input_json_args.json);
                    break;
                }
                // functions for SolTrace data information
                case st_api_call::CALL_ST_NUM_ELEMENTS:
                {
                    // st_num_elements signature
                    // -> st_context_v2_t pcxt, int *num_elements
                    st_return_t (*fn)(st_context_v2_t, int *) =
                        (st_return_t (*)(st_context_v2_t, int *))functions[i];
                    code = fn(pcxt, call_args->payload.num_elements_args.num_elements);
                    break;
                }
                // Simlulation Runner Functions
                case st_api_call::CALL_ST_SIM_SETUP:
                {
                    // st_sim_setup
                    // -> st_context_v2_t  pcxt, 
					// 	  st_runner_type_t runner_type, 
					// 	  uint_fast64_t    num_threads,
					// 	  st_uint_t 	   *seeds,
					// 	  size_t		   num_seeds
                    st_return_t (*fn)(st_context_v2_t,
                                      st_runner_type_t,
                                      uint_fast64_t,
                                      st_uint_t *,
                                      size_t) =
                        (st_return_t (*)(st_context_v2_t,
                                      st_runner_type_t,
                                      uint_fast64_t,
                                      st_uint_t *,
                                      size_t))functions[i];
                    code = fn(pcxt, 
                              call_args->payload.sim_setup_args.runner_type,
                              call_args->payload.sim_setup_args.num_threads,
                              call_args->payload.sim_setup_args.seeds,
                              call_args->payload.sim_setup_args.num_seeds);
                    break;
                }
                case st_api_call::CALL_ST_SIM_RUN_V2:
                {
                    // st_sim_run_v2
                    // -> st_context_v2_t pcxt
                    st_return_t (*fn)(st_context_v2_t) =
                        (st_return_t (*)(st_context_v2_t))functions[i];
                    code = fn(pcxt);
                    break;
                }
                // Simlulation Results Functions
                default:
                    fprintf(stderr, "execute_calls: unknown call type at index %d\n", i);
                    break;
            }

            if (is_error(code))
            {
                *fail_iteration = i;
                break;
            }
        }
    } catch (const std::exception& e) {
        if (cxt->p_cb) cxt->p_cb("st_batch", e.what());
    }
    return code;
}
