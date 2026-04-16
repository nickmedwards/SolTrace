/**
 * @file main.cpp
 * @brief Command-line driver for SolTrace ray tracing.
 *
 * Reads a JSON file to configure SimulationData, runs the ray tracer,
 * and writes the ray interaction records to a CSV file.
 *
 * Usage:
 *   simdriver <input.json> <output.csv> [options]
 *
 * Options:
 *   --threads <n>   Number of parallel threads (default: 1)
 *   --rays <n>      Override the number of rays from the JSON file
 *   --embree        Use the Embree runner (only available if built with
 *                   SOLTRACE_BUILD_EMBREE_SUPPORT=ON; falls back to native
 *                   runner with a warning if Embree support is absent)
 *   --optix         Use the OptiX runner (only available if built with
 *                   SOLTRACE_BUILD_OPTIX_SUPPORT=ON; falls back to native
 *                   runner with a warning if OptiX support is absent)
 */

#include <cstdlib>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <chrono>
#include <string>

#include "native_runner.hpp"
#include "simulation_data_export.hpp"
#include "simulation_result_export.hpp"

#ifdef SOLTRACE_EMBREE_SUPPORT
#include "embree_runner.hpp"
#endif

#ifdef SOLTRACE_OPTIX_SUPPORT
#include "optix_runner.hpp"
#endif

// using SolTrace::Data::SimulationData;
// using SolTrace::Data::SimulationParameters;
using SolTrace::NativeRunner::NativeRunner;
using SolTrace::Result::SimulationResult;
using SolTrace::Runner::RunnerStatus;

static void print_usage(const char *prog)
{
    std::cerr
        << "Usage: " << prog << " <input.json> <output.csv> [options]\n"
        << "\n"
        << "Options:\n"
        << "  --threads <n>   Number of threads (default: 1)\n"
        << "  --rays <n>      Override number of rays specified in the JSON file\n"
#ifdef SOLTRACE_EMBREE_SUPPORT
        << "  --embree        Use Embree runner instead of the native runner\n"
        << "                  (requires SOLTRACE_BUILD_EMBREE_SUPPORT=ON at build time)\n"
#endif
#ifdef SOLTRACE_OPTIX_SUPPORT
        << "  --optix         Use OptiX runner instead of the native runner\n"
        << "                  (requires SOLTRACE_BUILD_OPTIX_SUPPORT=ON at build time)\n"
#endif
        ;
}

int main(int argc, char *argv[])
{
    if (argc < 3)
    {
        print_usage(argv[0]);
        return EXIT_FAILURE;
    }

    const std::string input_file = argv[1];
    const std::string output_file = argv[2];

    int num_threads = 1;
    long long num_rays_override = -1; // -1 means use what the JSON specifies
    bool use_embree = false;
    bool use_optix = false;

    for (int i = 3; i < argc; ++i)
    {
        const std::string arg = argv[i];
        if (arg == "--threads")
        {
            if (i + 1 >= argc)
            {
                std::cerr << "Error: --threads requires an argument\n";
                return EXIT_FAILURE;
            }
            try
            {
                num_threads = std::stoi(argv[++i]);
            }
            catch (...)
            {
                std::cerr << "Error: invalid thread count '" << argv[i] << "'\n";
                return EXIT_FAILURE;
            }
            if (num_threads < 1)
            {
                std::cerr << "Error: thread count must be >= 1\n";
                return EXIT_FAILURE;
            }
        }
        else if (arg == "--rays")
        {
            if (i + 1 >= argc)
            {
                std::cerr << "Error: --rays requires an argument\n";
                return EXIT_FAILURE;
            }
            try
            {
                num_rays_override = std::stoll(argv[++i]);
            }
            catch (...)
            {
                std::cerr << "Error: invalid ray count '" << argv[i] << "'\n";
                return EXIT_FAILURE;
            }
            if (num_rays_override < 1)
            {
                std::cerr << "Error: ray count must be >= 1\n";
                return EXIT_FAILURE;
            }
        }
        else if (arg == "--embree")
        {
            use_embree = true;
        }
        else if (arg == "--optix")
        {
            use_optix = true;
        }
        else
        {
            std::cerr << "Error: unknown option '" << arg << "'\n";
            print_usage(argv[0]);
            return EXIT_FAILURE;
        }
    }

    // -------------------------------------------------------------------------
    // Load simulation data from JSON
    // -------------------------------------------------------------------------
    SimulationData simData;
    try
    {
        std::cout << "Loading simulation data from: " << input_file << "...\n";
        auto t_load_start = std::chrono::steady_clock::now();
        simData.import_json_file(input_file);
        auto t_load_end = std::chrono::steady_clock::now();
        std::cout << "  Loaded in "
                  << std::chrono::duration<double>(t_load_end - t_load_start).count()
                  << " s\n";
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error loading JSON file: " << e.what() << "\n";
        return EXIT_FAILURE;
    }

    // Override ray count if the user requested it
    if (num_rays_override > 0)
    {
        SimulationParameters &params = simData.get_simulation_parameters();
        params.number_of_rays = static_cast<uint_fast64_t>(num_rays_override);
        params.max_number_of_rays = params.number_of_rays * 100;
        std::cout << "Overriding ray count to " << params.number_of_rays << "\n";
    }

    // -------------------------------------------------------------------------
    // Set up and run the simulation
    // -------------------------------------------------------------------------
    RunnerStatus sts;
    SimulationResult result;

#ifdef SOLTRACE_EMBREE_SUPPORT
    if (use_embree)
    {
        SolTrace::EmbreeRunner::EmbreeRunner runner;

        sts = runner.initialize();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: failed to initialize Embree runner\n";
            return EXIT_FAILURE;
        }

        runner.set_number_of_threads(static_cast<uint_fast64_t>(num_threads));
        std::cout << "Using Embree runner with " << num_threads << " thread(s)\n";

        std::cout << "Setting up simulation...\n";
        auto t_setup_start = std::chrono::steady_clock::now();
        runner.disable_stages();
        sts = runner.setup_simulation(&simData);
        auto t_setup_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: Embree runner setup failed\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Setup in "
                  << std::chrono::duration<double>(t_setup_end - t_setup_start).count()
                  << " s\n";

        std::cout << "Running simulation...\n";
        auto t_run_start = std::chrono::steady_clock::now();
        sts = runner.run_simulation();
        auto t_run_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: simulation failed\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Completed in "
                  << std::chrono::duration<double>(t_run_end - t_run_start).count()
                  << " s\n";

        std::cout << "Retrieving results...\n";
        auto t_report_start = std::chrono::steady_clock::now();
        sts = runner.report_simulation(&result, 0);
        auto t_report_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: failed to collect simulation results\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Retrieved in "
                  << std::chrono::duration<double>(t_report_end - t_report_start).count()
                  << " s\n";
    }
    else
