#include <vector>
#include <gtest/gtest.h>
#include <string>

#include <optix_runner.hpp>
#include <simulation_data.hpp>
#include <simulation_data_export.hpp>
#include <simulation_result_export.hpp>

using SolTrace::Runner::RunnerStatus;

void make_two_plate_sd(SimulationData& sd, element_ptr& plate1, element_ptr& plate2)
{
	sd.clear();

	// Sun directly overhead
	auto sun = make_ray_source<Sun>();
	sun->set_position(0, 0, 100);
	sd.add_ray_source(sun);

	// Make stage
	auto stage = make_stage(0);
	stage->set_origin(0, 0, 0);
	stage->set_aim_vector(0, 0, 1);
	stage->set_name("stage");

	// Plate 1: Angled 45 degrees, receives rays from sun and reflects toward plate 2
	// Position at origin, tilted to reflect rays in +Y direction
	plate1 = make_element<SingleElement>();
	plate1->set_origin(0, 0, 50);
	plate1->set_aim_vector(0, 50, 100);  // Tilted 45 degrees toward +Y
	plate1->set_surface(make_surface<Flat>());
	plate1->set_aperture(make_aperture<Rectangle>(5, 5));
	plate1->get_front_optical_properties()->set_ideal_reflection();
	plate1->get_back_optical_properties()->set_ideal_reflection();
	plate1->set_name("plate1");

	// Plate 2: Positioned to receive reflected rays from plate 1
	// At Y=50, tilted 45 degrees to face plate 1
	plate2 = make_element<SingleElement>();
	plate2->set_origin(0, 50, 50);
	plate2->set_aim_vector(0, 0, 100);  // Tilted 45 degrees toward -Y (facing plate 1)
	plate2->set_surface(make_surface<Flat>());
	plate2->set_aperture(make_aperture<Rectangle>(10, 10));  // Larger to catch reflected rays
	plate2->get_front_optical_properties()->set_ideal_absorption();
	plate2->get_back_optical_properties()->set_ideal_absorption();
	plate2->set_name("plate2");

	// Add elements to stage
	stage->add_element(plate1);
	stage->add_element(plate2);

	// Add stage to sd
	sd.add_stage(stage);

	// Set parameters
	SimulationParameters& params = sd.get_simulation_parameters();
	params.number_of_rays = 10000;
	params.max_number_of_rays = params.number_of_rays * 100;
	params.include_optical_errors = false;
	params.include_sun_shape_errors = false;
	params.seed = 123;
}

void count_hits_two_plate(const SimulationResult& result,
	int plate1_id, int plate2_id,
	int& absorbed_plate1, int& transmitted_plate1, int& reflected_plate1,
	int& absorbed_plate2, int& transmitted_plate2, int& reflected_plate2,
	int& absorbed_total, int& transmitted_total, int& reflected_total)
{
	absorbed_plate1 = transmitted_plate1 = reflected_plate1 = 0;
	absorbed_plate2 = transmitted_plate2 = reflected_plate2 = 0;
	absorbed_total = transmitted_total = reflected_total = 0;

	int n_records = result.get_number_of_records();
	for (int i = 0; i < n_records; i++)
	{
		ray_record_ptr rec = result[i];
		int n_interactions = rec->get_number_of_interactions();
		for (int j = 0; j < n_interactions; j++)
		{
			RayEvent rev = rec->get_event(j);
			int elid = static_cast<int>(rec->get_element(j));

			// Totals
			if (rev == RayEvent::ABSORB) absorbed_total++;
			else if (rev == RayEvent::TRANSMIT) transmitted_total++;
			else if (rev == RayEvent::REFLECT) reflected_total++;

			// Per-plate
			if (elid == plate1_id)
			{
				if (rev == RayEvent::ABSORB) absorbed_plate1++;
				else if (rev == RayEvent::TRANSMIT) transmitted_plate1++;
				else if (rev == RayEvent::REFLECT) reflected_plate1++;
			}
			else if (elid == plate2_id)
			{
				if (rev == RayEvent::ABSORB) absorbed_plate2++;
				else if (rev == RayEvent::TRANSMIT) transmitted_plate2++;
				else if (rev == RayEvent::REFLECT) reflected_plate2++;
			}
		}
	}
}

