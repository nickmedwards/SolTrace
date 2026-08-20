/*
functions that are across different api builds (only native, with only embree, with only optix, with both embree and optix).
i.e. shouldn't need google-test.h in here.
intended to be called from tests inside different api build tests, those manage the context that these functions use.
*/

#include <fstream>
#include <vector>

#include "across_builds.hpp"

///////////////////////
// Utility Functions //
///////////////////////

json load_json()
{
    namespace fs = std::filesystem;

    // Build paths
    const fs::path project_root(PROJECT_DIR);
    const fs::path sample_path = project_root / "sample_ver_20251112.json";

    std::ifstream ifs(sample_path);
    if (!ifs.is_open()) throw std::runtime_error("Failure opening json");

    // Load json from file stream
    json root;
    ifs >> root;
    return root;
}

auto check = [](auto val, auto should_be)
{
    // false = 0, true = 1, to make successful test = 0 
    // -> !(a == b) returns 0 if the are equal, 1 otherwise
    return (st_return_t)!(val == (decltype(val))should_be); 
};

st_return_t check_optical_side(optical_set_ptr  set,
                               OpticalSide      side,
                               DistributionType dist,
                               double           tran,
                               double           refl,
                               double           slope,
                               double           spec)
{
    if (set->get_error_distribution(side) != dist
        || set->get_reflectivity(side) != refl
        || set->get_transmissivity(side) != tran
        || set->get_slope_error(side) != slope
        || set->get_specularity_error(side) != spec)
    {
        return 1;
    }
    return 0;
}

////////////////////////////////
// Simlulation Data Functions //
////////////////////////////////

// functions for simulation data management thru json strings
st_return_t call_stapi_v2_read_input_json(st_context_v2_t pcxt)
{
    json root = load_json();
    // add calls to other overloads
    return st_read_input_json(pcxt, root.dump().c_str());
}

// functions for simulation data management directly
st_return_t call_stapi_v2_sim_params(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationParameters &params = cxt->p_data->get_simulation_parameters();

    // test that initialized with defaults
    st_return_t code = check(params.number_of_rays, 10000);
    code += check(params.max_number_of_rays, 1000000);
    code += check(params.as_power_tower, false);

    st_sim_params(pcxt, 1, 100, true);

    code += check(params.number_of_rays, 1);
    code += check(params.max_number_of_rays, 100);
    code += check(params.as_power_tower, true);
    return code;
}

st_return_t call_stapi_v2_sim_errors(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationParameters &params = cxt->p_data->get_simulation_parameters();

    // test that initialized with defaults
    st_return_t code = check(params.include_sun_shape_errors, false);
    code += check(params.include_optical_errors, false);

    st_sim_errors(pcxt, true, true);

    code += check(params.include_sun_shape_errors, true);
    code += check(params.include_optical_errors, true);
    return code;
}

