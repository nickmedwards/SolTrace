project(stapi_v2)

cmake_minimum_required(VERSION 3.19)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# find_package(pybind11 CONFIG REQUIRED)

include_directories(
    .
    ../simulation_data
    ../simulation_results
    ../simulation_runner/native_runner
)

set(STAPI_SRC
	stapi_v2.cpp
)

# Add header files for IDE visibility
set(STAPI_HEADERS
    stapi_v2.h
)

# Group header files for IDEs
source_group("Header Files" FILES ${CORETRACE_HEADERS})

add_library(stapi_v2 SHARED ${STAPI_SRC} ${STAPI_HEADERS})

if(SOLTRACE_BUILD_EMBREE_SUPPORT)
    target_include_directories(stapi_v2 PRIVATE
        ../simulation_runner/embree_runner
    )
    target_compile_definitions(stapi_v2 PRIVATE SOLTRACE_EMBREE_SUPPORT)
    target_link_libraries(stapi_v2 PRIVATE embree_runner)
endif()

if(SOLTRACE_BUILD_OPTIX_SUPPORT)
    target_include_directories(stapi_v2 PRIVATE
        ../simulation_runner/optix_runner
    )
    target_compile_definitions(stapi_v2 PRIVATE SOLTRACE_OPTIX_SUPPORT)
    target_link_libraries(stapi_v2 PRIVATE optix_runner)
endif()

target_link_libraries(stapi_v2 PRIVATE
    simdata
    simresult
    native_runner
)

if(UNIX)
    target_link_libraries(stapi_v2 PRIVATE pthread)
endif()

if (NOT APPLE AND ENABLE_COVERAGE)
    target_link_options(stapi_v2 PRIVATE --coverage)
    target_link_libraries(stapi_v2 PRIVATE gcov)
endif()

install(TARGETS stapi_v2
    RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
)
