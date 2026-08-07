#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(optix_runner_tests, runner_setup)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sim_setup(pcxt);
    EXPECT_EQ(code, 
        st_return_code::WARNING_FELLBACK_FROM_EMBREE
        + st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE
    );

    CLEANUP_TEST_CXT();
}

TEST(optix_runner_tests, runner_setup_ignore_warning)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = st_sim_setup(pcxt, st_runner_type_t::OPTIX, 1);
    EXPECT_EQ(code, st_return_code::WARNING_ARGUMENT_IGNORED_BY_RUNNER);

    CLEANUP_TEST_CXT();
}

TEST(optix_runner_tests, runner_run_native)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::NATIVE);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(optix_runner_tests, runner_run_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}