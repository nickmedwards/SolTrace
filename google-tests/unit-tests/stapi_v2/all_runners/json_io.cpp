#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(json_io, read_input_json)
{
    SETUP_TEST_CXT();

    code = call_stapi_v2_read_input_json(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CLEANUP_TEST_CXT();
}