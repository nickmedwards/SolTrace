import ctypes, unittest

import orjson

try:
    from chedder import dot_h, found_in
    # import soltrace_constants as _STC
    from stapi_v2 import STAPIv2, STAPIv2Exception
except ImportError:
    from .chedder import dot_h, found_in
    # from . import soltrace_constants as _STC
    from .stapi_v2 import STAPIv2, STAPIv2Exception

class STAPIv2TestCase(unittest.TestCase):
    def setUp(self):
        self.stapi = STAPIv2(testing=True)
        return super().setUp()

    def assertStructEqual(self, value, check):
        for field in value._fields_:
            self.assertEqual(getattr(value, field[0]),
                             getattr(check, field[0]))

class JSONTests(STAPIv2TestCase):
    def test_read_from_filename(self):
        self.stapi.read_input_json('./sample.json')
        count = self.stapi.num_elements()
        self.assertEqual(count, 126)

        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.read_input_json('./errors.json')
        self.assertEqual(ex.exception.code, dot_h.st_return_code.EXCEPTION)

    def test_read_from_dict(self):
        f = open('./sample.json', mode='rb')
        _json = orjson.loads(f.read())
        f.close()
        self.stapi.read_input_json(_json)
        count = self.stapi.num_elements()
        self.assertEqual(count, 126)

        with self.assertRaises(STAPIv2Exception) as ex:
            f = open('./errors.json', mode='rb')
            _json = orjson.loads(f.read())
            f.close()
            self.stapi.read_input_json(_json)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.EXCEPTION)

class OpticalPropertiesSetTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        self.opt_set = dot_h.args_optical_properties_set("test".encode(), 1.1, 1.1, 2)
        self.front   = dot_h.args_optical_properties_face(.5, .5, 5, 5, 'g'.encode())
        self.back    = dot_h.args_optical_properties_face(.25, .25, 2, 2, 'g'.encode())

    def test_add_optical_properties_set(self):
        optical_id = self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        self.assertEqual(optical_id, 0)

        with self.assertRaises(STAPIv2Exception) as ex:
            bad_front = dot_h.args_optical_properties_face(.5, .5, 5, 5, 'z'.encode())
            self.stapi.add_optical_properties_set(self.opt_set, bad_front, self.back)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)

        with self.assertRaises(STAPIv2Exception) as ex:
            bad_back = dot_h.args_optical_properties_face(.25, .25, 2, 2, 'z'.encode())
            self.stapi.add_optical_properties_set(self.opt_set, self.front, bad_back)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)

    def test_get_optical_properties_set(self):
        optical_id = self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        self.assertEqual(optical_id, 0)

        _opt_set, _front, _back = self.stapi.get_optical_properties_set(optical_id)

        self.assertStructEqual(_opt_set, self.opt_set)
        self.assertStructEqual(_front, self.front)
        self.assertStructEqual(_back, self.back)

        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.get_optical_properties_set(optical_id + 1)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.DATA_VALUE_NOT_FOUND)

    def test_delete_optic(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)

        self.assertEqual(self.stapi.num_optics(), 2)

        with self.assertWarns(UserWarning):
            self.stapi.delete_optic(2)

        self.stapi.delete_optic(0)
        self.assertEqual(self.stapi.num_optics(), 1)

        self.stapi.delete_optic(1)
        self.assertEqual(self.stapi.num_optics(), 0)

    def test_clear_optics(self):
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        self.stapi.add_optical_properties_set(self.opt_set, self.front, self.back)
        self.assertEqual(self.stapi.num_optics(), 2)

        self.stapi.clear_optics()
        self.assertEqual(self.stapi.num_optics(), 0)

class ElementTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        # set up dummy optical set
        opt_set = dot_h.args_optical_properties_set("dummy".encode(), 1.1, 1.1, 0)
        front   = dot_h.args_optical_properties_face(.5, .5, 5, 5, 'g'.encode())
        back    = dot_h.args_optical_properties_face(.25, .25, 2, 2, 'g'.encode())
        
        self.stapi.add_optical_properties_set(opt_set, front, back)
        self.el_args = dot_h.args_element(2, 2, 2, 2, 2, 2, 2, False, True, 'c'.encode(), 'p'.encode())
        self.opt_id = 0
        self.a_params = [2]
        self.s_params = [2, 2]

    def test_add_element(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)

        # optical property not set
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.add_element(self.el_args, self.opt_id + 1, self.a_params, self.s_params)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.DATA_VALUE_NOT_FOUND)
        self.assertEqual(self.stapi.num_elements(), 1)

        # bad aperture char
        with self.assertRaises(STAPIv2Exception) as ex:
            self.el_args.ap = 'z'.encode()
            self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
            self.el_args.ap = 'c'.encode()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)
        self.assertEqual(self.stapi.num_elements(), 1)

        # bad surface char
        with self.assertRaises(STAPIv2Exception) as ex:
            self.el_args.surf = 'z'.encode()
            self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
            self.el_args.surf = 'p'.encode()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)
        self.assertEqual(self.stapi.num_elements(), 1)

        # bad aperture params
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.add_element(self.el_args, self.opt_id, [-2], self.s_params)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)
        self.assertEqual(self.stapi.num_elements(), 1)

        # bad surface params
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.add_element(self.el_args, self.opt_id, self.a_params, [2, float('nan')])
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)
        self.assertEqual(self.stapi.num_elements(), 1)

    def test_get_element(self):
        id = self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(id, 1)

        args, optic_id, a_params, s_params = self.stapi.get_element(id)

        self.assertStructEqual(args, self.el_args)
        self.assertEqual(optic_id, self.opt_id)
        self.assertEqual(a_params[0], self.a_params[0])
        self.assertEqual(s_params[0], 1 / (2 * self.s_params[0]))
        self.assertEqual(s_params[1], 1 / (2 * self.s_params[1]))

        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.get_optical_properties_set(id + 1)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.DATA_VALUE_NOT_FOUND)

    def test_delete_element(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 2)

        with self.assertWarns(UserWarning):
            self.stapi.delete_element(0)
        
        with self.assertWarns(UserWarning):
            self.stapi.delete_element(3)

        self.stapi.delete_element(1)
        self.assertEqual(self.stapi.num_elements(), 1)
        self.stapi.delete_element(2)
        self.assertEqual(self.stapi.num_elements(), 0)

    def test_clear_elements(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 2)

        self.stapi.clear_elements()
        self.assertEqual(self.stapi.num_elements(), 0)

    def test_element_enabled(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)

        with self.assertWarns(UserWarning):
            self.stapi.element_enabled(0, True)

        self.stapi.element_enabled(1, True)
        
    def test_element_virtual(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)

        with self.assertWarns(UserWarning):
            self.stapi.element_virtual(0, False)

        self.stapi.element_virtual(1, False)

    def test_element_xyz(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)

        with self.assertWarns(UserWarning):
            self.stapi.element_xyz(0, 3, 3, 3)

        self.stapi.element_xyz(1, 3, 3, 3)

    def test_element_aim(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)

        with self.assertWarns(UserWarning):
            self.stapi.element_aim(0, 3, 3, 3)

        self.stapi.element_aim(1, 3, 3, 3)

    def test_element_zrot(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)

        with self.assertWarns(UserWarning):
            self.stapi.element_zrot(0, 3)

        self.stapi.element_zrot(1, 3)

    def test_element_aperture(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)
        new_ap = 'r'
        new_params = [3, 3]

        with self.assertWarns(UserWarning):
            self.stapi.element_aperture(0, new_ap, new_params)

        # bad aperture char
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.element_aperture(1, 'z', new_params)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)

        # bad aperture params
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.element_aperture(1, new_ap, [0, 2])
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)

        self.stapi.element_aperture(1, new_ap, new_params)

    def test_element_surface(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)
        new_surf = 's'
        new_params = [3]

        with self.assertWarns(UserWarning):
            self.stapi.element_surface(0, new_surf, new_params)

        # bad surface char
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.element_surface(1, 'z', new_params)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)

        # bad surface params
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.element_surface(1, new_surf, [0])
        self.assertEqual(ex.exception.code, dot_h.st_return_code.INVALID_ARGUMENTS)

        self.stapi.element_surface(1, new_surf, new_params)

    def test_element_optic(self):
        self.stapi.add_element(self.el_args, self.opt_id, self.a_params, self.s_params)
        self.assertEqual(self.stapi.num_elements(), 1)

        # optical property not set
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.element_optic(1, self.opt_id + 1)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.DATA_VALUE_NOT_FOUND)

        self.stapi.element_optic(1, self.opt_id)

class SunTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        self.good_angles      = [0, 1, 2]
        self.good_intensities = [0, 1, 2]
        self.bad_intensities  = [0, -1]
        self.args_sun = dot_h.args_sun(3, 608, 303, 1000, 5, ' '.encode())

    def test_add_sun(self):
        # test bad intensities
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.add_sun(self.args_sun, self.good_angles, self.bad_intensities)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.EXCEPTION)

        # test bad shape
        self.args_sun.npoints = 0
        self.args_sun.shape = 'z'.encode()
        with self.assertWarns(UserWarning):
            self.stapi.add_sun(self.args_sun, [], [])
        
        # test bad value
        self.args_sun.shape = 'b'.encode()
        self.args_sun.sigma_halfwidth_csr = 1
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.add_sun(self.args_sun, [], [])
        self.assertEqual(ex.exception.code, dot_h.st_return_code.EXCEPTION)

        self.args_sun.npoints = 3
        self.stapi.add_sun(self.args_sun, self.good_angles, self.good_intensities)

    def test_get_sun(self):
        sun_args = dot_h.args_sun(0, 608, 303, 1000, .5, 'b'.encode())
        self.stapi.add_sun(sun_args)

        rt_sun_args, rt_angle, rt_intensity = self.stapi.get_sun()
        self.assertStructEqual(rt_sun_args, sun_args)
        # TODO: test userdata

    def test_sun_shape(self):
        # test bad shape
        with self.assertWarns(UserWarning):
            self.stapi.sun_shape('z', 4.65)
        
        # test bad value
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sun_shape('g', -4.65)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.EXCEPTION)

        self.stapi.sun_shape('g', 5)

    def test_sun_xyz(self):
        self.stapi.sun_xyz(1, 1, 1)

    def test_sun_userdata(self):
        # test bad intensities
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sun_userdata(3, self.good_angles, self.bad_intensities)
        self.assertEqual(ex.exception.code, dot_h.st_return_code.EXCEPTION)

        self.stapi.sun_userdata(3, self.good_angles, self.good_intensities)

class BatchTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        # set up dummy values
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

    def test_call_st_read_input_json(self):
        f = open('./sample.json', mode='rb')
        self.stapi.batch([
            self.stapi.generate_api_call(dot_h.st_api_call.CALL_ST_READ_INPUT_JSON, f.read())
        ])
        f.close()
        self.assertEqual(self.stapi.num_elements(), 126)

    # TODO: after simulation parameters getter function
    # def test_call_st_sim_params(self):
    #     pass
    # def test_call_st_sim_errors(self):
    #     pass

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
    # def test_call_st_sun_userdata(self):
    #     pass
    # def test_call_st_sim_setup(self):
    #     pass
    # def test_call_st_sim_run_v2(self):
    #     pass
    # def test_call_st_sim_report(self):
    #     pass

if __name__ == '__main__':
    # print(f'\n\n\n\n{found_in(dot_h)}\n\n\n\n')
    unittest.main()