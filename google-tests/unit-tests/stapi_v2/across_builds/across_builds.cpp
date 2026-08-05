/*
functions that are across different api builds (only native, with only embree, with only optix, with both embree and optix).
i.e. shouldn't need google-test.h in here.
intended to be called from tests inside different api build tests, those manage the context that these functions use.
*/

#include <fstream>

#include "stapi_v2.h"

int call_stapi_v2_read_input_json(st_context_v2_t pcxt)
{
    namespace fs = std::filesystem;
    using json = nlohmann::ordered_json;

    // Build paths
    const fs::path project_root(PROJECT_DIR);
    const fs::path sample_path = project_root / "sample_ver_20251112.json";

    std::ifstream ifs(sample_path);
    if (!ifs.is_open()) throw std::runtime_error("Failure opening json");

    // Load json from file stream
    json root;
    ifs >> root;

    // add calls to other overloads
    return st_read_input_json(pcxt, root.dump().c_str());
}