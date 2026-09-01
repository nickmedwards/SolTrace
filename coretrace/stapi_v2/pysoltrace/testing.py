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

class PointTests(unittest.TestCase):
    def setUp(self):
        self.a = Point(6, 0, 8)
        self.b = Point(3, 0, 3)
        self.d = Point(3.2, 5.0, 2.4)
        self.e = Point(6, 0, 8)
        self.zeros = Point()
        return super().setUp()
    
    def test_repr(self):
        self.assertEqual(f'{self.a}', '[6.00, 0.00, 8.00]')
        self.assertEqual(f'{self.a:.4e}', '[6.0000e+00, 0.0000e+00, 8.0000e+00]')

    def test_bool(self):
        self.assertEqual(bool(self.a), True)
        self.assertEqual(bool(self.zeros), False)

    def test_float(self):
        self.assertEqual(float(self.a), 10.0)

    def test_int(self):
        self.assertEqual(int(self.a), 10)

    def test_iter(self):
        sum = 0
        for v in self.a: sum += v
        self.assertEqual(sum, 14)

    def test_get_set_item(self):
        self.assertEqual(self.a[1], 0)
        self.a[1] = -17
        self.assertEqual(self.a[1], -17)

    def test_len(self):
        self.assertEqual(len(self.a), 3)

    def test_negation(self):
        self.assertEqual(-self.a, Point(-6, 0, -8))

    def test_abs(self):
        self.a[1] = -17
        self.assertEqual(abs(self.a), 19.72308292331602)

    def test_add(self):
        self.assertEqual(self.a + self.b,              Point(9, 0, 11))
        self.assertEqual(self.a + 1,                   Point(7, 1, 9))
        self.assertEqual(self.a + 2.1,                 Point(8.1, 2.1, 10.1))
        self.assertEqual(self.a + [3, 0, 3],           Point(9, 0, 11))
        self.assertEqual(self.a + np.array([3, 0, 3]), Point(9, 0, 11))
        # self.assertEqual(self.a + 'not implemented',   NotImplemented)

    def test_radd(self):
        self.assertEqual(1 + self.b,                   Point(4, 1, 4))
        self.assertEqual(2.1 + self.b,                 Point(5.1, 2.1, 5.1))
        self.assertEqual([6, 0, 8] + self.b,           Point(9, 0, 11))
        # right add with np.array returns np.array
        temp = np.array([6, 0, 8]) + self.b
        self.assertAlmostEqual(Point(9, 0, 11) - temp, 0)

    def test_iadd(self):
        c = Point()
        c += self.a + self.b
        self.assertEqual(c, Point(9, 0, 11))
        c += 1
        self.assertEqual(c, Point(10, 1, 12))
        c += 2.1
        self.assertEqual(c, Point(12.1, 3.1, 14.1))
        c += [2, 2, 2]
        self.assertEqual(c, Point(14.1, 5.1, 16.1))
        c += np.array([-2, -2, -2])
        # floating point error makes assertEqual fail
        self.assertAlmostEqual(c - Point(12.1, 3.1, 14.1), 0)

    def test_sub(self):
        self.assertEqual(self.a - self.b,              Point(3, 0, 5))
        self.assertEqual(self.a - 1,                   Point(5, -1, 7))
        self.assertEqual(self.a - 2.1,                 Point(3.9, -2.1, 5.9))
        self.assertEqual(self.a - [3, 0, 3],           Point(3, 0, 5))
        self.assertEqual(self.a - np.array([3, 0, 3]), Point(3, 0, 5))

    def test_rsub(self):
        self.assertEqual(1 - self.b, Point(-2, 1, -2))
        # floating point error makes assertEqual fail
        self.assertAlmostEqual(2.1 - self.b - Point(-.9, 2.1, -.9), 0)
        self.assertEqual([6, 0, 8] - self.b,           Point(3, 0, 5))
        # right subtraction with np.array returns np.array
        temp = np.array([6, 0, 8]) - self.b
        self.assertAlmostEqual(Point(3, 0, 5) - temp, 0)

    def test_isub(self):
        c = Point()
        c -= self.a + self.b
        self.assertEqual(c, Point(-9, 0, -11))
        c -= 1
        self.assertEqual(c, Point(-10, -1, -12))
        c -= 2.1
        self.assertEqual(c, Point(-12.1, -3.1, -14.1))
        c -= [2, 2, 2]
        self.assertEqual(c, Point(-14.1, -5.1, -16.1))
        c -= np.array([-2, -2, -2])
        # floating point error makes assertEqual fail
        self.assertAlmostEqual(c - Point(-12.1, -3.1, -14.1), 0)

    def test_mul(self):
        self.assertEqual(self.a * self.b, Point(18, 0, 24))
        self.assertEqual(self.a * 4,      Point(24, 0, 32))
        # floating point error makes assertEqual fail
        self.assertAlmostEqual(self.a * 2.1 - Point(12.6, 0, 16.8), 0)
        self.assertEqual(self.a * [3, 0, 3],           Point(18, 0, 24))
        self.assertEqual(self.a * np.array([3, 0, 3]), Point(18, 0, 24))

    def test_rmul(self):
        self.assertEqual(4 * self.b, Point(12, 0, 12))
        # floating point error makes assertEqual fail
        self.assertAlmostEqual(2.1 * self.b - Point(6.3, 0, 6.3), 0)
        self.assertEqual([6, 0, 8] * self.b,           Point(18, 0, 24))
        # right subtraction with np.array returns np.array
        temp = np.array([6, 0, 8]) * self.b
        self.assertAlmostEqual(Point(18, 0, 24) - temp, 0)

    def test_imul(self):
        c = self.a.copy()
        c *= self.b
        self.assertEqual(c, Point(18, 0, 24))
        c *= 4
        self.assertEqual(c, Point(72, 0, 96))
        c *= 2.1
        # floating point error makes assertEqual fail
        self.assertAlmostEqual(c - Point(151.2, 0, 201.6), 0)
        c *= [2, 2, 2]
        self.assertAlmostEqual(c - Point(302.4, 0, 403.2), 0)
        c *= np.array([2, 2, 2])
        self.assertAlmostEqual(c - Point(604.8, 0, 806.4), 0)

    def test_floordiv(self):
        self.assertEqual(self.a // self.d,              Point(1, 0, 3))
        self.assertEqual(self.a // 4,                   Point(1, 0, 2))
        self.assertEqual(self.a // 2.1,                 Point(2, 0, 3))
        self.assertEqual(self.a // [3, 1, 3],           Point(2, 0, 2))
        self.assertEqual(self.a // np.array([3, 1, 3]), Point(2, 0, 2))

    def test_ifloordiv(self):
        c = self.a.copy()
        c //= self.d
        self.assertEqual(c, Point(1, 0, 3))
        c = self.a.copy()
        c //= 4
        self.assertEqual(c, Point(1, 0, 2))
        c = self.a.copy()
        c //= 2.1
        self.assertEqual(c, Point(2, 0, 3))
        c = self.a.copy()
        c //= [3, 1, 3]
        self.assertEqual(c, Point(2, 0, 2))
        c = self.a.copy()
        c //= np.array([3, 1, 3])
        self.assertEqual(c, Point(2, 0, 2))

    def test_truediv(self):
        self.assertEqual(self.a / self.d,              Point(6 / 3.2, 0, 8 / 2.4))
        self.assertEqual(self.a / 4,                   Point(3 / 2, 0, 2))
        self.assertEqual(self.a / 2.1,                 Point(6 / 2.1, 0, 8 / 2.1))
        self.assertEqual(self.a / [3, 1, 3],           Point(2, 0, 8 / 3))
        self.assertEqual(self.a / np.array([3, 1, 3]), Point(2, 0, 8 / 3))

    def test_itruediv(self):
        c = self.a.copy()
        c /= self.d
        self.assertEqual(c, Point(6 / 3.2, 0, 8 / 2.4))
        c = self.a.copy()
        c /= 4
        self.assertEqual(c, Point(3 / 2, 0, 2))
        c = self.a.copy()
        c /= 2.1
        self.assertEqual(c, Point(6 / 2.1, 0, 8 / 2.1))
        c = self.a.copy()
        c /= [3, 1, 3]
        self.assertEqual(c, Point(2, 0, 8 / 3))
        c = self.a.copy()
        c /= np.array([3, 1, 3])
        self.assertEqual(c, Point(2, 0, 8 / 3))

    def test_cross(self):
        self.a[1] = -17
        self.assertEqual(self.a @ self.b,               Point(-51, 6, 51))
        self.assertEqual(self.a.dot(self.a @ self.b),   0)
        self.assertEqual(self.a @ [3, 10, 3],           Point(-131, 6, 111))
        self.assertEqual(self.a @ np.array([3, 10, 3]), Point(-131, 6, 111))

    def test_icross(self):
        self.a[1] = -17
        c = self.a.copy()
        c @= self.b
        self.assertEqual(c, Point(-51, 6, 51))
        c = self.a.copy()
        c @= [3, 10, 3]
        self.assertEqual(c, Point(-131, 6, 111))
        c = self.a.copy()
        c @= np.array([3, 10, 3])
        self.assertEqual(c, Point(-131, 6, 111))

    def test_eq(self):
        self.assertEqual(self.a,    self.e)
        self.assertNotEqual(self.a, self.e + 1)
        self.assertEqual(self.a,    [6, 0, 8])
        self.assertNotEqual(self.a, [6, 1, 8])
        self.assertEqual(self.a,    np.array([6, 0, 8]))
        self.assertNotEqual(self.a, np.array([6, 1, 8]))

    def test_neq(self):
        self.assertEqual(self.a != self.e,              False)
        self.assertEqual(self.a != self.e + 1,          True)
        self.assertEqual(self.a != [6, 0, 8],           False)
        self.assertEqual(self.a != [6, 1, 8],           True)
        self.assertEqual(self.a != np.array([6, 0, 8]), False)
        self.assertEqual(self.a != np.array([6, 1, 8]), True)

    def test_lt(self):
        self.assertEqual(self.a < self.e,               False)
        self.assertEqual(self.a < self.e + 1,           True)
        self.assertEqual(self.a < self.e - 1,           False)
        self.assertEqual(self.a < [6, 0, 8],            False)
        self.assertEqual(self.a < [6, 1, 8],            True)
        self.assertEqual(self.a < [6, -1, 8],           True)
        self.assertEqual(self.a < [5, -1, 7],           False)
        self.assertEqual(self.a < np.array([6, 0, 8]),  False)
        self.assertEqual(self.a < np.array([6, 1, 8]),  True)
        self.assertEqual(self.a < np.array([6, -1, 8]), True)
        self.assertEqual(self.a < np.array([5, -1, 7]), False)

    def test_gt(self):
        self.assertEqual(self.a > self.e,               False)
        self.assertEqual(self.a > self.e + 1,           False)
        self.assertEqual(self.a > self.e - 1,           True)
        self.assertEqual(self.a > [6, 0, 8],            False)
        self.assertEqual(self.a > [6, 1, 8],            False)
        self.assertEqual(self.a > [6, -1, 8],           False)
        self.assertEqual(self.a > [5, -1, 7],           True)
        self.assertEqual(self.a > np.array([6, 0, 8]),  False)
        self.assertEqual(self.a > np.array([6, 1, 8]),  False)
        self.assertEqual(self.a > np.array([6, -1, 8]), False)
        self.assertEqual(self.a > np.array([5, -1, 7]), True)

    def test_lte(self):
        self.assertEqual(self.a <= self.e,               True)
        self.assertEqual(self.a <= self.e + 1,           True)
        self.assertEqual(self.a <= self.e - 1,           False)
        self.assertEqual(self.a <= [6, 0, 8],            True)
        self.assertEqual(self.a <= [6, 1, 8],            True)
        self.assertEqual(self.a <= [6, -1, 8],           True)
        self.assertEqual(self.a <= [5, -1, 7],           False)
        self.assertEqual(self.a <= np.array([6, 0, 8]),  True)
        self.assertEqual(self.a <= np.array([6, 1, 8]),  True)
        self.assertEqual(self.a <= np.array([6, -1, 8]), True)
        self.assertEqual(self.a <= np.array([5, -1, 7]), False)

    def test_gte(self):
        self.assertEqual(self.a >= self.e,               True)
        self.assertEqual(self.a >= self.e + 1,           False)
        self.assertEqual(self.a >= self.e - 1,           True)
        self.assertEqual(self.a >= [6, 0, 8],            True)
        self.assertEqual(self.a >= [6, 1, 8],            False)
        self.assertEqual(self.a >= [6, -1, 8],           False)
        self.assertEqual(self.a >= [5, -1, 7],           True)
        self.assertEqual(self.a >= np.array([6, 0, 8]),  True)
        self.assertEqual(self.a >= np.array([6, 1, 8]),  False)
        self.assertEqual(self.a >= np.array([6, -1, 8]), False)
        self.assertEqual(self.a >= np.array([5, -1, 7]), True)

    def test_reduce(self):
        self.assertEqual(self.a.reduce(),     14)
        self.assertEqual(self.b.reduce(),     6)
        self.assertEqual(self.d.reduce(),     10.6)
        self.assertEqual(self.e.reduce(),     14)
        self.assertEqual(self.zeros.reduce(), 0)

    def test_radius(self):
        self.assertEqual(self.a.radius(),     10)
        self.assertEqual(self.b.radius(),     4.242640687119285)
        self.assertEqual(self.d.radius(),     6.4031242374328485)
        self.assertEqual(self.e.radius(),     10)
        self.assertEqual(self.zeros.radius(), 0)

    def test_unitize(self):
        self.assertEqual(self.a.unitize(),     Point(.6, 0, .8))
        self.assertEqual(self.b.unitize(),     Point(3 / sqrt(18), 0, 3 / sqrt(18)))
        self.assertEqual(self.d.unitize(),     Point(self.d.x / self.d.radius(),
                                                     self.d.y / self.d.radius(),
                                                     self.d.z / self.d.radius()))
        self.assertEqual(self.e.unitize(),     Point(.6, 0, .8))
        self.assertEqual(self.zeros.unitize(), Point())

    def test_as_list(self):
        self.assertEqual(self.a.as_list(),     [6, 0, 8])
        self.assertEqual(self.b.as_list(),     [3, 0, 3])
        self.assertEqual(self.d.as_list(),     [3.2, 5, 2.4])
        self.assertEqual(self.e.as_list(),     [6, 0, 8])
        self.assertEqual(self.zeros.as_list(), [0, 0, 0])

    def test_from_list(self):
        self.assertEqual(Point.from_list([6, 0, 8]),     Point(6, 0, 8))
        self.assertEqual(Point.from_list([3, 0, 3]),     Point(3, 0, 3))
        self.assertEqual(Point.from_list([3.2, 5, 2.4]), Point(3.2, 5, 2.4))
        self.assertEqual(Point.from_list(np.array([6, 0, 8])),     Point(6, 0, 8))
        self.assertEqual(Point.from_list(np.array([3, 0, 3])),     Point(3, 0, 3))
        self.assertEqual(Point.from_list(np.array([3.2, 5, 2.4])), Point(3.2, 5, 2.4))

class STAPIv2TestCase(unittest.TestCase):
    def setUp(self):
        self.stapi = STAPIv2(testing=True)
        return super().setUp()

    def assertStructEqual(self, value, check):
        for field in value._fields_:
            self.assertEqual(getattr(value, field[0]),
                             getattr(check, field[0]))

class ConstantsTests(STAPIv2TestCase):
    def test_error_code_msg(self):
        self.assertIn(dot_h.st_return_code.FAILURE, _STC.ST_RETURN_CODE_ERROR_MSG)
        self.assertEqual(len(_STC.ST_RETURN_CODE_ERROR_MSG[dot_h.st_return_code.FAILURE]), 0)

        for i in range(dot_h.st_return_code.CANCEL, 
                       dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE):
            self.assertIn(i, _STC.ST_RETURN_CODE_ERROR_MSG)
            self.assertGreater(len(_STC.ST_RETURN_CODE_ERROR_MSG[i]), 0)

        _, _, check_return_code = self.stapi.sneak()
        for i in range(dot_h.st_return_code.CANCEL, 
                       dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE):
            with self.assertRaises(STAPIv2Exception) as ex:
                check_return_code(i)
            self.assertEqual(ex.exception.code, i)

        for i in range(dot_h.st_return_code.RETURN_COUNT, 
                       dot_h.st_return_code.RETURN_COUNT + 2):
            with self.assertRaises(STAPIv2Exception) as ex:
                check_return_code(i)
            self.assertEqual(ex.exception.code, i)

    def test_warning_code_msg(self):
        for i in range(dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE, 
                       dot_h.st_return_code.RETURN_COUNT):
            self.assertIn(i, _STC.ST_RETURN_CODE_WARNING_MSG)
            self.assertGreater(len(_STC.ST_RETURN_CODE_WARNING_MSG[i]), 0)

        _, _, check_return_code = self.stapi.sneak()
        for i in range(dot_h.st_return_code.WARNING_FELLBACK_FROM_EMBREE, 
                       dot_h.st_return_code.RETURN_COUNT):
            with self.assertWarns(UserWarning):
                check_return_code(i)

class SimulationParametersTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        self.params = dot_h.args_simulation_parameters(1, 100, .1, 35.962278, -106.5122622, True, True, False)

    def test_set_simulation_parameters(self):
        self.stapi.set_simulation_parameters(self.params)

    def test_get_simulation_parameters(self):
        self.stapi.set_simulation_parameters(self.params)

        rt_params = self.stapi.get_simulation_parameters()
        self.assertStructEqual(rt_params, self.params)

    def test_sim_params(self):
        self.stapi.sim_params(1, 100, True)

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'number_of_rays'), 1)
        self.assertEqual(getattr(rt_params, 'max_number_of_rays'), 100)
        self.assertEqual(getattr(rt_params, 'as_power_tower'), True)

    def test_sim_errors(self):
        self.stapi.sim_errors(True, True)

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'include_sun_shape_errors'), True)
        self.assertEqual(getattr(rt_params, 'include_optical_errors'), True)

    def test_sim_location(self):
        self.stapi.sim_location(35.962278, -106.5122622)

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'latitude'), 35.962278)
        self.assertEqual(getattr(rt_params, 'longitude'), -106.5122622)

    def test_sim_tolerance(self):
        self.stapi.sim_tolerance(.1)

        rt_params = self.stapi.get_simulation_parameters()
        self.assertEqual(getattr(rt_params, 'tolerance'), .1)

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

        self.loc = dot_h.args_sun_location(40.0, -105.0, -7.0)
        self.dt  = dot_h.args_sun_datetime(2025, 6, 20)
        self.az = 178.61128380
        self.el = 73.439035265
        self.zen = 90 - self.el
        self.sun_vector = Point(0.006908, -0.2849516, 0.9585169)

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

    def test_get_sun_az_zen(self):
        az, zen = self.stapi.get_sun_az_zen(dot_h.SolarPositionCalculationMethod.SPA, self.loc, self.dt)
        self.assertAlmostEqual(az, self.az, 7)
        self.assertAlmostEqual(zen, self.zen, 7)

    def test_get_sun_az_el(self):
        az, el = self.stapi.get_sun_az_el(dot_h.SolarPositionCalculationMethod.SPA, self.loc, self.dt)
        self.assertAlmostEqual(az, self.az, 7)
        self.assertAlmostEqual(el, self.el, 7)

    def test_get_sun_vector(self):
        v = self.stapi.get_sun_vector(dot_h.SolarPositionCalculationMethod.SPA, self.loc, self.dt)
        self.assertAlmostEqual((v - self.sun_vector).radius(), 0, 6)
        
class RunnerTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        self.stapi.read_input_json('./sample.json')

    def test_set_up_native(self):
        # if this is called after sim_setup call, leads to OS error 
        # bc I think dll handle gets cleaned up before call completes
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE, 8, [608, 303])
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NUMBER_THREADS_SEEDS_MISMATCH_FAILURE)

        self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)

    def test_set_up_embree(self):
        if self.stapi.is_runner_installed(dot_h.st_runner_type_t.EMBREE):
            self.stapi.sim_setup(dot_h.st_runner_type_t.EMBREE)
        else:
            with self.assertWarns(UserWarning):
                self.stapi.sim_setup(dot_h.st_runner_type_t.EMBREE)
        
    def test_set_up_optix(self):
        if self.stapi.is_runner_installed(dot_h.st_runner_type_t.OPTIX):
            self.stapi.sim_setup(dot_h.st_runner_type_t.OPTIX)

            with self.assertWarns(UserWarning):
                self.stapi.sim_setup(dot_h.st_runner_type_t.OPTIX, 1)
        else:
            with self.assertWarns(UserWarning):
                self.stapi.sim_setup(dot_h.st_runner_type_t.OPTIX)

    def test_run_native(self):
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_run_v2()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_FOUND)

        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)
        self.stapi.sim_run_v2()

    def test_run_embree(self):
        if not self.stapi.is_runner_installed(dot_h.st_runner_type_t.EMBREE):
            self.skipTest('Embree runner not installed, skip testing running EmbreeRunner.')
        
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_run_v2()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_FOUND)

        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.EMBREE)
        self.stapi.sim_run_v2()
        
    def test_run_optix(self):
        if not self.stapi.is_runner_installed(dot_h.st_runner_type_t.OPTIX):
            self.skipTest('Optix runner not installed, skip testing running OptixRunner.')
        
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_run_v2()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_FOUND)

        self.stapi.sim_setup(dot_h.st_runner_type_t.OPTIX)
        self.stapi.sim_run_v2()

    def test_report_native(self):
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_report()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_FOUND)

        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)

        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_report()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_READY)

        self.stapi.sim_run_v2()
        self.stapi.sim_report()

    def test_report_embree(self):
        if not self.stapi.is_runner_installed(dot_h.st_runner_type_t.EMBREE):
            self.skipTest('Embree runner not installed, skip testing running EmbreeRunner.')
        
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_report()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_FOUND)

        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.EMBREE)

        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_report()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_READY)

        self.stapi.sim_run_v2()
        self.stapi.sim_report()
        
    def test_report_optix(self):
        if not self.stapi.is_runner_installed(dot_h.st_runner_type_t.OPTIX):
            self.skipTest('Optix runner not installed, skip testing running OptixRunner.')
        
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_report()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_FOUND)

        self.stapi.sim_setup(dot_h.st_runner_type_t.OPTIX)
        
        with self.assertRaises(STAPIv2Exception) as ex:
            self.stapi.sim_report()
        self.assertEqual(ex.exception.code, dot_h.st_return_code.RUNNER_NOT_READY)

        self.stapi.sim_run_v2()
        self.stapi.sim_report()

class ResultsNativeTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        self.stapi.read_input_json('./sample.json')
        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.NATIVE)
        self.stapi.sim_run_v2()
        self.stapi.sim_report()
        self.n_intersections = self.stapi.num_intersections()

    def test_locations(self):
        loc_x, loc_y, loc_z = self.stapi.locations(self.n_intersections)
        self.assertEqual(len(loc_x), self.n_intersections)
        self.assertEqual(len(loc_y), self.n_intersections)
        self.assertEqual(len(loc_z), self.n_intersections)

    def test_cosines(self):
        coz_x, coz_y, coz_z = self.stapi.cosines(self.n_intersections)
        self.assertEqual(len(coz_x), self.n_intersections)
        self.assertEqual(len(coz_y), self.n_intersections)
        self.assertEqual(len(coz_z), self.n_intersections)

    def test_elementmap(self):
        element_map = self.stapi.elementmap(self.n_intersections)
        self.assertEqual(len(element_map), self.n_intersections)

    def test_stagemap(self):
        stage_map = self.stapi.stagemap(self.n_intersections)
        self.assertEqual(len(stage_map), self.n_intersections)

    def test_raynumbers(self):
        ray_numbers = self.stapi.raynumbers(self.n_intersections)
        self.assertEqual(len(ray_numbers), self.n_intersections)

    def test_sun_stats(self):
        width, height, area, nsunrays = self.stapi.sun_stats()
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
        self.assertGreater(area, 0)
        self.assertGreater(nsunrays, 0)

    def test_get_results_data(self):
        res = self.stapi.get_results_data(self.n_intersections)
        self.assertEqual(len(res.loc_x[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.loc_y[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.loc_z[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_x[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_y[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_z[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.element_map[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.stage_map[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.ray_numbers[:self.n_intersections]), self.n_intersections)

@unittest.skipIf(not STAPIv2(testing=True).is_runner_installed(dot_h.st_runner_type_t.EMBREE),
                 "Embree runner not installed, skip testing EmbreeRunner results.")
class ResultsEmbreeTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        self.stapi.read_input_json('./sample.json')
        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.EMBREE)
        self.stapi.sim_run_v2()
        self.stapi.sim_report()
        self.n_intersections = self.stapi.num_intersections()

    def test_locations(self):
        loc_x, loc_y, loc_z = self.stapi.locations(self.n_intersections)
        self.assertEqual(len(loc_x), self.n_intersections)
        self.assertEqual(len(loc_y), self.n_intersections)
        self.assertEqual(len(loc_z), self.n_intersections)

    def test_cosines(self):
        coz_x, coz_y, coz_z = self.stapi.cosines(self.n_intersections)
        self.assertEqual(len(coz_x), self.n_intersections)
        self.assertEqual(len(coz_y), self.n_intersections)
        self.assertEqual(len(coz_z), self.n_intersections)

    def test_elementmap(self):
        element_map = self.stapi.elementmap(self.n_intersections)
        self.assertEqual(len(element_map), self.n_intersections)

    def test_stagemap(self):
        stage_map = self.stapi.stagemap(self.n_intersections)
        self.assertEqual(len(stage_map), self.n_intersections)

    def test_raynumbers(self):
        ray_numbers = self.stapi.raynumbers(self.n_intersections)
        self.assertEqual(len(ray_numbers), self.n_intersections)

    def test_sun_stats(self):
        width, height, area, nsunrays = self.stapi.sun_stats()
        self.assertGreater(width, 0)
        self.assertGreater(height, 0)
        self.assertGreater(area, 0)
        self.assertGreater(nsunrays, 0)

    def test_get_results_data(self):
        res = self.stapi.get_results_data(self.n_intersections)
        self.assertEqual(len(res.loc_x[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.loc_y[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.loc_z[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_x[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_y[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_z[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.element_map[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.stage_map[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.ray_numbers[:self.n_intersections]), self.n_intersections)

@unittest.skipIf(not STAPIv2(testing=True).is_runner_installed(dot_h.st_runner_type_t.OPTIX),
                 "Optix runner not installed, skip testing OptixRunner results.")
class ResultsOptixTests(STAPIv2TestCase):
    def setUp(self):
        super().setUp()
        self.stapi.read_input_json('./sample.json')
        self.stapi.sim_params(1000, 10000, False)
        self.stapi.sim_setup(dot_h.st_runner_type_t.OPTIX)
        self.stapi.sim_run_v2()
        self.stapi.sim_report()
        self.n_intersections = self.stapi.num_intersections()

    def test_locations(self):
        loc_x, loc_y, loc_z = self.stapi.locations(self.n_intersections)
        self.assertEqual(len(loc_x), self.n_intersections)
        self.assertEqual(len(loc_y), self.n_intersections)
        self.assertEqual(len(loc_z), self.n_intersections)

    def test_cosines(self):
        coz_x, coz_y, coz_z = self.stapi.cosines(self.n_intersections)
        self.assertEqual(len(coz_x), self.n_intersections)
        self.assertEqual(len(coz_y), self.n_intersections)
        self.assertEqual(len(coz_z), self.n_intersections)

    def test_elementmap(self):
        element_map = self.stapi.elementmap(self.n_intersections)
        self.assertEqual(len(element_map), self.n_intersections)

    def test_stagemap(self):
        stage_map = self.stapi.stagemap(self.n_intersections)
        self.assertEqual(len(stage_map), self.n_intersections)

    def test_raynumbers(self):
        ray_numbers = self.stapi.raynumbers(self.n_intersections)
        self.assertEqual(len(ray_numbers), self.n_intersections)

    def test_sun_stats(self):
        width, height, area, nsunrays = self.stapi.sun_stats()
        self.assertEqual(width, 0)
        self.assertEqual(height, 0)
        self.assertGreater(area, 0)
        self.assertGreater(nsunrays, 0)

    def test_get_results_data(self):
        res = self.stapi.get_results_data(self.n_intersections)
        self.assertEqual(len(res.loc_x[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.loc_y[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.loc_z[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_x[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_y[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.cos_z[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.element_map[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.stage_map[:self.n_intersections]), self.n_intersections)
        self.assertEqual(len(res.ray_numbers[:self.n_intersections]), self.n_intersections)

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