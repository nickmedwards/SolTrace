#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(results_tests, results_write_native)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_write_results_csv(pcxt, st_runner_type_t::NATIVE, "temp_char.csv");
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(results_tests, results_write_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_write_results_csv(pcxt, st_runner_type_t::OPTIX, "temp_char.csv");
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}