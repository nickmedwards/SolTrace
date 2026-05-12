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



    // EXPECT_EQ(groups[0], 4);
    // EXPECT_EQ(groups[1], 6);
    // EXPECT_EQ(groups[2], 8);
    // EXPECT_EQ(sd.get_number_of_elements(), 7);

    // auto group_0 = sd.get_element(groups[0]);
    // auto group_1 = sd.get_element(groups[1]);
    // auto group_2 = sd.get_element(groups[2]);
    // EXPECT_EQ(group_0->get_group(), 0);
    // EXPECT_EQ(group_1->get_group(), 1);
    // EXPECT_EQ(group_2->get_group(), 2);
}