// functions to add/remove/set optical properties
st_return_t call_stapi_v2_add_optics(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    auto get_last_opt_set = [data]()
    {
        optical_set_ptr opt_set;
        for (auto it = data->get_optics_iterator(); !data->is_optics_at_end(it); ++it)
            opt_set = it->second;
        return opt_set;
    };

    args_optical_properties_set set = {"test1", 1.1, 1.1, 1};
    args_optical_properties_face f = {.5, .5, .5, .5, 'g'};
    args_optical_properties_face b = {.25, .25, .25, .25, 'g'};

    // check no optics set
    uint_fast64_t num = -1;
    st_num_optics(pcxt, &num);
    st_return_t code = check(num, 0);

    // test add refractive set
    // expect += st_return_code::SUCCESS
    code += st_add_optical_properties_set(pcxt, &set, &f, &b, &num);
    code += check(num, 1);

    // check values were set
    auto last_opt_set = get_last_opt_set();
    code += check(last_opt_set->get_name(), "test1");
    code += check(last_opt_set->get_interaction_type(), InteractionType::REFRACTION);
    code += check_optical_side(last_opt_set, OpticalSide::Front, DistributionType::GAUSSIAN, .5, .5, .5, .5);
    code += check_optical_side(last_opt_set, OpticalSide::Back, DistributionType::GAUSSIAN, .25, .25, .25, .25);

    // test add reflective set
    set.type = 0;
    set.name = "test2";
    // expect += st_return_code::SUCCESS
    code += st_add_optical_properties_set(pcxt, &set, &f, &b, &num);
    code += check(num, 2);

    // check values were set
    last_opt_set = get_last_opt_set();
    code += check(last_opt_set->get_name(), "test2");
    code += check(last_opt_set->get_interaction_type(), InteractionType::REFLECTION);
    code += check_optical_side(last_opt_set, OpticalSide::Front, DistributionType::GAUSSIAN, .5, .5, .5, .5);
    code += check_optical_side(last_opt_set, OpticalSide::Back, DistributionType::GAUSSIAN, .25, .25, .25, .25);

    // set bad distribution characters for front
    f.error_distribution_type = 'z';
    // expect += st_return_code::INVALID_ARGUMENTS
    code += st_add_optical_properties_set(pcxt, &set, &f, &b, &num);
    code += check(num, 2);

    // set bad distribution characters for back
    f.error_distribution_type = 'g';
    b.error_distribution_type = 'z';
    // expect += st_return_code::INVALID_ARGUMENTS
    code += st_add_optical_properties_set(pcxt, &set, &f, &b, &num);
    code += check(num, 2);

    // expect == 2 * st_return_code::INVALID_ARGUMENTS
    return code;
}

st_return_t call_stapi_v2_remove_optics(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    args_optical_properties_set set = {"test1", 1.1, 1.1, 0};
    args_optical_properties_face f = {.5, .5, .5, .5, 'g'};
    args_optical_properties_face b = {.25, .25, .25, .25, 'g'};

    // check no optics set
    uint_fast64_t num = -1;
    st_num_optics(pcxt, &num);
    st_return_t code = check(num, 0);

    // expect += st_return_code::SUCCESS
    code += st_add_optical_properties_set(pcxt, &set, &f, &b, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_clear_optics(pcxt);
    st_num_optics(pcxt, &num);
    code += check(num, 0);

    // expect += st_return_code::SUCCESS
    code += st_add_optical_properties_set(pcxt, &set, &f, &b, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_delete_optic(pcxt, 1);
    st_num_optics(pcxt, &num);
    code += check(num, 0);
    
    return code;
}

// functions to add/remove/modify elements
st_return_t call_stapi_v2_add_elements(st_context_v2_t pcxt)
{
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);

    // check no elements set
    uint_fast64_t num = -1;
    st_num_elements(pcxt, &num);
    st_return_t code = check(num, 0);

    // set element to non default values
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // test good element
    // expect += st_return_code::SUCCESS
    code += st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);

    // test values set
    element_ptr el = data->get_element(1);
    auto sel = std::dynamic_pointer_cast<SingleElement>(el);
    code += check(sel->is_enabled(), false);
    code += check(sel->is_virtual(), true);
    auto origin = sel->get_origin_ref();
    auto aim = sel->get_aim_vector_ref();
    auto zrot = sel->get_zrot();
    code += check(origin[0], 2);
    code += check(origin[1], 2);
    code += check(origin[2], 2);
    code += check(aim[0], 2);
    code += check(aim[1], 2);
    code += check(aim[2], 2);
    code += check(zrot, 2);

    optical_set_ptr opt_set = sel->get_optical_property_set();
    code += check(opt_set->get_name(), std::string("dummy"));

    aperture_ptr ap = sel->get_aperture();
    code += check(ap->my_type, ApertureType::CIRCLE);
    auto circle = std::dynamic_pointer_cast<Circle>(ap);
    code += check(circle->diameter, 2);

    surface_ptr surf = sel->get_surface();
    code += check(surf->my_type, SurfaceType::PARABOLA);
    auto parabola = std::dynamic_pointer_cast<Parabola>(surf);
    code += check(parabola->focal_length_x, 1. / 4.);
    code += check(parabola->focal_length_y, 1. / 4.);

    // try bad optical id
    // expect code += st_return_code::DATA_VALUE_NOT_FOUND
    code += st_add_element(pcxt, &el_args, res.id + 1, a_params, s_params, &num);
    code += check(num, 1);

    // try bad aperture type
    // expect code += st_return_code::INVALID_ARGUMENTS
    el_args.ap = 'z';
    code += st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    el_args.ap = 'c';
    
    // try bad surface type
    // expect code += st_return_code::INVALID_ARGUMENTS
    el_args.surf = 'z';
    code += st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    el_args.surf = 'p';
    
    // try bad aperture params
    // expect code += st_return_code::INVALID_ARGUMENTS
    double bad_a_params[1] = { -2 };
    code += st_add_element(pcxt, &el_args, res.id, bad_a_params, s_params, &num);
    code += check(num, 1);

    // try bad surface params
    // expect code += st_return_code::INVALID_ARGUMENTS
    double bad_s_params[2] = { std::numeric_limits<double>::quiet_NaN(), 2 };
    code += st_add_element(pcxt, &el_args, res.id, a_params, bad_s_params, &num);
    code += check(num, 1);

    // expect == st_return_code::DATA_VALUE_NOT_FOUND
    //         + 4 * st_return_code::INVALID_ARGUMENTS 
    return code;
}

