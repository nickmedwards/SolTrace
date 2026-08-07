/*
functions that are across different api builds (only native, with only embree, with only optix, with both embree and optix).
i.e. shouldn't need google-test.h in here.
intended to be called from tests inside different api build tests, those manage the context that these functions use.
*/

#include <fstream>

#include "across_builds.hpp"

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

st_return_t call_stapi_v2_read_input_json(st_context_v2_t pcxt)
{
    json root = load_json();
    // add calls to other overloads
    return st_read_input_json(pcxt, root.dump().c_str());
}

st_return_t call_stapi_v2_sim_setup(st_context_v2_t pcxt)
{
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