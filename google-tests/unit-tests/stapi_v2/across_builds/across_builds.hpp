#ifndef STAPI_V2_ACROSS_BUILDS_H
#define STAPI_V2_ACROSS_BUILDS_H

#include "../../../../coretrace/stapi_v2/stapi_v2.h"

using json = nlohmann::ordered_json;

#define SETUP_TEST_CXT()                         \
    st_context_v2_t pcxt;                        \
    st_return_t code = st_create_context(&pcxt); \
    EXPECT_EQ(code, st_return_code::SUCCESS);    \
    EXPECT_NE(pcxt, nullptr);

#define CLEANUP_TEST_CXT()                   \
    code = st_free_context(pcxt);            \
    EXPECT_EQ(code, st_return_code::SUCCESS);

#define LOAD_TEST_JSON()                                  \
    json root = load_json();                              \
    code = st_read_input_json(pcxt, root.dump().c_str()); \
    EXPECT_EQ(code, st_return_code::SUCCESS);

///////////////////////
// Utility Functions //
///////////////////////

json load_json();

////////////////////////////////
// Simlulation Data Functions //
////////////////////////////////

// functions for simulation data management thru json strings
st_return_t call_stapi_v2_read_input_json(st_context_v2_t pcxt);

// functions for simulation data management directly
st_return_t call_stapi_v2_sim_params(st_context_v2_t pcxt);
st_return_t call_stapi_v2_sim_errors(st_context_v2_t pcxt);

// function for optical properties
st_return_t call_stapi_v2_add_optics(st_context_v2_t pcxt);
st_return_t call_stapi_v2_all_optics(st_context_v2_t pcxt);

// functions for elements
st_return_t call_stapi_v2_add_elements(st_context_v2_t pcxt);
st_return_t call_stapi_v2_all_elements(st_context_v2_t pcxt);

// sun functions
st_return_t call_stapi_v2_add_sun(st_context_v2_t pcxt);
st_return_t call_stapi_v2_sun(st_context_v2_t pcxt);
st_return_t call_stapi_v2_sun_xyz(st_context_v2_t pcxt);
st_return_t call_stapi_v2_sun_userdata(st_context_v2_t pcxt);


//////////////////////////////////
// Simlulation Runner Functions //
//////////////////////////////////

st_return_t call_stapi_v2_sim_setup(st_context_v2_t pcxt);
st_return_t call_stapi_v2_sim_run_v2(st_context_v2_t pcxt, st_runner_type_t runner_type);

///////////////////////////////////
// Simlulation Results Functions //
///////////////////////////////////

// TODO: add test for st_write_results_json
st_return_t call_stapi_v2_write_results_csv(st_context_v2_t  pcxt, 
                                            st_runner_type_t runner_type, 
                                            const char       *filename);

#endif