TEST(TwoPlateOptix, ReflectionToAbsorber)
{
	// Make two-plate simulation data
	SimulationData sd;
	element_ptr plate1, plate2;
	make_two_plate_sd(sd, plate1, plate2);

	// Run simulation
	OptixRunner runner;
	RunnerStatus sts = runner.initialize();
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);
	sts = runner.setup_simulation(&sd);
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);
	sts = runner.run_simulation();
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);

	// Collect results
	SimulationResult result;
	sts = runner.report_simulation(&result, 0);
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);

	// Count events per-plate and totals
	int a1, t1, r1, a2, t2, r2, at, tt, rt;
	count_hits_two_plate(result, plate1->get_id(), plate2->get_id(), a1, t1, r1, a2, t2, r2, at, tt, rt);

	// Check number of hits
	EXPECT_EQ(sd.get_simulation_parameters().number_of_rays, result.get_number_of_records());

	// Rays should reflect off plate1 and be absorbed by plate2
	EXPECT_EQ(a1, 0);	// plate1 is ideal reflective
	EXPECT_EQ(r2, 0);	// plate2 is ideal absorptive
	EXPECT_GT(r1, 0);
	EXPECT_GT(a2, 0);

	// All the rays hit something
	EXPECT_GT(rt + at, sd.get_simulation_parameters().number_of_rays);

	// More absorptions than reflections
	EXPECT_GT(at, rt);

	// Sun Ray Checks
	int N_sun_rays = runner.get_N_sun_rays();
	OptixCSP::SolTraceSystem* sys = runner.get_optix_system();
	
	std::vector<float4> hp_vec;
	std::vector<uint_fast64_t> raynumber_vec;
	std::vector<int32_t> element_id_vec;
	std::vector<uint8_t> hit_type_vec;
	sys->get_hp_output(hp_vec, raynumber_vec, element_id_vec, hit_type_vec);
	std::vector<uint_fast64_t> sunraynumber_vec = sys->get_sunraynumber_vec();

	EXPECT_EQ(hp_vec.size(), raynumber_vec.size());						// Hit results are same size
	EXPECT_EQ(raynumber_vec.size(), element_id_vec.size());
	EXPECT_EQ(element_id_vec.size(), hit_type_vec.size());
	EXPECT_EQ(N_sun_rays, sunraynumber_vec.back());						// Reported sun rays is the sun ray id of last hit
	EXPECT_TRUE(N_sun_rays <= sd.get_simulation_parameters().max_number_of_rays);	// Only generated max number of rays or fewer
}

TEST(TwoPlateOptix, BatchMaxRayLimit)
{
	// Make two-plate simulation data
	SimulationData sd;
	element_ptr plate1, plate2;
	make_two_plate_sd(sd, plate1, plate2);

	// Set max rays equal to desired
	int NRays = 1000;
	int NMaxRays = NRays;
	auto& sim_par = sd.get_simulation_parameters();
	sim_par.number_of_rays = NRays;
	sim_par.max_number_of_rays = NMaxRays;

	// Run simulation
	OptixRunner runner;
	RunnerStatus sts = runner.initialize();
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);
	sts = runner.setup_simulation(&sd);
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);
	sts = runner.run_simulation();
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);

	// Collect results
	SimulationResult result;
	sts = runner.report_simulation(&result, 0);
	EXPECT_EQ(sts, RunnerStatus::SUCCESS);

	// Should NOT reach desired number of rays
	ASSERT_TRUE(result.get_number_of_records() < NRays);
}