st_return_t call_stapi_v2_remove_elements(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_clear_elements(pcxt);
    st_num_elements(pcxt, &num);
    code += check(num, 0);
    
    // expect += st_return_code::SUCCESS
    code += st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);

    // expect += st_return_code::WARNING_NOT_FOUND
    code += st_delete_element(pcxt, 1);
    st_num_elements(pcxt, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_delete_element(pcxt, 2);
    st_num_elements(pcxt, &num);
    code += check(num, 0);
    
    // expect == st_return_code::WARNING_NOT_FOUND
    return code;
}

st_return_t call_stapi_v2_toggle_element(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_element_enabled(pcxt, 1, true);
    
    // expect += st_return_code::SUCCESS
    code += st_element_virtual(pcxt, 1, false);
    
    // expect += st_return_code::WARNING_NOT_FOUND
    code += st_element_enabled(pcxt, 0, false);
    
    // expect += st_return_code::WARNING_NOT_FOUND
    code += st_element_virtual(pcxt, 0, true);

    // test values set
    auto sel = std::dynamic_pointer_cast<SingleElement>(data->get_element(1));
    code += check(sel->is_enabled(), true);
    code += check(sel->is_virtual(), false);

    // expect == 2 * st_return_code::WARNING_NOT_FOUND
    return code; 
}

st_return_t call_stapi_v2_element_xyz(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_element_xyz(pcxt, 1, 1, 1, 1);
    
    // expect += st_return_code::WARNING_NOT_FOUND
    code += st_element_xyz(pcxt, 0, 2, 2, 2);

    // test values set
    auto sel = std::dynamic_pointer_cast<SingleElement>(data->get_element(1));
    auto origin = sel->get_origin_ref();
    code += check(origin[0], 1);
    code += check(origin[1], 1);
    code += check(origin[2], 1);

    // expect == st_return_code::WARNING_NOT_FOUND
    return code; 
}

st_return_t call_stapi_v2_element_aim(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_element_aim(pcxt, 1, 1, 1, 1);
    
    // expect += st_return_code::WARNING_NOT_FOUND
    code += st_element_aim(pcxt, 0, 2, 2, 2);

    // test values set
    auto sel = std::dynamic_pointer_cast<SingleElement>(data->get_element(1));
    auto aim = sel->get_aim_vector_ref();
    code += check(aim[0], 1);
    code += check(aim[1], 1);
    code += check(aim[2], 1);

    // expect == st_return_code::WARNING_NOT_FOUND
    return code; 
}

st_return_t call_stapi_v2_element_zrot(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    
    // expect += st_return_code::SUCCESS
    code += st_element_zrot(pcxt, 1, 1);
    
    // expect += st_return_code::WARNING_NOT_FOUND
    code += st_element_zrot(pcxt, 0, 2);

    // test values set
    auto sel = std::dynamic_pointer_cast<SingleElement>(data->get_element(1));
    auto zrot = sel->get_zrot();
    code += check(zrot, 1);

    // expect == st_return_code::WARNING_NOT_FOUND
    return code; 
}

