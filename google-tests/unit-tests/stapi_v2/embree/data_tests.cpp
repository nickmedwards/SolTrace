#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(optix_data_tests, data_params)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sim_params(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(optix_data_tests, data_errors)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sim_errors(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(optix_data_tests, data_add_sun)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_add_sun(pcxt);
    EXPECT_EQ(code, 3 * st_return_code::WARNING_SUN_SHAPE_IGNORED
                    + st_return_code::EXCEPTION);

    CLEANUP_TEST_CXT();
}

TEST(optix_data_tests, data_sun_shape)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sun_shape(pcxt);
    EXPECT_EQ(code, 3 * st_return_code::WARNING_SUN_SHAPE_IGNORED);

    CLEANUP_TEST_CXT();
}

// TEST(embree_data_tests, data_sun_xyz)
// {
//     SETUP_TEST_CXT();

//     code = call_stapi_v2_sun_xyz(pcxt);
//     EXPECT_EQ(code, st_return_code::SUCCESS);

//     CLEANUP_TEST_CXT();
// }

// TEST(embree_data_tests, data_sun_userdata)
// {
//     SETUP_TEST_CXT();

//     code = call_stapi_v2_sun_userdata(pcxt);
//     EXPECT_EQ(code, st_return_code::EXCEPTION);

//     CLEANUP_TEST_CXT();
// }