TEST(TwoPlateOptix, SimResults)
{
	// Make two-plate simulation data
	SimulationData sd;
	element_ptr plate1, plate2;
	make_two_plate_sd(sd, plate1, plate2);

	// Run simulation
	OptixRunner runner;
	RunnerStatus sts = runner.initialize();
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);
	sts = runner.setup_simulation(&sd);
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);
	sts = runner.run_simulation();
	ASSERT_EQ(sts, RunnerStatus::SUCCESS);

	// Collect results
	SimulationResult result;
	sts = runner.report_simulation(&result, 0);
	EXPECT_EQ(sts, RunnerStatus::SUCCESS);
	int n_records = result.get_number_of_records();

	// Check sim result order
	for (int i = 0; i < n_records; i++)
	{
		ray_record_ptr rec = result[i];

		int n_interactions = rec->get_number_of_interactions();
		RayEvent prev_rev = RayEvent::UNKNOWN;
		for (int j = 0; j < n_interactions; j++)
		{
			RayEvent rev = rec->get_event(j);
			
			// Check that ray event is assigned
			ASSERT_FALSE(rev == RayEvent::UNKNOWN);

			// Check that first interaction is create
			if (j == 0)
				ASSERT_TRUE(rev == RayEvent::CREATE);
			if (rev == RayEvent::CREATE)
				ASSERT_TRUE(j == 0);

			// Check that nothing happens after absorb or exit
			if (j > 0)
			{
				ASSERT_FALSE(prev_rev == RayEvent::ABSORB);
				ASSERT_FALSE(prev_rev == RayEvent::EXIT);
			}

			prev_rev = rev;
		}
	}
	
}
  ///////////////////////////////////
 // first attempts at NSTTF tests //
///////////////////////////////////