st_return_t call_stapi_v2_element_aperture(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);

    double params[2] = { 4, 4 };

    // expect += st_return_code::SUCCESS
    code += st_element_aperture(pcxt, 1, 'r', params);

    auto sel = std::dynamic_pointer_cast<SingleElement>(data->get_element(1));
    aperture_ptr ap = sel->get_aperture();
    code += check(ap->my_type, ApertureType::RECTANGLE);
    auto rectangle = std::dynamic_pointer_cast<Rectangle>(ap);
    code += check(rectangle->x_length(), 4);
    code += check(rectangle->y_length(), 4);

    // expect += st_return_code::INVALID_ARGUMENTS
    code += st_element_aperture(pcxt, 1, 'z', params);

    double bad_params[2] = { -4, 4 };
    // expect += st_return_code::INVALID_ARGUMENTS
    code += st_element_aperture(pcxt, 1, 'r', bad_params);
    
    // expect == 2 * st_return_code::INVALID_ARGUMENTS
    return code;
}

st_return_t call_stapi_v2_element_surface(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res = data->add_optical_property_set(opt);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res.id, a_params, s_params, &num);
    code += check(num, 1);
    
    double params[1] = { 4 };
    // expect += st_return_code::SUCCESS
    code += st_element_surface(pcxt, 1, 's', params);
    
    auto sel = std::dynamic_pointer_cast<SingleElement>(data->get_element(1));
    surface_ptr surf = sel->get_surface();
    code += check(surf->my_type, SurfaceType::SPHERE);
    auto sphere = std::dynamic_pointer_cast<Sphere>(surf);
    code += check(sphere->vertex_curv, 4);

    // expect += st_return_code::INVALID_ARGUMENTS
    code += st_element_surface(pcxt, 1, 'z', params);

    double bad_params[1] = { -4 };
    // expect += st_return_code::INVALID_ARGUMENTS
    code += st_element_surface(pcxt, 1, 's', bad_params);

    // expect == 2 * st_return_code::INVALID_ARGUMENTS
    return code;
}

st_return_t call_stapi_v2_element_optic(st_context_v2_t pcxt)
{
    uint_fast64_t num = -1;
    // set up dummy optical properties
    OpticalPropertySet opt1(InteractionType::REFLECTION, std::string("dummy"));
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    OpticalPropertySetReference res1 = data->add_optical_property_set(opt1);
    // set up dummy element arguments
    args_element el_args = {2, 2, 2, 2, 2, 2, 2, false, true, 'c', 'p'};
    double a_params[1] = { 2 };
    double s_params[2] = { 2, 2 };

    // expect += st_return_code::SUCCESS
    st_return_t code = st_add_element(pcxt, &el_args, res1.id, a_params, s_params, &num);
    code += check(num, 1);

    // expect += st_return_code::DATA_VALUE_NOT_FOUND
    code += st_element_optic(pcxt, 1, res1.id + 1);

    // set up other optical properties
    OpticalPropertySet opt2(InteractionType::REFLECTION, std::string("other"));
    OpticalPropertySetReference res2 = data->add_optical_property_set(opt2);
    // expect += st_return_code::SUCCESS
    code += st_element_optic(pcxt, 1, res2.id);
    
    auto sel = std::dynamic_pointer_cast<SingleElement>(data->get_element(1));
    optical_set_ptr opt_set = sel->get_optical_property_set();
    code += check(opt_set->get_name(), std::string("other"));
    
    // expect == st_return_code::DATA_VALUE_NOT_FOUND
    return code;
}

