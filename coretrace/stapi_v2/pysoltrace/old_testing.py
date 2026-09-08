import ctypes, unittest
from math import sin, cos, pi, sqrt
import orjson
import numpy as np


try:
    from chedder import dot_h, found_in
    import soltrace_constants as _STC
    from point import Point
    from stapi_v2 import STAPIv2, STAPIv2Exception
    from legacy import legacy
except ImportError:
    from .chedder import dot_h, found_in
    from . import soltrace_constants as _STC
    from .point import Point
    from .stapi_v2 import STAPIv2, STAPIv2Exception
    from .legacy import legacy

class STAPIv2TestCase(unittest.TestCase):
    def setUp(self):
        self.stapi = STAPIv2(testing=True)
        return super().setUp()

    def assertStructEqual(self, value, check):
        for field in value._fields_:
            self.assertEqual(getattr(value, field[0]),
                             getattr(check, field[0]))

class BatchTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        # set up dummy values
        self.sim_params = dot_h.args_simulation_parameters(1, 100, .1, 35.962278, -106.5122622, True, True, False)

        self.args_sun_buie = dot_h.args_sun(0, 2, 2, 2, .5, 'b'.encode())
        self.args_sun_user = dot_h.args_sun(3, 608, 303, 1000, 5, ' '.encode())
        self.good_angles      = [0, 1, 2]
        self.good_intensities = [0, 1, 2]
        
        self.opt_set = dot_h.args_optical_properties_set("dummy".encode(), 1.1, 1.1, 2)
        self.front   = dot_h.args_optical_properties_face(.5, .5, 5, 5, 'g'.encode())
        self.back    = dot_h.args_optical_properties_face(.25, .25, 2, 2, 'g'.encode())
        
        self.el_args = dot_h.args_element(2, 2, 2, 2, 2, 2, 2, False, True, 'c'.encode(), 'p'.encode())
        self.opt_id = 0
        self.a_params = [2]
        self.s_params = [2, 2]

    def test_simple(self):
        f = open('./sample.json', mode='rb')
        pcount = ctypes.c_uint64()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_READ_INPUT_JSON, f.read()),
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_NUM_ELEMENTS, ctypes.pointer(pcount)),
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_SETUP, dot_h.st_runner_type_t.OPTIX),
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_RUN_V2),
        ])

        f.close()
        self.assertEqual(pcount.value, 126)

    # functions for simulation data management thru json strings
    def test_call_st_read_input_json(self):
        f = open('./sample.json', mode='rb')
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_READ_INPUT_JSON, f.read())
        ])
        f.close()
        self.assertEqual(self.stapi.num_elements(), 126)

    # functions for simulation data management directly
    def test_call_st_set_simulation_parameters(self):
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SET_SIMULATION_PARAMETERS, ctypes.pointer(self.sim_params))
        ])

        rt_params = self.stapi.get_simulation_parameters()
        self.assertStructEqual(rt_params, self.sim_params)

    def test_call_st_sim_params(self):
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_PARAMS, 1, 100, True)
        ])

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'number_of_rays'), 1)
        self.assertEqual(getattr(rt_params, 'max_number_of_rays'), 100)
        self.assertEqual(getattr(rt_params, 'as_power_tower'), True)

    def test_call_st_sim_errors(self):
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_ERRORS, True, True)
        ])

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'include_sun_shape_errors'), True)
        self.assertEqual(getattr(rt_params, 'include_optical_errors'), True)

    def test_call_st_sim_location(self):
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_LOCATION, 35.962278, -106.5122622)
        ])

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'latitude'), 35.962278)
        self.assertEqual(getattr(rt_params, 'longitude'), -106.5122622)

    def test_call_st_sim_tolerance(self):
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_TOLERANCE, .1)
        ])

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'tolerance'), .1)

    # functions to add/remove/set optical properties
    def test_call_st_num_optics(self):
        pcount = ctypes.c_uint64()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_NUM_OPTICS, ctypes.pointer(pcount))
        ])
        self.assertEqual(pcount.value, 0)

        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_NUM_OPTICS, ctypes.pointer(pcount))
        ])
        self.assertEqual(pcount.value, 1)

    def test_call_st_add_optical_properies_set(self):
        pid = ctypes.c_uint64()

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_OPTICAL_PROPERIES_SET,
                                            ctypes.pointer(self.opt_set),
                                            ctypes.pointer(self.front),
                                            ctypes.pointer(self.back),
                                            ctypes.pointer(pid))
        ])

        _opt_set, _front, _back = self.stapi.get_optical_properties_set(pid.value)
        
        self.assertStructEqual(_opt_set, self.opt_set)
        self.assertStructEqual(_front, self.front)
        self.assertStructEqual(_back, self.back)

    def test_call_st_delete_optic(self):
        id = self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_DELETE_OPTIC, id)
        ])

        self.assertEqual(self.stapi.num_optics(), 0)

    def test_call_st_clear_optics(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_CLEAR_OPTICS)
        ])

        self.assertEqual(self.stapi.num_optics(), 0)

    # functions to add/remove elements
    def test_call_st_num_elements(self):
        pcount = ctypes.c_uint64()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_NUM_ELEMENTS, ctypes.pointer(pcount))
        ])
        self.assertEqual(pcount.value, 0)

        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_NUM_ELEMENTS, ctypes.pointer(pcount))
        ])
        self.assertEqual(pcount.value, 1)

    def test_call_st_add_element(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        pid = ctypes.c_uint64()
        _a_params = (ctypes.c_double * 8)(*self.a_params)
        _s_params = (ctypes.c_double * 8)(*self.s_params)
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_ELEMENT,
                                         ctypes.pointer(self.el_args),
                                         self.opt_id,
                                         _a_params,
                                         _s_params,
                                         ctypes.pointer(pid))
        ])

        args, optic_id, a_params, s_params = self.stapi.get_element(pid.value)
        
        self.assertStructEqual(args, self.el_args)
        self.assertEqual(optic_id, self.opt_id)
        self.assertEqual(a_params[0], self.a_params[0])
        self.assertEqual(s_params[0], 1 / (2 * self.s_params[0]))
        self.assertEqual(s_params[1], 1 / (2 * self.s_params[1]))

    def test_call_st_delete_element(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_DELETE_ELEMENT, id)
        ])

        self.assertEqual(self.stapi.num_elements(), 0)
    
    def test_call_st_clear_elements(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_CLEAR_ELEMENTS)
        ])

        self.assertEqual(self.stapi.num_elements(), 0)

    # functions to modify elements
    def test_call_st_element_enabled(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_ENABLED, id, True)
        ])

        args, *_ = self.stapi.get_element(id)

        self.assertEqual(getattr(args, 'enabled_flag'), True)

    def test_call_st_element_virtual(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_VIRTUAL, id, False)
        ])

        args, *_ = self.stapi.get_element(id)

        self.assertEqual(getattr(args, 'virtual_flag'), False)

    def test_call_st_element_zyx(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_XYZ, id, 4, 4, 4)
        ])

        args, *_ = self.stapi.get_element(id)

        self.assertEqual(getattr(args, 'x'), 4)
        self.assertEqual(getattr(args, 'y'), 4)
        self.assertEqual(getattr(args, 'z'), 4)

    def test_call_st_element_aim(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_AIM, id, 4, 4, 4)
        ])

        args, *_ = self.stapi.get_element(id)

        self.assertEqual(getattr(args, 'ax'), 4)
        self.assertEqual(getattr(args, 'ay'), 4)
        self.assertEqual(getattr(args, 'az'), 4)

    def test_call_st_element_zrot(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_ZROT, id, 4)
        ])

        args, *_ = self.stapi.get_element(id)

        self.assertEqual(getattr(args, 'zrot'), 4)

    def test_call_st_element_aperture(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        new_ap = 'r'.encode()
        new_params = (ctypes.c_double * 8)(*[3, 3])
        
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_APERTURE, id, new_ap, new_params)
        ])

        args, optic_id, a_params, s_params = self.stapi.get_element(id)

        self.assertEqual(getattr(args, 'ap'), new_ap)
        self.assertEqual(a_params[0], new_params[0])
        self.assertEqual(a_params[1], new_params[1])

    def test_call_st_element_surface(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        new_surf = 's'.encode()
        new_params = (ctypes.c_double * 8)(*[3])

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_SURFACE, id, new_surf, new_params)
        ])

        args, optic_id, a_params, s_params = self.stapi.get_element(id)

        self.assertEqual(getattr(args, 'surf'), new_surf)
        self.assertEqual(s_params[0], new_params[0])
        
    def test_call_st_element_optic(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)

        other_opt = dot_h.args_optical_properties_set("other".encode(), 1.1, 1.1, 0)
        other_id = self.stapi.add_optical_properties_set(other_opt, self.front, self.back)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENT_OPTIC, id, other_id)
        ])

        args, optic_id, a_params, s_params = self.stapi.get_element(id)
        self.assertEqual(optic_id, other_id)

    # sun functions
    def test_call_st_add_sun(self):
        _angle = (ctypes.c_double * len(self.good_angles))(*self.good_angles)
        _intensity = (ctypes.c_double * len(self.good_intensities))(*self.good_intensities)
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_SUN,
                                         ctypes.pointer(self.args_sun_user),
                                         _angle,
                                         _intensity)
        ])

        rt_sun_args, *_ = self.stapi.get_sun()
        print(rt_sun_args)
        # bypassing assertStructEqual because sigma is not set
        self.assertEqual(getattr(rt_sun_args, 'npoints'), 3)
        self.assertEqual(getattr(rt_sun_args, 'x'), 608)
        self.assertEqual(getattr(rt_sun_args, 'y'), 303)
        self.assertEqual(getattr(rt_sun_args, 'z'), 1000)
        self.assertEqual(getattr(rt_sun_args, 'shape'), b'd')


        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ADD_SUN,
                                            ctypes.pointer(self.args_sun_buie),
                                            ctypes.pointer(ctypes.c_double()),
                                            ctypes.pointer(ctypes.c_double()))
        ])

        rt_sun_args, *_ = self.stapi.get_sun()
        self.assertStructEqual(rt_sun_args, self.args_sun_buie)

    def test_call_st_sun_xyz(self):
        self.stapi.add_sun(self.args_sun_buie)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SUN_XYZ, 608, 303, 1000)
        ])

        rt_sun_args, *_ = self.stapi.get_sun()
        self.assertEqual(getattr(rt_sun_args, 'x'), 608)
        self.assertEqual(getattr(rt_sun_args, 'y'), 303)
        self.assertEqual(getattr(rt_sun_args, 'z'), 1000)
        
    # def test_call_st_sun_position(self):
    #     pass
    
    def test_call_st_sun_userdata(self):
        self.stapi.add_sun(self.args_sun_buie)

        _angle = (ctypes.c_double * len(self.good_angles))(*self.good_angles)
        _intensity = (ctypes.c_double * len(self.good_intensities))(*self.good_intensities)

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SUN_USERDATA, 3, _angle, _intensity)
        ])

        rt_sun_args, *_ = self.stapi.get_sun()
        self.assertEqual(getattr(rt_sun_args, 'npoints'), 3)
        self.assertEqual(getattr(rt_sun_args, 'shape'), b'd')

    # functions for SolTrace runner management
    def test_call_st_sim_setup(self):
        self.stapi.read_input_json('./sample.json')

        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_SETUP, dot_h.st_runner_type_t.NATIVE)
        ])

    def test_call_st_sim_run_v2(self):
        self.stapi.read_input_json('./sample.json')
        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_RUN_V2)
        ])

    def test_call_st_sim_report(self):
        self.stapi.read_input_json('./sample.json')
        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)
        self.stapi.sim_run_v2()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SIM_REPORT, 0)
        ])

    def set_up_run_report(self):
        self.stapi.read_input_json('./sample.json')
        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)
        self.stapi.sim_run_v2()
        self.stapi.sim_report()
        return self.stapi.num_intersections()

    # functions for SolTrace results management
    def test_call_st_write_results_csv(self):
        self.set_up_run_report()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_WRITE_RESULTS_CSV, b'./batch_sample.csv')
        ])

    # functions to get results directly
    def test_call_st_locations(self):
        n = self.set_up_run_report()
        loc_x = (ctypes.c_double * n)()
        loc_y = (ctypes.c_double * n)()
        loc_z = (ctypes.c_double * n)()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_LOCATIONS, loc_x, loc_y, loc_z)
        ])
        self.assertEqual(len(loc_x[:n]), n)
        self.assertEqual(len(loc_y[:n]), n)
        self.assertEqual(len(loc_z[:n]), n)

    def test_call_st_cosines(self):
        n = self.set_up_run_report()
        cos_x = (ctypes.c_double * n)()
        cos_y = (ctypes.c_double * n)()
        cos_z = (ctypes.c_double * n)()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_COSINES, cos_x, cos_y, cos_z)
        ])
        self.assertEqual(len(cos_x[:n]), n)
        self.assertEqual(len(cos_y[:n]), n)
        self.assertEqual(len(cos_z[:n]), n)

    def test_call_st_elementmap(self):
        n = self.set_up_run_report()
        els = (ctypes.c_uint64 * n)()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_ELEMENTMAP, els)
        ])
        self.assertEqual(len(els[:n]), n)
        
    def test_call_st_stagemap(self):
        n = self.set_up_run_report()
        stages = (ctypes.c_uint64 * n)()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_STAGEMAP, stages)
        ])
        self.assertEqual(len(stages[:n]), n)

    def test_call_st_raynumbers(self):
        n = self.set_up_run_report()
        ray_numbers = (ctypes.c_uint64 * n)()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_RAYNUMBERS, ray_numbers)
        ])
        self.assertEqual(len(ray_numbers[:n]), n)

    def test_call_st_sun_stats(self):
        self.set_up_run_report()
        width    = ctypes.c_double()
        height   = ctypes.c_double()
        area     = ctypes.c_double()
        nsunrays = ctypes.c_uint64()
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_SUN_STATS,
                                         ctypes.pointer(width),
                                         ctypes.pointer(height),
                                         ctypes.pointer(area),
                                         ctypes.pointer(nsunrays))
        ])
        self.assertGreater(width.value, 0.)
        self.assertGreater(height.value, 0.)
        self.assertGreater(area.value, 0.)
        self.assertGreater(nsunrays.value, 0)

    def test_call_st_get_results_data(self):
        n = self.set_up_run_report()
        args = dot_h.args_results_data((ctypes.c_double * n)(),
                                       (ctypes.c_double * n)(),
                                       (ctypes.c_double * n)(),
                                       (ctypes.c_double * n)(),
                                       (ctypes.c_double * n)(),
                                       (ctypes.c_double * n)(),
                                       (ctypes.c_uint64 * n)(),
                                       (ctypes.c_uint64 * n)(),
                                       (ctypes.c_uint64 * n)())
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_GET_RESULTS_DATA, ctypes.pointer(args))
        ])

        self.assertEqual(len(args.loc_x[:n]), n)
        self.assertEqual(len(args.loc_y[:n]), n)
        self.assertEqual(len(args.loc_z[:n]), n)
        self.assertEqual(len(args.cos_x[:n]), n)
        self.assertEqual(len(args.cos_y[:n]), n)
        self.assertEqual(len(args.cos_z[:n]), n)
        self.assertEqual(len(args.element_map[:n]), n)
        self.assertEqual(len(args.stage_map[:n]), n)
        self.assertEqual(len(args.ray_numbers[:n]), n)


class LegacyTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()

        self.legacy = legacy(testing = True)
        # set up dummy values
        # sun
        self.sun = self.legacy.add_sun()
        self.sun.position = Point(608, 303, 1000)
        self.sun.shape = 'b'
        self.sun.sigma = .5
        self.sun_args = dot_h.args_sun(0, 608, 303, 1000, .5, 'b'.encode())

        # optical property set
        self.opt = self.legacy.add_optic('dummy')

        # front face object (f is 6th letter)
        self.opt.front.dist_type       = 'f'
        self.opt.front.refraction_real = 1.6
        self.opt.front.reflectivity    = .6
        self.opt.front.transmissivity  = .6
        self.opt.front.slope_error     = 6
        self.opt.front.spec_error      = 6

        # back face object (b is 2nd letter)
        self.opt.back.dist_type       = 'p'
        self.opt.back.refraction_real = 1.2
        self.opt.back.reflectivity    = .2
        self.opt.back.transmissivity  = .2
        self.opt.back.slope_error     = 2
        self.opt.back.spec_error      = 2

        self.opt_args   = dot_h.args_optical_properties_set("dummy".encode(), 1.6, 1.2, 2)
        self.front_args = dot_h.args_optical_properties_face(.6, .6, 6, 6, 'f'.encode())
        self.back_args  = dot_h.args_optical_properties_face(.2, .2, 2, 2, 'p'.encode())

        # dummy element (e is 5th letter)
        self.stage = self.legacy.add_stage()
        self.el = self.stage.add_element()

        self.el.optic    = self.opt
        self.el.position = Point(5, 5, 5)
        self.el.aim      = Point(5, 5, 5)
        self.el.zrot     = 5
        self.el.aperture_circle(5)
        self.el.surface_parabolic(5, 5)

        self.el_args = dot_h.args_element(5, 5, 5, 5, 5, 5, 5, True, False, 'c'.encode(), 'p'.encode())
        self.opt_id = 0
        self.a_params = [5]
        self.s_params = [5, 5]

    def test_legacy_sun(self):
        self.sun.Create(self.stapi, _do = True)

        rt_sun_args, *_ = self.stapi.get_sun()
        self.assertStructEqual(rt_sun_args, self.sun_args)

    def test_legacy_optic(self):
        self.opt.Create(self.stapi, _do = True)

        _opt_set, _front, _back = self.stapi.get_optical_properties_set(0)
        self.assertStructEqual(_opt_set, self.opt_args)
        self.assertStructEqual(_front, self.front_args)
        self.assertStructEqual(_back, self.back_args)

    def test_legacy_element(self):
        self.opt.Create(self.stapi, _do = True)
        self.el.Create(self.stapi, _do = True)

        args, optic_id, a_params, s_params = self.stapi.get_element(1)
        
        self.assertStructEqual(args, self.el_args)
        self.assertEqual(optic_id, self.opt_id)
        self.assertEqual(a_params[0], self.a_params[0])
        self.assertEqual(s_params[0], 1 / (2 * self.s_params[0]))
        self.assertEqual(s_params[1], 1 / (2 * self.s_params[1]))

