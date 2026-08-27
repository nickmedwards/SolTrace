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

TEST(results_tests, results_locations_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_locations(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(results_tests, results_cosines_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_cosines(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(results_tests, results_elementmap_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_elementmap(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(results_tests, results_stagemap_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_stagemap(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(results_tests, results_raynumbers_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_raynumbers(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(results_tests, results_sun_stats_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_sun_stats(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(results_tests, results_get_results_data_optix)
{
    SETUP_TEST_CXT();

    LOAD_TEST_JSON();

    code = call_stapi_v2_get_results_data(pcxt, st_runner_type_t::OPTIX);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}