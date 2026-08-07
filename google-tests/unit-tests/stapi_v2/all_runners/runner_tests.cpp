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

    json root = load_json();
    code = st_read_input_json(pcxt, root.dump().c_str());
    EXPECT_EQ(code, st_return_code::SUCCESS);

    code = st_sim_setup(pcxt, st_runner_type_t::OPTIX, 1);
    EXPECT_EQ(code, st_return_code::WARNING_ARGUMENT_IGNORED_BY_RUNNER);

    CXT_CLEANUP_TEST();
}