// sun functions
st_return_t call_stapi_v2_add_sun(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    // expect == 0
    st_return_t code = (st_return_t)cxt->p_data->get_number_of_ray_sources();

    double good_angles[3]      = {0, 1, 2};
    double good_intensities[3] = {0, 1, 2};
    double bad_intensities[2]  = {0, -1};

    args_sun args = {3, 608, 303, 1000, 5, ' '};

    // test bad intensitites
    // expect += st_return_code::EXCEPTION
    code += st_add_sun(pcxt, &args, good_angles, bad_intensities);

    auto sun_0 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    auto xyz = sun_0->get_position();
    // expect position to be what was set
    if (xyz[0] != 608 || xyz[1] != 303 || xyz[2] != 1000) ++code;
    std::vector<double> angles, intensities;
    sun_0->get_user_data(angles, intensities);
    // expect vectors of no size
    if (angles.size() || intensities.size()) ++code;

    // test good intensities
    // expect += st_return_code::SUCCESS
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);
    
    sun_0->get_user_data(angles, intensities);
    if (angles[0] != good_angles[0]
        || angles[1] != good_angles[1]
        || angles[2] != good_angles[2]
        || intensities[0] != good_intensities[0]
        || intensities[1] != good_intensities[1]
        || intensities[2] != good_intensities[2]) ++code;

    // test built in shapes
    args.npoints = 0;
    
    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);
    auto sun_1 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    SunShape shape = sun_1->get_shape();
    double sigma = sun_1->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    // expect sun object to be same
    if (sun_0 != sun_1) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += st_return_code::SUCCESS
    args.shape = 'g';
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);
    auto sun_2 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_2->get_shape();
    sigma = sun_2->get_sigma();
    // expect both of these to equal args
    if (shape != SunShape::GAUSSIAN || sigma != 5) ++code;
    // expect sun object to be same
    if (sun_1 != sun_2) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += st_return_code::SUCCESS
    args.shape = 'p';
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);
    auto sun_3 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_3->get_shape();
    double hw = sun_3->get_half_width();
    // expect both of these to equal args
    if (shape != SunShape::PILLBOX || hw != 5) ++code;
    // expect sun object to be same
    if (sun_2 != sun_3) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    args.shape = 'l';
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);
    auto sun_4 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_4->get_shape();
    sigma = sun_4->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    // expect sun object to be same
    if (sun_3 != sun_4) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += 0
    args.shape = 'b';
    args.sigma_halfwidth_csr = .5;
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);
    auto sun_5 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_5->get_shape();
    double csr = sun_5->get_circumsolar_ratio();
    // expect both of these to equal args
    if (shape != SunShape::BUIE_CSR || csr != .5) ++code;
    // expect sun object to be same
    if (sun_4 != sun_5) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    args.shape = 'u';
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);
    auto sun_6 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_6->get_shape();
    sigma = sun_6->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    // expect sun object to be same
    if (sun_5 != sun_6) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect == 3 * st_return_code::WARNING_SUN_SHAPE_IGNORED
    //           + st_return_code::EXCEPTION
    return code;
}

st_return_t call_stapi_v2_sun_shape(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    // expect == 0
    st_return_t code = (st_return_t)cxt->p_data->get_number_of_ray_sources();

    double good_angles[3]      = {0, 1, 2};
    double good_intensities[3] = {0, 1, 2};

    args_sun args = {3, 608, 303, 1000, 5, 'g'};

    // expect += st_return_code::SUCCESS
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);

    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_sun_shape(pcxt, ' ', 0);
    auto sun = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    SunShape shape = sun->get_shape();
    double sigma = sun->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;

    // tests below follow switch statement order in st_sun_shape

    // expect += 0
    code += st_sun_shape(pcxt, 'g', 5);
    auto sun_2 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_2->get_shape();
    sigma = sun_2->get_sigma();
    // expect both of these to equal args
    if (shape != SunShape::GAUSSIAN || sigma != 5) ++code;
    
    // expect += 0
    code += st_sun_shape(pcxt, 'p', 5);
    auto sun_3 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_3->get_shape();
    double hw = sun_3->get_half_width();
    // expect both of these to equal args
    if (shape != SunShape::PILLBOX || hw != 5) ++code;
    
    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_sun_shape(pcxt, 'l', 5);
    auto sun_4 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_4->get_shape();
    sigma = sun_4->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    
    // expect += 0
    code += st_sun_shape(pcxt, 'b', .5);
    auto sun_5 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_5->get_shape();
    double csr = sun_5->get_circumsolar_ratio();
    // expect both of these to equal args
    if (shape != SunShape::BUIE_CSR || csr != .5) ++code;
    
    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_sun_shape(pcxt, 'u', 0);
    auto sun_6 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_6->get_shape();
    sigma = sun_6->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    
    // expect code == 3 * st_return_code::WARNING_SUN_SHAPE_IGNORED
    return code;
}

