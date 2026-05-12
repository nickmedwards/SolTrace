#include <gtest/gtest.h>

#include <algorithm>

#include <aperture.hpp>
#include <surface.hpp>
#include <constants.hpp>
#include <optix_runner.hpp>
#include <simulation_data_export.hpp>
#include <simulation_result_export.hpp>
#include <json_helpers.hpp>

#include "common.hpp"

TEST(grouped_results, counts_test) {
    using SolTrace::Runner::RunnerStatus;
    namespace fs = std::filesystem;

    // Build paths
    const fs::path project_root(PROJECT_DIR);
    const std::string input_str = project_root.string() + "/field_test.json";

    SimulationData sd;
    ASSERT_NO_THROW(sd.import_json_file(input_str));

    // Check groups
    std::vector<uint_fast64_t> groups = sd.get_groups();
    EXPECT_EQ(sd.get_groups().size(), 5);

    SimulationParameters &params = sd.get_simulation_parameters();
    params.number_of_rays = static_cast<uint_fast64_t>(100);
    params.max_number_of_rays = params.number_of_rays * 100;
    params.seed = 608;

    OptixRunner runner;

    RunnerStatus sts = runner.initialize();
    ASSERT_EQ(sts, RunnerStatus::SUCCESS) << "runner.initialize() failed";
    
    sts = runner.setup_simulation(&sd);
    ASSERT_EQ(sts, RunnerStatus::SUCCESS) << "runner.setup_simulation() failed";
    OptixCSP::SolTraceSystem *sys = runner.get_optix_system();
    ASSERT_EQ(sys->get_num_groups(), 5) << "Number of groups in system does not match expected";
    ASSERT_EQ(sys->get_group(26), -1) << "Element 26 should be ungrouped";
    ASSERT_EQ(sys->get_group(27), 0) << "Element 27 should be in group 0";
    ASSERT_EQ(sys->get_group(127), 4) << "Element 127 should be in group 4";

    sts = runner.run_simulation();
    ASSERT_EQ(sts, RunnerStatus::SUCCESS) << "runner.run_simulation() failed";

    SimulationResult result;
    sts = runner.report_simulation(&result, SolTrace::Runner::RunnerStatistics::GROUPED_COUNTS);
    std::vector<GroupResult> grouped_results = result.get_grouped_results();
    ASSERT_EQ(sts, RunnerStatus::SUCCESS) << "runner.report_simulation() failed";

    // these are the counts that i got, they seem reasonable, its kinda weird that each heliostat
    // recieved the same number of hits but that might be a halton distribution thing. i'm putting
    // the test in for now to make sure the behavior stays the same
    ASSERT_EQ(grouped_results[0].absorb_count, 0);
    ASSERT_EQ(grouped_results[0].reflect_count, 15);
    
    ASSERT_EQ(grouped_results[1].absorb_count, 1);
    ASSERT_EQ(grouped_results[1].reflect_count, 14);
    
    ASSERT_EQ(grouped_results[2].absorb_count, 2);
    ASSERT_EQ(grouped_results[2].reflect_count, 13);
    
    ASSERT_EQ(grouped_results[3].absorb_count, 4);
    ASSERT_EQ(grouped_results[3].reflect_count, 11);
    
    ASSERT_EQ(grouped_results[4].reflect_count, 0);
    ASSERT_EQ(grouped_results[4].absorb_count, 90);
    ASSERT_EQ(grouped_results[4].absorb_sun_previous, 22);
    ASSERT_EQ(grouped_results[4].absorb_previous_group[0], 15);
    ASSERT_EQ(grouped_results[4].absorb_previous_group[1], 14);
    ASSERT_EQ(grouped_results[4].absorb_previous_group[2], 13);
    ASSERT_EQ(grouped_results[4].absorb_previous_group[3], 11);
}