class TowerDemoTest(STAPIv2TestCase):
    def setUp(self):
        super().setUp()

    def test(self):
        PT = legacy(testing = True)
        # this object has data from previous legacy tests?
        PT.clear_optics()
        PT.clear_stages()
        # Create two optics types - one for reflector, and one for absorber.
        opt_ref = PT.add_optic("Reflector")
        opt_ref.front.reflectivity = 1.
        opt_abs = PT.add_optic("Absorber")
        opt_abs.front.reflectivity = 0.

        # Sun
        sun = PT.add_sun()
        # Give sun an arbitrary position
        sun.position.x = 1.
        sun.position.y = -1.
        sun.position.z = 99.

        # Reflector stage
        st = PT.add_stage()

        #absorber element height
        abs_pos = Point(0., 0., 10.)

        # Create a heliostat at some random x,y position, reflecting to the receiver
        for i in range(-1,2):
            hpos = [sin(i*pi/2)*5, cos(i*pi/2)*5]
            # hpos = [random.uniform(-10,10), random.uniform(-10,10)]
            el = st.add_element()
            el.optic = opt_ref
            el.position.x = hpos[0]
            el.position.y = hpos[1]
            # calculate the vectors - receiver, sun, and aim
            rvec = (abs_pos - el.position).unitize()
            svec = sun.position.unitize()
            avec = (rvec + svec)/2.
            # assign the aim vector. scale by a large number
            el.aim = el.position + avec*100.
            # compute surface z rotation to align with plane of the ground
            el.zrot = PT.util_calc_zrot_azel(avec)
            # Set surface and aperture characteristics
            el.surface_flat()
            el.aperture_rectangle(1.0,1.95)

        sta = PT.add_stage()
        # flat absorber element
        ela = sta.add_element()
        ela.position = abs_pos
        ela.aim.z = 0.
        ela.aim.x = 0.
        ela.aim.y = 5.
        ela.optic = opt_abs
        ela.surface_flat()
        ela.aperture_rectangle(2,2)  

        # set simulation parameters
        PT.num_ray_hits = 1e3
        PT.max_rays_traced = PT.num_ray_hits*100
        PT.is_sunshape = True 
        PT.is_surface_errors = True

        PT.run(-1, True, 1)

if __name__ == '__main__':
    # print(f'\n\n\n\n{found_in(dot_h)}\n\n\n\n')
    unittest.main()