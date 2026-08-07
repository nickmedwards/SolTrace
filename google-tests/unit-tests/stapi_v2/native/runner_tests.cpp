#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(native_runner_tests, runner_setup)
{
    CXT_SETUP_TEST();

    code = call_stapi_v2_sim_setup(pcxt);
    EXPECT_EQ(code, 
        st_return_code::WARNING_FELLBACK_FROM_EMBREE 
        + st_return_code::WARNING_FELLBACK_FROM_OPTIX
        + st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE);

    CXT_CLEANUP_TEST();
}

TEST(native_runner_tests, runner_run_native)
{
    CXT_SETUP_TEST();

    LOAD_JSON_TEST();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::NATIVE);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CXT_CLEANUP_TEST();
}