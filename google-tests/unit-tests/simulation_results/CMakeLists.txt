Project(SimulationResultsUnitTests)

include_directories(
    .
    ../common
    ${SAMPLE_DIR}
    ${TEST_INPUT_DIR}
    ../../../coretrace/simulation_results
    ../../../coretrace/simulation_data
    ../../../coretrace/simulation_runner
	../../../coretrace/simulation_runner/optix_runner
)

# Add test files for simulation_results
set(SIMULATION_RESULTS_TEST_SRC
    ../common/common.cpp
    simulation_result_test.cpp
)

add_executable(SimulationResultsUnitTests
    ${SIMULATION_RESULTS_TEST_SRC}
)

set(RES_LIBS
    simdata
    simresult
    GTest::gtest_main
)

target_link_libraries(SimulationResultsUnitTests ${RES_LIBS})

if (ENABLE_COVERAGE AND CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_link_options(SimulationResultsUnitTests PRIVATE --coverage)
    target_link_libraries(SimulationResultsUnitTests gcov)
endif()

if(UNIX)
    target_link_libraries(SimulationResultsUnitTests pthread)
endif()

add_test(NAME SimulationResultsUnitTests COMMAND SimulationResultsUnitTests)