#endif
#ifdef SOLTRACE_OPTIX_SUPPORT
    if (use_optix)
    {
        OptixRunner runner;

        sts = runner.initialize();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: failed to initialize OptiX runner\n";
            return EXIT_FAILURE;
        }

        std::cout << "Using OptiX runner\n";

        std::cout << "Setting up simulation...\n";
        auto t_setup_start = std::chrono::steady_clock::now();
        sts = runner.setup_simulation(&simData);
        auto t_setup_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: OptiX runner setup failed\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Setup in "
                  << std::chrono::duration<double>(t_setup_end - t_setup_start).count()
                  << " s\n";

        std::cout << "Running simulation...\n";
        auto t_run_start = std::chrono::steady_clock::now();
        sts = runner.run_simulation();
        auto t_run_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: simulation failed\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Completed in "
                  << std::chrono::duration<double>(t_run_end - t_run_start).count()
                  << " s\n";

        std::cout << "Retrieving results...\n";
        auto t_report_start = std::chrono::steady_clock::now();
        sts = runner.report_simulation(&result, 0);
        auto t_report_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: failed to collect simulation results\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Retrieved in "
                  << std::chrono::duration<double>(t_report_end - t_report_start).count()
                  << " s\n";
    }
    else
#endif
    {
#ifndef SOLTRACE_EMBREE_SUPPORT
        if (use_embree)
        {
            std::cerr << "Warning: this build does not include Embree support. "
                         "Falling back to the native runner.\n";
        }
#endif
#ifndef SOLTRACE_OPTIX_SUPPORT
        if (use_optix)
        {
            std::cerr << "Warning: this build does not include OptiX support. "
                         "Falling back to the native runner.\n";
        }
#endif

        NativeRunner runner;

        sts = runner.initialize();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: failed to initialize native runner\n";
            return EXIT_FAILURE;
        }

        runner.set_number_of_threads(static_cast<uint_fast64_t>(num_threads));
        std::cout << "Using native runner with " << num_threads << " thread(s)\n";

        std::cout << "Setting up simulation...\n";
        auto t_setup_start = std::chrono::steady_clock::now();
        sts = runner.setup_simulation(&simData);
        auto t_setup_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: native runner setup failed\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Setup in "
                  << std::chrono::duration<double>(t_setup_end - t_setup_start).count()
                  << " s\n";

        std::cout << "Running simulation...\n";
        auto t_run_start = std::chrono::steady_clock::now();
        sts = runner.run_simulation();
        auto t_run_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: simulation failed\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Completed in "
                  << std::chrono::duration<double>(t_run_end - t_run_start).count()
                  << " s\n";

        std::cout << "Retrieving results...\n";
        auto t_report_start = std::chrono::steady_clock::now();
        sts = runner.report_simulation(&result, 0);
        auto t_report_end = std::chrono::steady_clock::now();
        if (sts != RunnerStatus::SUCCESS)
        {
            std::cerr << "Error: failed to collect simulation results\n";
            return EXIT_FAILURE;
        }
        std::cout << "  Retrieved in "
                  << std::chrono::duration<double>(t_report_end - t_report_start).count()
                  << " s\n";
    }

    // -------------------------------------------------------------------------
    // Write results to CSV
    // -------------------------------------------------------------------------
    std::cout << "Writing " << result.get_number_of_records()
              << " ray records to: " << output_file << "...\n";
    try
    {
        auto t_write_start = std::chrono::steady_clock::now();
        result.write_csv_file(output_file);
        auto t_write_end = std::chrono::steady_clock::now();
        std::cout << "  Written in "
                  << std::chrono::duration<double>(t_write_end - t_write_start).count()
                  << " s\n";
    }
    catch (const std::exception &e)
    {
        std::cerr << "Error writing CSV file: " << e.what() << "\n";
        return EXIT_FAILURE;
    }

    std::cout << "Done.\n";
    return EXIT_SUCCESS;
}
