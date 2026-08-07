#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(all_runners_runner_tests, runner_setup)
{
    CXT_SETUP_TEST();

    code = call_stapi_v2_sim_setup(pcxt);
    EXPECT_EQ(code, st_return_code::RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE);

    CXT_CLEANUP_TEST();
}

TEST(all_runners_runner_tests, runner_setup_ignore_warning)
{
    CXT_SETUP_TEST();

    LOAD_JSON_TEST();

    code = st_sim_setup(pcxt, st_runner_type_t::OPTIX, 1);
    EXPECT_EQ(code, st_return_code::WARNING_ARGUMENT_IGNORED_BY_RUNNER);

    CXT_CLEANUP_TEST();
}

TEST(all_runners_runner_tests, runner_run_native)
{
    CXT_SETUP_TEST();

    LOAD_JSON_TEST();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::NATIVE);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CXT_CLEANUP_TEST();
}

TEST(all_runners_runner_tests, runner_run_embree)
{
    CXT_SETUP_TEST();

    LOAD_JSON_TEST();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::EMBREE);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CXT_CLEANUP_TEST();
}

TEST(all_runners_runner_tests, runner_run_optix)
{
    CXT_SETUP_TEST();

    LOAD_JSON_TEST();

    code = call_stapi_v2_sim_run_v2(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CXT_CLEANUP_TEST();
}

TEST(all_runners_runner_tests, runner_not_found)
{
    CXT_SETUP_TEST();

    code = st_sim_run_v2(pcxt);
    EXPECT_EQ(code, st_return_code::RUNNER_NOT_FOUND);

    CXT_CLEANUP_TEST();
}