/*
sun
0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35, 1.5, 1.65, 1.8, 1.95, 2.1, 2.25, 2.4, 2.55, 2.7, 2.85, 3, 3.15, 3.3, 3.45, 3.6, 3.75, 3.9, 4.05, 4.2, 4.35, 4.5, 4.65, 4.8, 4.95, 5.1, 5.25, 5.4, 5.55, 5.7, 5.85, 6, 6.15, 6.3, 6.45, 6.6, 6.75, 6.9, 7.05, 7.2, 7.35, 7.5, 7.65, 7.8, 7.95
1, 0.999872, 0.999485, 0.998837, 0.997923, 0.996734, 0.99526, 0.993487, 0.991399, 0.988976, 0.986193, 0.983019, 0.979417, 0.975345, 0.970747, 0.965558, 0.959697, 0.953063, 0.945528, 0.936933, 0.927069, 0.915665, 0.902358, 0.886653, 0.867855, 0.844965, 0.816477, 0.78003, 0.731687, 0.66436, 0.563875, 0.397159, 5.34414e-05, 5.07222e-05, 4.82164e-05, 4.59018e-05, 4.37589e-05, 4.17708e-05, 3.99224e-05, 3.82007e-05, 3.65941e-05, 3.50923e-05, 3.36861e-05, 3.23674e-05, 3.11289e-05, 2.9964e-05, 2.88669e-05, 2.78323e-05, 2.68554e-05, 2.59319e-05, 2.50579e-05, 2.42298e-05, 2.34443e-05, 2.26985e-05

picked near left (2), mid right (150), far center (212)
ground plane is x-z

    x		   y		   z		 aim x		 aim y		  aim z		   retangular		     parabolic					name
-81.9557  	11.2769		61.0378		444.267		642.662		-508.728 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 1
-83.0617  	11.2769		59.9892		447.184		642.662		-505.962 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 2
-83.9833  	11.2769		59.1153		449.616		642.662		-503.656 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 3
-84.905  	11.2769		58.2414		452.047		642.662		-501.351 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 4
-86.0109  	11.2769		57.1928		454.965		642.662		-498.585 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 5
-81.3977  	10.2995		60.4492		442.795		645.241		-507.175 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 6
-82.5036  	10.2995		59.4006		445.712		645.241		-504.409 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 7
-83.4253  	10.2995		58.5267		448.144		645.241		-502.104 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 8
-84.347  	10.2995		57.6528		450.575		645.241		-499.798 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 9
-85.4529  	10.2995		56.6043		453.493		645.241		-497.032 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 10
-80.8224  	9.31		59.8425		441.299		647.878		-505.598 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 11
-81.9283  	9.31		58.7939		444.217		647.878		-502.832 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 12
-82.85  	9.31		57.92		446.648		647.878		-500.526 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 13
-83.7717  	9.31		57.0461		449.08		647.878		-498.221 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 14
-84.8776  	9.31		55.9975		451.997		647.878		-495.455 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 15
-80.2594  	8.30571		59.2487		439.792		650.501		-504.008 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 16
-81.3653  	8.30571		58.2001		442.709		650.501		-501.242 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 17
-82.287  	8.30571		57.3262		445.141		650.501		-498.936 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 18
-83.2086  	8.30571		56.4523		447.572		650.501		-496.631 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 19
-84.3146  	8.30571		55.4037		450.49		650.501		-493.865 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 20
-79.7014  	7.32828		58.6601		438.32		653.079		-502.455 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 21
-80.8073  	7.32828		57.6115		441.237		653.079		-499.689 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 22
-81.7289  	7.32828		56.7376		443.669		653.079		-497.384 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 23
-82.6506  	7.32828		55.8638		446.1		653.079		-495.078 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 24
-83.7565  	7.32828		54.8152		449.017		653.079		-492.312 ... 1.2192	1.2192 ... 0.0036381	0.0036381 ... Heliostat 2, Facet 25

134.775		7.60946		137.2		-183.48		583.231		-616.132 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 1
133.365		7.60946		137.778		-180.566	583.231		-617.327 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 2
132.19		7.60946		138.26		-178.138	583.231		-618.323 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 3
131.015		7.60946		138.742		-175.71		583.231		-619.319 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 4
129.605		7.60946		139.321		-172.796	583.231		-620.514 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 5
134.495		6.57665		136.516		-182.901	585.365		-614.718 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 6
133.085		6.57665		137.094		-179.987	585.365		-615.913 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 7
131.91		6.57665		137.576		-177.558	585.365		-616.91  ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 8
130.735		6.57665		138.058		-175.13		585.365		-617.906 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 9
129.325		6.57665		138.637		-172.216	585.365		-619.101 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 10
134.205		5.53		135.81		-182.313	587.549		-613.285 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 11
132.795		5.53		136.388		-179.399	587.549		-614.481 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 12
131.62		5.53		136.87		-176.971	587.549		-615.477 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 13
130.445		5.53		137.352		-174.542	587.549		-616.473 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 14
129.035		5.53		137.93		-171.628	587.549		-617.668 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 15
133.923		4.46987		135.121		-181.718	589.719		-611.835 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 16
132.513		4.46987		135.699		-178.804	589.719		-613.03  ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 17
131.337		4.46987		136.181		-176.376	589.719		-614.026 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 18
130.162		4.46987		136.663		-173.947	589.719		-615.023 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 19
128.752		4.46987		137.241		-171.033	589.719		-616.218 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 20
133.642		3.43706		134.437		-181.138	591.854		-610.422 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 21
132.232		3.43706		135.015		-178.224	591.854		-611.617 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 22
131.057		3.43706		135.497		-175.796	591.854		-612.613 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 23
129.882		3.43706		135.979		-173.368	591.854		-613.609 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 24
128.472		3.43706		136.558		-170.454	591.854		-614.804 ... 1.2192	1.2192 ... 0.0030666	0.0030666 ... Heliostat 150, Facet 25

-2.35416	10.9087		196.56		115.429		548.023		-638.742 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 1
-3.86137	10.9087		196.334		117.776		548.023		-638.391 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 2
-5.11748	10.9087		196.146		119.732		548.023		-638.098 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 3
-6.3736		10.9087		195.958		121.689		548.023		-637.805 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 4
-7.88081	10.9087		195.733		124.036		548.023		-637.454 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 5
-2.25215	9.84182		195.878		115.27		549.685		-637.68  ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 6
-3.75936	9.84182		195.653		117.617		549.685		-637.329 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 7
-5.01548	9.84182		195.465		119.574		549.685		-637.036 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 8
-6.27159	9.84182		195.277		121.53		549.685		-636.744 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 9
-7.77881	9.84182		195.051		123.877		549.685		-636.392 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 10
-2.14667	8.76		195.174		115.109		551.386		-636.607 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 11
-3.65389	8.76		194.948		117.457		551.386		-636.256 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 12
-4.91		8.76		194.76		119.413		551.386		-635.963 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 13
-6.16611	8.76		194.572		121.369		551.386		-635.671 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 14
-7.67333	8.76		194.346		123.717		551.386		-635.319 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 15
-2.04407	7.66561		194.488		114.946		553.074		-635.515 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 16
-3.55129	7.66561		194.262		117.293		553.074		-635.164 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 17
-4.8074		7.66561		194.074		119.25		553.074		-634.871 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 18
-6.06352	7.66561		193.886		121.206		553.074		-634.578 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 19
-7.57073	7.66561		193.661		123.553		553.074		-634.227 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 20
-1.94207	6.59876		193.806		114.787		554.736		-634.454 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 21
-3.44928	6.59876		193.581		117.134		554.736		-634.102 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 22
-4.7054		6.59876		193.393		119.091		554.736		-633.809 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 23
-5.96151	6.59876		193.205		121.047		554.736		-633.517 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 24
-7.46872	6.59876		192.979		123.394		554.736		-633.165 ... 1.2192	1.2192 ... 0.0025574	0.0025574 ... Heliostat 212, Facet 25


0			30.05		0			0			30.05		1		 ... 10		60.1   ... 0			0		  ... tower	2	tower

receiver
-5.65		64.54		4.25		-5.65		64.54		100		 ... 2		2	   ... 0			0		  ... solar 1 flux target	2	
*/

