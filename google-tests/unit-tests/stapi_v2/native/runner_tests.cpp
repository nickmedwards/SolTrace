#include <gtest/gtest.h>

#include "../../../../coretrace/stapi_v2/stapi_v2.h"
#include "across_builds.hpp"

TEST(all_runners_runner_tests, runner_setup)
{
    st_context_v2_t pcxt;
    st_return_t code = st_create_context(&pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);
    EXPECT_NE(pcxt, nullptr);

    code = call_stapi_v2_sim_setup(pcxt);
    EXPECT_EQ(code, st_return_code::WARNING_FELLBACK_FROM_EMBREE + st_return_code::WARNING_FELLBACK_FROM_OPTIX);

    code = st_free_context(pcxt);
    EXPECT_EQ(code, st_return_code::SUCCESS);
}