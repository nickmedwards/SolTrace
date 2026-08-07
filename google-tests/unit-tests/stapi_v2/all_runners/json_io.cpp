#include <gtest/gtest.h>

#include "across_builds.hpp"

TEST(all_runners_json_io, read_input_json)
{
    st_context_v2_t pcxt;
    st_return_t code = st_create_context(&pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);
    EXPECT_NE(pcxt, nullptr);

    code = call_stapi_v2_read_input_json(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);

    code = st_free_context(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);
}