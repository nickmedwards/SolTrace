#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(all_runners_json_io, read_input_json)
{
    CXT_SETUP_TEST();

    code = call_stapi_v2_read_input_json(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    CXT_CLEANUP_TEST();
}