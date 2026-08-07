#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(embree_runner_tests, runner_setup)
{
    CXT_SETUP_TEST();

    code = call_stapi_v2_sim_setup(pcxt);
    EXPECT_EQ(code, 
        st_return_code::WARNING_FELLBACK_FROM_OPTIX 
        + st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE
    );

    CXT_CLEANUP_TEST();
}