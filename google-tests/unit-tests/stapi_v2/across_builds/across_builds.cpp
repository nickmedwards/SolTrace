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
    const SimulationParameters params = cxt->p_data->get_simulation_parameters();

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
    const SimulationParameters params = cxt->p_data->get_simulation_parameters();

    // test that initialized with defaults
    st_return_t code = check(params.include_sun_shape_errors, false);
    code += check(params.include_optical_errors, false);

    st_sim_errors(pcxt, true, true);

    code += check(params.include_sun_shape_errors, true);
    code += check(params.include_optical_errors, true);
    return code;
}

// functions to add/remove/set optical properties
st_return_t call_stapi_v2_all_optics(st_context_v2_t pcxt)
{
    // set up arguments for st_optic
    st_uint_t idx = 0;
    int       fb = 1; /* 1=front,2=back */
    char      dist = 'g';
    int       optnum, apgr, order = 0;
    double    rreal = 1;
    double    rimag = 0;
    double    ref, tra = .5;
    double    gratingab12[3] = { 0, 0, 0 };
    double    rmsslope, rmsspec = .5;
    int       userefltable, refl_npoints = 0;
    double    *refl_angles;
    double    refls[1] = { .25 };
    int       usetranstable, trans_npoints = 0;
    double    *trans_angles;
    double    transs[1] = { .25 };
    
    // check no optics set
    int *num;
    st_num_optics(pcxt, num);
    st_return_t code = check(num, 0);

    // check add optic -> expect st_return_code::SUCCESS
    code += st_add_optic(pcxt, "test1", num);
    code += check(num, 1);
    
    // check name was set and faces are default
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    SimulationData *data = cxt->p_data;
    optical_set_ptr opt_set;
    for (auto it = data->get_optics_iterator(); !data->is_optics_at_end(it); ++it)
        opt_set = it->second;
    
    code += check(opt_set->get_name(), "test1");
    code += check_optical_side(opt_set, OpticalSide::Front, DistributionType::UNKNOWN, 0, 0, 0, 0);
    code += check_optical_side(opt_set, OpticalSide::Back, DistributionType::UNKNOWN, 0, 0, 0, 0);

    // try to set property set that doesn't exist yet
    // expect -> st_return_code::DATA_VALUE_NOT_FOUND
    code += st_optic(pcxt, 1, fb, dist, optnum, apgr, 
                     order, rreal, rimag, ref, tra, 
                     gratingab12, rmsslope, rmsspec, 
                     userefltable, refl_npoints, 
                     refl_angles, refls, 
                     userefltable, trans_npoints, 
                     trans_angles, transs);
    code += check_optical_side(opt_set, OpticalSide::Front, DistributionType::UNKNOWN, 0, 0, 0, 0);
    
    // try to set distribution type that doesn't exist yet
    // expect -> st_return_code::INVALID_ARGUMENTS
    code += st_optic(pcxt, idx, fb, 'z', optnum, apgr, 
                     order, rreal, rimag, ref, tra, 
                     gratingab12, rmsslope, rmsspec, 
                     userefltable, refl_npoints, 
                     refl_angles, refls, 
                     userefltable, trans_npoints, 
                     trans_angles, transs);
    code += check_optical_side(opt_set, OpticalSide::Front, DistributionType::UNKNOWN, 0, 0, 0, 0);

    // try to use optical tables
    // expect -> st_return_code::WARNING_OPTICAL_TABLE_DEPRECATED
    // reflection table
    code += st_optic(pcxt, idx, fb, dist, optnum, apgr, 
                     order, rreal, rimag, ref, tra, 
                     gratingab12, rmsslope, rmsspec, 
                     1, 1, 
                     refl_angles, refls, 
                     userefltable, trans_npoints, 
                     trans_angles, transs);
    code += check_optical_side(opt_set, OpticalSide::Front, DistributionType::GAUSSIAN, 0.5, 0.25, 0, 0);
    
    // expect -> st_return_code::WARNING_OPTICAL_TABLE_DEPRECATED
    // transmission table
    code += st_optic(pcxt, idx, fb, dist, optnum, apgr, 
                     order, rreal, rimag, ref, tra, 
                     gratingab12, rmsslope, rmsspec, 
                     userefltable, refl_npoints,
                     refl_angles, refls, 
                     1, 1, 
                     trans_angles, transs);
    code += check_optical_side(opt_set, OpticalSide::Front, DistributionType::GAUSSIAN, 0.25, 0.5, 0, 0);

    // expect -> st_return_code::SUCCESS
    code += st_optic(pcxt, idx, 2, dist, optnum, apgr, 
                     order, rreal, rimag, ref, tra, 
                     gratingab12, rmsslope, rmsspec, 
                     userefltable, refl_npoints, 
                     refl_angles, refls, 
                     userefltable, trans_npoints, 
                     trans_angles, transs);
    code += check_optical_side(opt_set, OpticalSide::Back, DistributionType::GAUSSIAN, 0.5, 0.5, 0, 0);

    // test removing optics
    // expect -> st_return_code::WARNING_NOT_FOUND
    code += st_delete_optic(pcxt, 1);

    // add an optical set to remove and still test clear
    code += st_add_optic(pcxt, "test2", num);
    code += check(num, 2);
    // expect -> st_return_code::SUCCESS
    code += st_delete_optic(pcxt, 1);

    st_num_optics(pcxt, num);
    code = check(num, 1);

    // test clear
    // expect -> st_return_code::SUCCESS
    code += st_clear_optics(pcxt);
    st_num_optics(pcxt, num);
    code = check(num, 0);
    
    return code;
}

