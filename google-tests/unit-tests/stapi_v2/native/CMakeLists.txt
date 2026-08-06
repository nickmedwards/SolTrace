# mirroring corestrace/stapi_v2/CMakeLists.txt but forcing only native runner to be built and linked in for testing purposes
project(stapi_v2_native)

include_directories(
    .
    ../across_builds
    ${SAMPLE_DIR}
    ${TEST_INPUT_DIR}
    ../../../../coretrace/simulation_data
    ../../../../coretrace/simulation_results
    ../../../../coretrace/simulation_runner/native_runner
    ../../../../coretrace/stapi_v2
)

set(STAPI_V2_NATIVE_SRC
    ../across_builds/across_builds.cpp
	json_io.cpp
)

add_executable(stapi_v2_native ${STAPI_V2_NATIVE_SRC})

# no build options for optional runners

target_link_libraries(stapi_v2_native PRIVATE
    simdata
    simresult
    native_runner
    stapi_v2
    testtools
    GTest::gtest_main
)

add_custom_command(TARGET stapi_v2_native POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    $<TARGET_FILE:stapi_v2>            # The source DLL from the 'stapi_v2' target
    $<TARGET_FILE_DIR:stapi_v2_native> # The destination folder
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    $<TARGET_PDB_FILE:stapi_v2>        # The source pdb from the 'stapi_v2' target
    $<TARGET_FILE_DIR:stapi_v2_native> # The destination folder
)

if (ENABLE_COVERAGE AND CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_link_options(stapi_v2_native PRIVATE --coverage)
    target_link_libraries(stapi_v2_native gcov)
endif()

if(UNIX)
    target_link_libraries(stapi_v2_native pthread)
endif()

add_test(NAME stapi_v2_native COMMAND stapi_v2_native)