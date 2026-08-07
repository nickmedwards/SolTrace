#ifndef STAPI_V2_ACROSS_BUILDS_H
#define STAPI_V2_ACROSS_BUILDS_H

#include "../../../../coretrace/stapi_v2/stapi_v2.h"

using json = nlohmann::ordered_json;

// #ifdef __cplusplus
// extern "C" {
// #endif

#define CXT_SETUP_TEST()                         \
    st_context_v2_t pcxt;                        \
    st_return_t code = st_create_context(&pcxt); \
    EXPECT_EQ(code, st_return_code::SUCCESS);    \
    EXPECT_NE(pcxt, nullptr);

#define CXT_CLEANUP_TEST()                   \
    code = st_free_context(pcxt);            \
    EXPECT_EQ(code, st_return_code::SUCCESS);

#define LOAD_JSON_TEST()                                  \
    json root = load_json();                              \
    code = st_read_input_json(pcxt, root.dump().c_str()); \
    EXPECT_EQ(code, st_return_code::SUCCESS);

json load_json();

st_return_t call_stapi_v2_read_input_json(st_context_v2_t pcxt);

st_return_t call_stapi_v2_sim_setup(st_context_v2_t pcxt);

st_return_t call_stapi_v2_sim_run_v2(st_context_v2_t pcxt, st_runner_type_t runner_type);

// #ifdef __cplusplus
// } /* extern "C" */
// #endif

#endif
