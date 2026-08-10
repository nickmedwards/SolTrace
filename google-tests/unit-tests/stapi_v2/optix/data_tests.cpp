#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(optix_data_tests, data_sun_setup)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sun(pcxt);
    EXPECT_EQ(code, 4 * st_return_code::WARNING_SUN_SHAPE_IGNORED);

    CLEANUP_TEST_CXT();
}

TEST(optix_data_tests, data_sun_xyz)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sun_xyz(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}

TEST(optix_data_tests, data_sun_userdata)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_sun_userdata(pcxt);
    EXPECT_EQ(code, st_return_code::EXCEPTION);

    CLEANUP_TEST_CXT();
}