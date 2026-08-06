# mirroring corestrace/stapi_v2/CMakeLists.txt but forcing all runners to be built and linked in for testing purposes
project(stapi_v2_all_runners)

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

set(STAPI_V2_ALL_RUNNERS_SRC
    ../across_builds/across_builds.cpp
	json_io.cpp
)

add_executable(stapi_v2_all_runners ${STAPI_V2_ALL_RUNNERS_SRC})

# build options for optional runners
target_include_directories(stapi_v2_all_runners PRIVATE
    ../../../../coretrace/simulation_runner/embree_runner
)
target_compile_definitions(stapi_v2_all_runners PRIVATE SOLTRACE_EMBREE_SUPPORT)
target_link_libraries(stapi_v2_all_runners PRIVATE embree_runner)

target_include_directories(stapi_v2_all_runners PRIVATE
    ../../../../coretrace/simulation_runner/optix_runner
)
target_compile_definitions(stapi_v2_all_runners PRIVATE SOLTRACE_OPTIX_SUPPORT)
target_link_libraries(stapi_v2_all_runners PRIVATE optix_runner)

target_link_libraries(stapi_v2_all_runners PRIVATE
    simdata
    simresult
    native_runner
    stapi_v2
    testtools
    GTest::gtest_main
)

add_custom_command(TARGET stapi_v2_all_runners POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    $<TARGET_FILE:stapi_v2>                 # The source DLL from the 'stapi_v2' target
    $<TARGET_FILE_DIR:stapi_v2_all_runners> # The destination folder
    COMMAND ${CMAKE_COMMAND} -E copy_if_different
    $<TARGET_PDB_FILE:stapi_v2>             # The source pdb from the 'stapi_v2' target
    $<TARGET_FILE_DIR:stapi_v2_all_runners> # The destination folder
)

if (ENABLE_COVERAGE AND CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_link_options(stapi_v2_all_runners PRIVATE --coverage)
    target_link_libraries(stapi_v2_all_runners gcov)
endif()

if(UNIX)
    target_link_libraries(stapi_v2_all_runners pthread)
endif()

add_test(NAME stapi_v2_all_runners COMMAND stapi_v2_all_runners)