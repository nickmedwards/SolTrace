#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(embree_runner_tests, runner_setup)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sim_setup(pcxt);
    EXPECT_EQ(code, 
        st_return_code::WARNING_FELLBACK_FROM_OPTIX 
        + st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE
    );

    CLEANUP_TEST_CXT();
}

TEST(embree_runner_tests, runner_run_native)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::NATIVE);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(embree_runner_tests, runner_run_embree)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::EMBREE);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}