// sun functions
st_return_t call_stapi_v2_sun(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    // expect == 0
    st_return_t code = (st_return_t)cxt->p_data->get_number_of_ray_sources();

    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_sun(pcxt, 0, (char)"", 0);
    auto sun_0 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    SunShape shape = sun_0->get_shape();
    double sigma = sun_0->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;

    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_sun(pcxt, 1, (char)"", 0);
    auto sun_1 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_1->get_shape();
    sigma = sun_1->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    // expect sun opbject to be same
    if (sun_0 != sun_1) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // tests below follow switch statement order in st_sun

    // expect += 0
    code += st_sun(pcxt, 0, 'g', 5);
    auto sun_2 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_2->get_shape();
    sigma = sun_2->get_sigma();
    // expect both of these to equal args
    if (shape != SunShape::GAUSSIAN || sigma != 5) ++code;
    // expect sun opbject to be same
    if (sun_1 != sun_2) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += 0
    code += st_sun(pcxt, 0, 'p', 5);
    auto sun_3 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_3->get_shape();
    double hw = sun_3->get_half_width();
    // expect both of these to equal args
    if (shape != SunShape::PILLBOX || hw != 5) ++code;
    // expect sun opbject to be same
    if (sun_2 != sun_3) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_sun(pcxt, 0, 'l', 5);
    auto sun_4 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_4->get_shape();
    sigma = sun_4->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    // expect sun opbject to be same
    if (sun_3 != sun_4) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += 0
    code += st_sun(pcxt, 0, 'b', .5);
    auto sun_5 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_5->get_shape();
    double csr = sun_5->get_circumsolar_ratio();
    // expect both of these to equal args
    if (shape != SunShape::BUIE_CSR || csr != .5) ++code;
    // expect sun opbject to be same
    if (sun_4 != sun_5) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect += st_return_code::WARNING_SUN_SHAPE_IGNORED
    code += st_sun(pcxt, 0, 'u', 0);
    auto sun_6 = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    shape = sun_6->get_shape();
    sigma = sun_6->get_sigma();
    // expect both of these to equal defaults
    if (shape != SunShape::GAUSSIAN || sigma != 4.65) ++code;
    // expect sun opbject to be same
    if (sun_5 != sun_6) ++code;
    // expect one ray source
    code += (st_return_t)cxt->p_data->get_number_of_ray_sources() - 1;

    // expect code == 4 * st_return_code::WARNING_SUN_SHAPE_IGNORED
    return code;
}

st_return_t call_stapi_v2_sun_xyz(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    // expect == 0
    st_return_t code = (st_return_t)cxt->p_data->get_number_of_ray_sources();

    // expect == 0
    code += st_sun_xyz(pcxt, 608, 303, 1000);
    auto sun = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    auto xyz = sun->get_position();
    // expect position to be what was set
    if (xyz[0] != 608 || xyz[1] != 303 || xyz[2] != 1000) ++code;

    return code;
}

st_return_t call_stapi_v2_sun_userdata(st_context_v2_t pcxt)
{
    st_context *cxt = reinterpret_cast<st_context*>(pcxt);
    // expect == 0
    st_return_t code = (st_return_t)cxt->p_data->get_number_of_ray_sources();

    double good_angles[3]      = {0, 1, 2};
    double good_intensities[3] = {0, 1, 2};

    // expect += 0
    code += st_sun_userdata(pcxt, 3, good_angles, good_intensities);
    auto sun = std::dynamic_pointer_cast<Sun>(cxt->p_data->get_ray_source(0));
    
    std::vector<double> angles, intensities;
    sun->get_user_data(angles, intensities);
    if (angles[0] != good_angles[0]
        || angles[1] != good_angles[1]
        || angles[2] != good_angles[2]
        || intensities[0] != intensities[0]
        || intensities[1] != intensities[1]
        || intensities[2] != intensities[2]) ++code;

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