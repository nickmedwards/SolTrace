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
// functions for simulation data management thru json strings
STAPI_V2 st_return_t st_read_input_json(st_context_v2_t pcxt, const char *json)
{
	CONTEXT(pcxt);
    DATA(cxt);
    
    ST_WRAP_CB_TRY_CATCH(data->import_json_string(json), cxt->p_cb);
    return st_return_code::SUCCESS;
}

// functions for simulation data management directly
STAPI_V2 st_return_t st_sim_params(st_context_v2_t pcxt,
								   int 			   raycount,
								   int 			   maxcount,
								   int 			   include_dynamic_group)
{
	CONTEXT(pcxt);
    DATA(cxt);

    SimulationParameters &sim_params = data->get_simulation_parameters();
    
    data->set_number_of_rays(raycount);
    data->set_max_rays_traced(maxcount);
    data->set_as_power_tower(include_dynamic_group);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_sim_errors(st_context_v2_t pcxt,
								   int 			   include_sun_shape,
								   int 			   include_optics)
{
	CONTEXT(pcxt);
    DATA(cxt);
    
    SimulationParameters &sim_params = data->get_simulation_parameters();
    data->set_include_sun_shape_errors((bool)include_sun_shape);
    data->set_include_optical_errors((bool)include_optics);
    return st_return_code::SUCCESS;
}

// functions to add/remove optical properties
STAPI_V2 st_return_t st_num_optics(st_context_v2_t pcxt, uint_fast64_t *num_optics)
{
    CONTEXT(pcxt);
    DATA(cxt);

    *num_optics = data->get_number_of_optocal_property_sets();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_add_optical_properties_set(st_context_v2_t 				pcxt, 
												   args_optical_properties_set 	*opt_set,
												   args_optical_properties_face *front, 
												   args_optical_properties_face *back, 
												   uint_fast64_t 				*num_optics)
{
    auto bad_type_char = [](char type) 
    {
        return type != 'g' && type != 'p' && type != 'f' && type != 'd';
    };

    if (bad_type_char(front->error_distribution_type) 
        || bad_type_char(back->error_distribution_type)) 
        return st_return_code::INVALID_ARGUMENTS;

    InteractionType inter_type = opt_set->type == 0 
                                 ? InteractionType::REFLECTION
                                 : InteractionType::REFRACTION;
    OpticalPropertySet opt(inter_type,
                           opt_set->refraction_index_front,
                           opt_set->refraction_index_back,
                           std::string(opt_set->name));
    
    opt.set_properties(OpticalSide::Front,
                       char_to_distribution(front->error_distribution_type),
                       front->transmissivity,
                       front->reflectivity,
                       front->slope_error,
                       front->specularity_error);

    opt.set_properties(OpticalSide::Back,
                       char_to_distribution(back->error_distribution_type),
                       back->transmissivity,
                       back->reflectivity,
                       back->slope_error,
                       back->specularity_error);
    
    CONTEXT(pcxt);
    DATA(cxt);
    OpticalPropertySetReference res = data->add_optical_property_set(opt);

    if (res.id < 0) return st_return_code::DATA_INSERTION_FAILURE;

    *num_optics = data->get_number_of_optocal_property_sets();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_delete_optic(st_context_v2_t pcxt, st_uint_t idx)
{
    CONTEXT(pcxt);
    DATA(cxt);

    int removed = data->remove_optical_property_set(idx);

    // only warn if requested to remove optical property set that doesn't exist
    return removed > 0 ? st_return_code::SUCCESS : st_return_code::WARNING_NOT_FOUND;
}

STAPI_V2 st_return_t st_clear_optics(st_context_v2_t pcxt)
{
    CONTEXT(pcxt);
    DATA(cxt);

    data->clear_optical_property_sets();
    return st_return_code::SUCCESS;
}

// functions to add/remove elements
STAPI_V2 st_return_t st_num_elements(st_context_v2_t pcxt, uint_fast64_t *num_elements)
{
    CONTEXT(pcxt);
    DATA(cxt);

    *num_elements = data->get_number_of_elements();
    return st_return_code::SUCCESS;
}

const OpticalPropertySetReference get_optics_ref_by_id(SimulationData *data, int_fast64_t opt_id)
{
    optical_set_ptr existing_set;
    for (auto it = data->get_optics_iterator(); !data->is_optics_at_end(it); ++it)
    {
        if (it->first == opt_id)
            existing_set = it->second;
    }

    if (!existing_set) {
        OpticalPropertySetReference ref;
        ref.id = SolTrace::Data::OPTICS_ID_TYPES::OPTICS_ID_UNASSIGNED;
        // ref.optical_property_set = nullptr;
        return ref;
    }

    return data->find_or_add_optical_property_set(*existing_set);
}

int32_t num_aperture_params(ApertureType type)
{
    int32_t rt = -1;
    
    switch (type)
    {
        case ApertureType::CIRCLE:
        case ApertureType::EQUILATERAL_TRIANGLE:
        case ApertureType::HEXAGON:
        {
            rt = 1;
            break;
        }
        case ApertureType::RECTANGLE:
        {
            rt = 2;
            break;
        }
        case ApertureType::ANNULUS:
        case ApertureType::SINGLE_AXIS_CURVATURE_SECTION:
        {
            rt = 3;
            break;
        }
        case ApertureType::IRREGULAR_TRIANGLE:
        {
            rt = 6;
            break;
        }
        case ApertureType::IRREGULAR_QUADRILATERAL:
        {
            rt = 8;
            break;
        }
        default:
            rt = -1;
            break;
        }
    return rt;
}

int32_t num_surface_params(SurfaceType type)
{
    int32_t rt = -1;

    switch (type)
    {
        case SurfaceType::FLAT:
        {
            rt = 0;
            break;
        }
        case SurfaceType::CONE:
        case SurfaceType::CYLINDER:
        case SurfaceType::SPHERE:
        {
            rt = 1;
            break;
        }
        case SurfaceType::PARABOLA:
        {
            rt = 2;
            break;
        }
        case SurfaceType::HYPER:
        case SurfaceType::GENERAL_SPENCER_MURTY:
        case SurfaceType::TORUS:
        default:
            rt = -1; // Not implemented yet
            break;
    }

    return rt;
}

STAPI_V2 st_return_t st_add_element(st_context_v2_t pcxt,
									args_element    *args,
									int_fast64_t    opt_id,
									double 		    a_params[8],
									double 		    s_params[8],
									uint_fast64_t   *num_elements)
{
    CONTEXT(pcxt);
    DATA(cxt);

    // check that inputs are good
    const OpticalPropertySetReference existing_set = get_optics_ref_by_id(data, opt_id);
    if (existing_set.id == SolTrace::Data::OPTICS_ID_TYPES::OPTICS_ID_UNASSIGNED)
        return st_return_code::DATA_VALUE_NOT_FOUND;

    ApertureType a_type = char_to_aperture(args->ap);
    SurfaceType s_type = char_to_surface(args->surf);
    int32_t num_a_params = num_aperture_params(a_type);
    int32_t num_s_params = num_surface_params(s_type);
    if (num_a_params < 0 || num_s_params < 0) return st_return_code::INVALID_ARGUMENTS;

    std::vector<double> _a_params(a_params, a_params + num_a_params);
    std::vector<double> _s_params(s_params, s_params + num_s_params);
    aperture_ptr ap;
    surface_ptr surf;
    try
    {
        ap = Aperture::make_aperture_from_type(a_type, _a_params);
        surf = SolTrace::Data::make_surface_from_type(s_type, _s_params);
    }
    catch (const std::invalid_argument& e)
    {
        if (cxt->p_cb) cxt->p_cb("geometry creation", e.what());
        return st_return_code::INVALID_ARGUMENTS;
    }

    element_ptr el = make_element<SingleElement>();
    
    el->set_origin(args->x, args->y, args->z);
    el->set_aim_vector(args->ax, args->ay, args->az);
    el->set_zrot(args->zrot);
    if (args->enabled_flag) el->enable();
    else                    el->disable();
    if (args->virtual_flag) el->mark_virtual();
    else                    el->unmark_virtual();
    
    el->set_optical_property_set(existing_set);
    el->set_aperture(ap);
    el->set_surface(surf);
    // TODO in simulation_data.cpp saying add_element will be throwable in the future
    ST_WRAP_CB_TRY_CATCH(data->add_element(el), cxt->p_cb);

    *num_elements = data->get_number_of_elements();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_delete_element(st_context_v2_t pcxt, st_uint_t idx)
{
    CONTEXT(pcxt);
    DATA(cxt);

    uint_fast64_t removed = data->remove_element(idx);

    if (removed == 0) return st_return_code::WARNING_NOT_FOUND;
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_clear_elements(st_context_v2_t pcxt)
{
    CONTEXT(pcxt);
    DATA(cxt);

    data->clear_elements();
    return st_return_code::SUCCESS;
}

// functions to modify elements
STAPI_V2 st_return_t st_element_enabled(st_context_v2_t pcxt,
										st_uint_t 		idx,
										bool 			enabled_flag)
{
    CONTEXT(pcxt);
    DATA(cxt);
    
    element_ptr el = data->get_element(idx);
    if (!el) return st_return_code::WARNING_NOT_FOUND;

    if (enabled_flag) el->enable();
    else              el->disable();

    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_element_virtual(st_context_v2_t pcxt,
										st_uint_t 		idx,
										bool 			virtual_flag)
{
    CONTEXT(pcxt);
    DATA(cxt);
    
    element_ptr el = data->get_element(idx);
    if (!el) return st_return_code::WARNING_NOT_FOUND;

    if (virtual_flag) el->mark_virtual();
    else              el->unmark_virtual();

    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_element_xyz(st_context_v2_t pcxt, 
									st_uint_t 		idx,
									double 	  		x,
									double 	  		y,
									double 	  		z)
{
    CONTEXT(pcxt);
    DATA(cxt);

    element_ptr el = data->get_element(idx);
    if (!el) return st_return_code::WARNING_NOT_FOUND;

    el->set_origin(x, y, z);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_element_aim(st_context_v2_t pcxt, 
									st_uint_t 		idx,
									double 	  		ax,
									double 	  		ay,
									double 	  		az)
{
    CONTEXT(pcxt);
    DATA(cxt);
    
    element_ptr el = data->get_element(idx);
    if (!el) return st_return_code::WARNING_NOT_FOUND;

    el->set_aim_vector(ax, ay, az);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_element_zrot(st_context_v2_t pcxt,
									 st_uint_t 		 idx,
									 double 		 zrot)
{
    CONTEXT(pcxt);
    DATA(cxt);

    element_ptr el = data->get_element(idx);
    if (!el) return st_return_code::WARNING_NOT_FOUND;

    el->set_zrot(zrot);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_element_aperture(st_context_v2_t pcxt,
                                         st_uint_t 	     idx,
                                         char      	     ap,
                                         double    	     params[8])
{
    CONTEXT(pcxt);
    DATA(cxt);

    element_ptr el = data->get_element(idx);
    if (!el) return st_return_code::WARNING_NOT_FOUND;
    
    ApertureType ap_type = char_to_aperture(ap);
    int32_t num_params = num_aperture_params(ap_type);
    if (num_params < 0) return st_return_code::INVALID_ARGUMENTS;

    std::vector<double> _params(params, params + num_params);
    aperture_ptr a;
    try
    {
        a = Aperture::make_aperture_from_type(ap_type, _params);
    }
    catch (const std::invalid_argument& e)
    {
        if (cxt->p_cb) cxt->p_cb("geometry creation", e.what());
        return st_return_code::INVALID_ARGUMENTS;
    }

    el->set_aperture(a);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_element_surface(st_context_v2_t pcxt,
                                        st_uint_t 	    idx,
                                        char      	    surf,
                                        double    	    params[8])
{
    CONTEXT(pcxt);
    DATA(cxt);
    
    element_ptr el = data->get_element(idx);
    if (!el) return st_return_code::WARNING_NOT_FOUND;
    
    SurfaceType surf_type = char_to_surface(surf);
    int32_t num_params = num_surface_params(surf_type);
    if (num_params < 0) return st_return_code::INVALID_ARGUMENTS;

    std::vector<double> _params(params, params + num_params);
    surface_ptr s;
    try
    {
        s = SolTrace::Data::make_surface_from_type(surf_type, _params);
    }
    catch (const std::invalid_argument& e)
    {
        if (cxt->p_cb) cxt->p_cb("geometry creation", e.what());
        return st_return_code::INVALID_ARGUMENTS;
    }

    el->set_surface(s);
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_t st_element_optic(st_context_v2_t pcxt,
									  st_uint_t 	  idx,
									  int_fast64_t 	  opt_id)
{
    CONTEXT(pcxt);
    DATA(cxt);
    
    const OpticalPropertySetReference existing_set = get_optics_ref_by_id(data, opt_id);
    if (existing_set.id == SolTrace::Data::OPTICS_ID_TYPES::OPTICS_ID_UNASSIGNED)
        return st_return_code::DATA_VALUE_NOT_FOUND;

    element_ptr el = data->get_element(idx);
    el->set_optical_property_set(existing_set);
    return st_return_code::SUCCESS;
}


// sun functions
std::shared_ptr<Sun> get_or_create_sun(SimulationData *data)
{
    if (!data->get_number_of_ray_sources())
        data->add_ray_source(make_ray_source<Sun>());
    
    ray_source_ptr sun_ptr = data->get_ray_source(0);
    return std::dynamic_pointer_cast<Sun>(sun_ptr);
}

STAPI_V2 st_return_t st_add_sun(st_context_v2_t pcxt, sun_args *args)
{
    CONTEXT(pcxt);
    DATA(cxt);

    st_return_t code = st_return_code::SUCCESS;
    auto sun = get_or_create_sun(data);

    sun->set_position(args->x, args->y, args->z);

    if (args->npoints)
    {
        std::vector<double> v_angle(args->angle, 
                                    args->angle + args->npoints);
        std::vector<double> v_intensity(args->intensity, 
                                        args->intensity + args->npoints);
        ST_WRAP_CB_TRY_CATCH(sun->set_shape(SunShape::USER_DEFINED,
                                            0, 0, 0,
                                            v_angle, 
                                            v_intensity),
                            cxt->p_cb);
    }
    else
    {
        SunShape sun_shape = SunShape::GAUSSIAN;
        double s_hw_csr = args->sigma_halfwidth_csr;
        switch (args->shape)
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
            s_hw_csr = 4.65;
            code = st_return_code::WARNING_SUN_SHAPE_IGNORED;
            break;
        }

        auto sun = get_or_create_sun(data);
        sun->set_shape(sun_shape, 
                       s_hw_csr,
                       s_hw_csr,
                       s_hw_csr);
    }

    return code;
}

STAPI_V2 st_return_t st_sun_shape(st_context_v2_t pcxt,
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
									 double          *x,
									 double          *y,
									 double          *z)
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



// functions for SolTrace data information


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

// functions to get results directly
STAPI_V2 st_return_code st_num_intersections(st_context_v2_t pcxt, uint_fast64_t *num_intersections)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    *num_intersections = result->get_number_of_records();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_code st_locations(st_context_v2_t pcxt,
									 double 		 *loc_x,
									 double 		 *loc_y,
									 double 		 *loc_z)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    std::vector<double> x, y, z;
    glm::dvec3 loc;
    for (auto it = result->get_ray_record_iterator(); !result->is_at_end(it); ++it)
    {
        ray_record_ptr rec = *it;
        for (auto jt = rec->get_interaction_record_iterator(); !rec->is_at_end(jt); ++jt)
        {
            loc = (*jt)->location;
            x.push_back(loc[0]);
            y.push_back(loc[1]);
            z.push_back(loc[2]);
        }
    }

    loc_x = x.data();
    loc_y = y.data();
    loc_z = z.data();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_code st_cosines(st_context_v2_t pcxt,
							 	   double 		   *cos_x,
							 	   double 		   *cos_y,
							 	   double 		   *cos_z)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    std::vector<double> x, y, z;
    glm::dvec3 cosine;
    for (auto it = result->get_ray_record_iterator(); !result->is_at_end(it); ++it)
    {
        ray_record_ptr rec = *it;
        for (auto jt = rec->get_interaction_record_iterator(); !rec->is_at_end(jt); ++jt)
        {
            cosine = (*jt)->direction;
            x.push_back(cosine[0]);
            y.push_back(cosine[1]);
            z.push_back(cosine[2]);
        }
    }

    cos_x = x.data();
    cos_y = y.data();
    cos_z = z.data();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_code st_elementmap(st_context_v2_t pcxt, int *element_map)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    std::vector<int> els;
    for (auto it = result->get_ray_record_iterator(); !result->is_at_end(it); ++it)
    {
        ray_record_ptr rec = *it;
        for (auto jt = rec->get_interaction_record_iterator(); !rec->is_at_end(jt); ++jt)
        {
            els.push_back((int)(*jt)->element);
        }
    }

    element_map = els.data();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_code st_stagemap(st_context_v2_t pcxt, int *stage_map)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    // deprecating stages return array of 0s
    stage_map = new int[result->get_number_of_records()]{};

    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_code st_raynumbers(st_context_v2_t pcxt, int *ray_numbers)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    std::vector<int> nums;
    for (auto it = result->get_ray_record_iterator(); !result->is_at_end(it); ++it)
    {
        ray_record_ptr rec = *it;
        for (auto jt = rec->get_interaction_record_iterator(); !rec->is_at_end(jt); ++jt)
        {
            nums.push_back((int)rec->id);
        }
    }

    ray_numbers = nums.data();
    return st_return_code::SUCCESS;
}

STAPI_V2 st_return_code st_sun_stats(st_context_v2_t pcxt,
									 double 		 *xmin,
									 double 		 *xmax,
									 double 		 *ymin,
									 double 		 *ymax,
									 int 			 *nsunrays)
{
    CONTEXT(pcxt);
    RESULT(cxt);

    *xmin = 0;
    *ymin = 0;
    result->get_sun_dimensions(*xmax, *ymax);
    *nsunrays = result->get_sun_ray_count();

    return st_return_code::SUCCESS;
}

/////////////////////////
// Batch api call work //
/////////////////////////

// could upgrade by moving non macro stuff to internal _st_* functions and fetch 
// full context at the beginning of the for loop

bool is_error(st_return_t code)
{
    return code > st_return_code::SUCCESS && code < st_return_code::WARNING_FELLBACK_FROM_EMBREE;
}

STAPI_V2 st_return_t st_batch(st_context_v2_t pcxt,
							  void**          arguments, 
							  st_uint_t       num_calls,
                              st_uint_t       *fail_iteration,
                              bool            verbose)
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
            
            if (verbose && cxt->p_cb) 
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
                // case st_api_call::CALL_ST_SUN:
                // {
                //     code = st_sun(pcxt,
                //                   call_args->payload.sun_args.point_source,
                //                   call_args->payload.sun_args.shape,
                //                   call_args->payload.sun_args.sigma_halfwidth_csr);
                //     break;
                // }
                case st_api_call::CALL_ST_SUN_XYZ:
                {
                    code = st_sun_xyz(pcxt,
                                      call_args->payload.sun_xyz_args.x,
                                      call_args->payload.sun_xyz_args.y,
                                      call_args->payload.sun_xyz_args.z);
                    break;
                }
                case st_api_call::CALL_ST_SUN_POSITION:
                {
                    code = st_sun_position(pcxt,
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
                    code = st_sun_userdata(pcxt,
                                           call_args->payload.sun_userdata_args.npoints,
                                           call_args->payload.sun_userdata_args.angle,
                                           call_args->payload.sun_userdata_args.intensity);
                    break;
                }
        		// functions for simulation data management thru json strings
                case st_api_call::CALL_ST_READ_INPUT_JSON:
                {
                    code = st_read_input_json(pcxt, call_args->payload.read_input_json_args.json);
                    break;
                }
                // functions for SolTrace data information
                case st_api_call::CALL_ST_NUM_ELEMENTS:
                {
                    code = st_num_elements(pcxt, call_args->payload.num_elements_args.num_elements);
                    break;
                }
                // Simlulation Runner Functions
                case st_api_call::CALL_ST_SIM_SETUP:
                {
                    code = st_sim_setup(pcxt, 
                                        call_args->payload.sim_setup_args.runner_type,
                                        call_args->payload.sim_setup_args.num_threads,
                                        call_args->payload.sim_setup_args.seeds,
                                        call_args->payload.sim_setup_args.num_seeds);
                    break;
                }
                case st_api_call::CALL_ST_SIM_RUN_V2:
                {
                    code = st_sim_run_v2(pcxt);
                    break;
                }
                // Simlulation Results Functions
                default:
                    code = st_return_code::UKNOWN_BATCH_API_CALL_FAILURE;
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