/*
void make_NSTTF_sun(SimulationData& sd)
{
	std::vector<double> angles = {
		0,   0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.05, 1.2, 1.35,
		1.5, 1.65, 1.8, 1.95, 2.1, 2.25, 2.4, 2.55, 2.7, 2.85, 
		3,   3.15, 3.3, 3.45, 3.6, 3.75, 3.9, 4.05, 4.2, 4.35, 
		4.5, 4.65, 4.8, 4.95, 5.1, 5.25, 5.4, 5.55, 5.7, 5.85,
		6,   6.15, 6.3, 6.45, 6.6, 6.75, 6.9, 7.05, 7.2, 7.35, 
		7.5, 7.65, 7.8, 7.95
	};

	std::vector<double> intensities = {
		1, 0.999872, 0.999485, 0.998837, 0.997923, 0.996734, 
		0.99526, 0.993487, 0.991399, 0.988976, 0.986193, 
		0.983019, 0.979417, 0.975345, 0.970747, 0.965558, 
		0.959697, 0.953063, 0.945528, 0.936933, 0.927069, 
		0.915665, 0.902358, 0.886653, 0.867855, 0.844965, 
		0.816477, 0.78003, 0.731687, 0.66436, 0.563875, 
		0.397159, 5.34414e-05, 5.07222e-05, 4.82164e-05, 
		4.59018e-05, 4.37589e-05, 4.17708e-05, 3.99224e-05, 
		3.82007e-05, 3.65941e-05, 3.50923e-05, 3.36861e-05, 
		3.23674e-05, 3.11289e-05, 2.9964e-05, 2.88669e-05, 
		2.78323e-05, 2.68554e-05, 2.59319e-05, 2.50579e-05, 
		2.42298e-05, 2.34443e-05, 2.26985e-05
	};

	// Sun directly overhead
	auto sun = make_ray_source<Sun>();
	sun->set_position(0, 815.495, -578.764);
	sun->set_shape(SunShape::USER_DEFINED, 0, 0, 0, angles, intensities);
	sd.add_ray_source(sun);
}

stage_ptr make_NSTTF_stage(SimulationData& sd) {
	// Make stage
	auto stage = make_stage(0);
	stage->set_origin(0, 0, 0);
	stage->set_aim_vector(0, 0, 1);
	stage->set_name("stage");

	return stage;
}

std::vector<element_ptr> make_NSTTF_heliostats(SimulationData& sd, stage_ptr& stage) {
	const std::vector<std::string> names = {
		"Heliostat 2, Facet 1",
		"Heliostat 2, Facet 2",
		"Heliostat 2, Facet 3",
		"Heliostat 2, Facet 4",
		"Heliostat 2, Facet 5",
		"Heliostat 2, Facet 6",
		"Heliostat 2, Facet 7",
		"Heliostat 2, Facet 8",
		"Heliostat 2, Facet 9",
		"Heliostat 2, Facet 10",
		"Heliostat 2, Facet 11",
		"Heliostat 2, Facet 12",
		"Heliostat 2, Facet 13",
		"Heliostat 2, Facet 14",
		"Heliostat 2, Facet 15",
		"Heliostat 2, Facet 16",
		"Heliostat 2, Facet 17",
		"Heliostat 2, Facet 18",
		"Heliostat 2, Facet 19",
		"Heliostat 2, Facet 20",
		"Heliostat 2, Facet 21",
		"Heliostat 2, Facet 22",
		"Heliostat 2, Facet 23",
		"Heliostat 2, Facet 24",
		"Heliostat 2, Facet 25",
		"Heliostat 150, Facet 1",
		"Heliostat 150, Facet 2",
		"Heliostat 150, Facet 3",
		"Heliostat 150, Facet 4",
		"Heliostat 150, Facet 5",
		"Heliostat 150, Facet 6",
		"Heliostat 150, Facet 7",
		"Heliostat 150, Facet 8",
		"Heliostat 150, Facet 9",
		"Heliostat 150, Facet 10",
		"Heliostat 150, Facet 11",
		"Heliostat 150, Facet 12",
		"Heliostat 150, Facet 13",
		"Heliostat 150, Facet 14",
		"Heliostat 150, Facet 15",
		"Heliostat 150, Facet 16",
		"Heliostat 150, Facet 17",
		"Heliostat 150, Facet 18",
		"Heliostat 150, Facet 19",
		"Heliostat 150, Facet 20",
		"Heliostat 150, Facet 21",
		"Heliostat 150, Facet 22",
		"Heliostat 150, Facet 23",
		"Heliostat 150, Facet 24",
		"Heliostat 150, Facet 25",
		"Heliostat 212, Facet 1",
		"Heliostat 212, Facet 2",
		"Heliostat 212, Facet 3",
		"Heliostat 212, Facet 4",
		"Heliostat 212, Facet 5",
		"Heliostat 212, Facet 6",
		"Heliostat 212, Facet 7",
		"Heliostat 212, Facet 8",
		"Heliostat 212, Facet 9",
		"Heliostat 212, Facet 10",
		"Heliostat 212, Facet 11",
		"Heliostat 212, Facet 12",
		"Heliostat 212, Facet 13",
		"Heliostat 212, Facet 14",
		"Heliostat 212, Facet 15",
		"Heliostat 212, Facet 16",
		"Heliostat 212, Facet 17",
		"Heliostat 212, Facet 18",
		"Heliostat 212, Facet 19",
		"Heliostat 212, Facet 20",
		"Heliostat 212, Facet 21",
		"Heliostat 212, Facet 22",
		"Heliostat 212, Facet 23",
		"Heliostat 212, Facet 24",
		"Heliostat 212, Facet 25",
	};

	const std::vector<std::vector<double>> geometries = {
		//   x		   y		   z		 aim x		 aim y		  aim z		   rectagular     parabolic
		{-81.9557, 	11.2769, 	61.0378, 	444.267,	642.662,	-508.728,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-83.0617, 	11.2769, 	59.9892, 	447.184,	642.662,	-505.962,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-83.9833, 	11.2769, 	59.1153, 	449.616,	642.662,	-503.656,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-84.905, 	11.2769, 	58.2414, 	452.047,	642.662,	-501.351,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-86.0109, 	11.2769, 	57.1928, 	454.965,	642.662,	-498.585,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-81.3977, 	10.2995, 	60.4492, 	442.795,	645.241,	-507.175,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-82.5036, 	10.2995, 	59.4006, 	445.712,	645.241,	-504.409,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-83.4253, 	10.2995, 	58.5267, 	448.144,	645.241,	-502.104,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-84.347, 	10.2995, 	57.6528, 	450.575,	645.241,	-499.798,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-85.4529, 	10.2995, 	56.6043, 	453.493,	645.241,	-497.032,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-80.8224, 	9.31,		59.8425, 	441.299,	647.878,	-505.598,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-81.9283, 	9.31,		58.7939, 	444.217,	647.878,	-502.832,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-82.85, 	9.31,		57.92, 		446.648,	647.878,	-500.526,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-83.7717, 	9.31,		57.0461, 	449.08,	 	647.878,	-498.221,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-84.8776, 	9.31,		55.9975, 	451.997,	647.878,	-495.455,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-80.2594, 	8.30571,	59.2487, 	439.792,	650.501,	-504.008,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-81.3653, 	8.30571,	58.2001, 	442.709,	650.501,	-501.242,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-82.287, 	8.30571,	57.3262, 	445.141,	650.501,	-498.936,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-83.2086, 	8.30571,	56.4523, 	447.572,	650.501,	-496.631,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-84.3146, 	8.30571,	55.4037, 	450.49,	 	650.501,	-493.865,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-79.7014, 	7.32828,	58.6601, 	438.32,	 	653.079,	-502.455,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-80.8073, 	7.32828,	57.6115, 	441.237,	653.079,	-499.689,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-81.7289, 	7.32828,	56.7376, 	443.669,	653.079,	-497.384,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-82.6506, 	7.32828,	55.8638, 	446.1, 		653.079,	-495.078,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{-83.7565, 	7.32828,	54.8152, 	449.017,	653.079,	-492.312,	1.2192,	1.2192,	0.0036381, 0.0036381},
		{134.775, 	7.60946,	137.2, 		-183.48,	583.231,	-616.132,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{133.365, 	7.60946,	137.778, 	-180.566,	583.231,	-617.327,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{132.19, 	7.60946,	138.26, 	-178.138,	583.231,	-618.323,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{131.015, 	7.60946,	138.742, 	-175.71,	583.231,	-619.319,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{129.605, 	7.60946,	139.321, 	-172.796,	583.231,	-620.514,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{134.495, 	6.57665,	136.516, 	-182.901,	585.365,	-614.718,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{133.085, 	6.57665,	137.094, 	-179.987,	585.365,	-615.913,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{131.91, 	6.57665,	137.576, 	-177.558,	585.365,	-616.91,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{130.735, 	6.57665,	138.058, 	-175.13,	585.365,	-617.906,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{129.325, 	6.57665,	138.637, 	-172.216,	585.365,	-619.101,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{134.205, 	5.53,		135.81, 	-182.313,	587.549,	-613.285,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{132.795, 	5.53,		136.388,	-179.399,	587.549,	-614.481,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{131.62, 	5.53,		136.87, 	-176.971,	587.549,	-615.477,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{130.445, 	5.53,		137.352,	-174.542,	587.549,	-616.473,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{129.035, 	5.53,		137.93, 	-171.628,	587.549,	-617.668,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{133.923, 	4.46987,	135.121,	-181.718,	589.719,	-611.835,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{132.513, 	4.46987,	135.699, 	-178.804,	589.719,	-613.03,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{131.337, 	4.46987,	136.181, 	-176.376,	589.719,	-614.026,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{130.162, 	4.46987,	136.663, 	-173.947,	589.719,	-615.023,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{128.752, 	4.46987,	137.241, 	-171.033,	589.719,	-616.218,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{133.642, 	3.43706,	134.437, 	-181.138,	591.854,	-610.422,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{132.232, 	3.43706,	135.015, 	-178.224,	591.854,	-611.617,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{131.057, 	3.43706,	135.497, 	-175.796,	591.854,	-612.613,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{129.882, 	3.43706,	135.979, 	-173.368,	591.854,	-613.609,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{128.472, 	3.43706,	136.558, 	-170.454,	591.854,	-614.804,	1.2192,	1.2192,	0.0030666, 0.0030666},
		{-2.35416, 	10.9087,	196.56, 	115.429,	548.023,	-638.742,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-3.86137, 	10.9087,	196.334, 	117.776,	548.023,	-638.391,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-5.11748, 	10.9087,	196.146, 	119.732,	548.023,	-638.098,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-6.3736, 	10.9087,	195.958, 	121.689,	548.023,	-637.805,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-7.88081, 	10.9087,	195.733, 	124.036,	548.023,	-637.454,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-2.25215, 	9.84182,	195.878, 	115.27,	 	549.685,	-637.68,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-3.75936, 	9.84182,	195.653, 	117.617,	549.685,	-637.329,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-5.01548, 	9.84182,	195.465, 	119.574,	549.685,	-637.036,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-6.27159, 	9.84182,	195.277, 	121.53,	 	549.685,	-636.744,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-7.77881, 	9.84182,	195.051, 	123.877,	549.685,	-636.392,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-2.14667, 	8.76,		195.174, 	115.109,	551.386,	-636.607,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-3.65389, 	8.76,		194.948, 	117.457,	551.386,	-636.256,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-4.91, 	8.76,		194.76, 	119.413,	551.386,	-635.963,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-6.16611, 	8.76,		194.572, 	121.369,	551.386,	-635.671,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-7.67333, 	8.76,		194.346, 	123.717,	551.386,	-635.319,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-2.04407, 	7.66561,	194.488, 	114.946,	553.074,	-635.515,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-3.55129, 	7.66561,	194.262, 	117.293,	553.074,	-635.164,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-4.8074, 	7.66561,	194.074, 	119.25,	 	553.074,	-634.871,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-6.06352, 	7.66561,	193.886, 	121.206,	553.074,	-634.578,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-7.57073, 	7.66561,	193.661, 	123.553,	553.074,	-634.227,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-1.94207, 	6.59876,	193.806, 	114.787,	554.736,	-634.454,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-3.44928, 	6.59876,	193.581, 	117.134,	554.736,	-634.102,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-4.7054, 	6.59876,	193.393, 	119.091,	554.736,	-633.809,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-5.96151, 	6.59876,	193.205, 	121.047,	554.736,	-633.517,	1.2192,	1.2192,	0.0025574, 0.0025574},
		{-7.46872, 	6.59876,	192.979, 	123.394,	554.736,	-633.165,	1.2192,	1.2192,	0.0025574, 0.0025574},
	};

	std::vector<element_ptr> elements(names.size());

	for (int i = 0; i < names.size(); i++) {
		element_ptr el = make_element<SingleElement>();
		std::vector<double> temp_geometry = geometries[i];

		el->set_origin(temp_geometry[0], temp_geometry[1], temp_geometry[2]);
		el->set_aim_vector(temp_geometry[3], temp_geometry[4], temp_geometry[5]);
		el->set_surface(make_surface<Flat>());
		el->set_aperture(make_aperture<Rectangle>(5, 5));
		el->get_front_optical_properties()->set_ideal_reflection();
		el->get_back_optical_properties()->set_ideal_reflection();
		el->set_name("plate1");
	}
}

void make_NSTTF(SimulationData& sd) {
	sd.clear();
	make_NSTTF_sun(sd);
	stage_ptr stage = make_NSTTF_stage(sd);
	int test = 0;
}
*/

TEST(TwoPlateOptix, NSTTF_test)
{
	SimulationData sd;
	RunnerStatus sts;

	// std::string fname = 

	sd.import_json_file("C:\\Users\\nicke\\Desktop\\esolab\\NSTTF_heliostat_scripting\\json\\test_NSTTF.json");
	// make_NSTTF(sd);
	OptixRunner runner;

	sts = runner.initialize();
	if (sts != RunnerStatus::SUCCESS)
	{
		std::cerr << "Error: failed to initialize OptiX runner\n";
	}
	sts = runner.setup_simulation(&sd);
	if (sts != RunnerStatus::SUCCESS)
	{
		std::cerr << "Error: Embree runner setup failed\n";
	}
}