st_return_t call_stapi_v2_sun_xyz(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    // expect == 0
    st_return_t code = (st_return_t)cxt->p_data->get_number_of_ray_sources();

    double good_angles[3]      = {0, 1, 2};
    double good_intensities[3] = {0, 1, 2};

    args_sun args = {3, 608, 303, 1000, 5, 'g'};

    // expect += st_return_code::SUCCESS
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);

    // expect == 0
    code += st_sun_xyz(pcxt, 0, 0, 0);
    auto sun = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    auto xyz = sun->get_position();
    // expect position to be what was set
    if (xyz[0] != 0 || xyz[1] != 0 || xyz[2] != 0) ++code;

    return code;
}

st_return_t call_stapi_v2_sun_userdata(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    // expect == 0
    st_return_t code = (st_return_t)cxt->p_data->get_number_of_ray_sources();

    double good_angles[3]      = {0, 1, 2};
    double good_intensities[3] = {0, 1, 2};

    args_sun args = {3, 608, 303, 1000, 5, 'g'};

    // expect += st_return_code::SUCCESS
    code += st_add_sun(pcxt, &args, good_angles, good_intensities);

    double new_angles[3]      = {0, .1, .2};
    double new_intensities[3] = {0, .1, .2};
    // expect += 0
    code += st_sun_userdata(pcxt, 3, new_angles, new_intensities);
    auto sun = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    
    std::vector<double> angles, intensities;
    sun->get_user_data(angles, intensities);
    if (angles[0] != new_angles[0]
        || angles[1] != new_angles[1]
        || angles[2] != new_angles[2]
        || intensities[0] != new_intensities[0]
        || intensities[1] != new_intensities[1]
        || intensities[2] != new_intensities[2]) ++code;

    double bad_intensities[2] = {0, -1};
    // expect += st_return_code::EXCEPTION
    code += st_sun_userdata(pcxt, 3, good_angles, bad_intensities);
    
    return code;
}

//////////////////////////////////
// Simlulation Runner Functions //
//////////////////////////////////

// functions for SolTrace runner management
st_return_t call_stapi_v2_sim_setup(st_context_v2_t pcxt)
{
    // this fails on first execution after build if optix is built
    // when debugging first execution, it passes 
    json root = load_json();

    st_return_t rt = st_read_input_json(pcxt, root.dump().c_str());

    if (rt != st_return_code::SUCCESS) return rt;

    rt =  st_sim_setup(pcxt, st_runner_type_t::NATIVE);
    unsigned int *seeds_test = new unsigned int[2] { 608, 303, };
    rt += st_sim_setup(pcxt, st_runner_type_t::NATIVE, 1, seeds_test, 2);
    rt += st_sim_setup(pcxt, st_runner_type_t::EMBREE);
    rt += st_sim_setup(pcxt, st_runner_type_t::OPTIX);

    return rt;
}

st_return_t call_stapi_v2_sim_run_v2(st_context_v2_t pcxt, st_runner_type_t runner_type)
{
    if (runner_type != st_runner_type_t::OPTIX)
    {
        st_context *cxt = reinterpret_cast<st_context*>(pcxt);
        cxt->p_data->set_number_of_rays(1000);
    }

    return st_sim_setup(pcxt, runner_type) + st_sim_run_v2(pcxt);
}

///////////////////////////////////
// Simlulation Results Functions //
///////////////////////////////////

st_return_t call_stapi_v2_write_results_csv(st_context_v2_t  pcxt, 
                                            st_runner_type_t runner_type, 
                                            const char       *filename)
{
    if (runner_type != st_runner_type_t::OPTIX)
    {
        st_context* cxt = reinterpret_cast<st_context*>(pcxt);
        cxt->p_data->set_number_of_rays(1000);
    }

    st_return_t rt = st_sim_setup(pcxt, runner_type); 
    rt += st_sim_run_v2(pcxt);
    rt += st_sim_report(pcxt, 0);
    rt += st_write_results_csv(pcxt, filename);

    std::error_code ec;
    std::filesystem::remove(filename, ec);

    return rt;
}