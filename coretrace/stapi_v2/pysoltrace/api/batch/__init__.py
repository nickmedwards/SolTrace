# class is_ready:
#     def __init__(self):
#         self.ready = False

# class holder:
#     _slots_ = ('readys')

#     def __init__(self):
#         self.readys = []

#     def add(self):
#         n = is_ready()
#         self.readys.append(n)
#         return n

#     def test(self):
#         self.readys[0].ready = True

# h = holder()

# one = h.add()
# two = h.add()

# print(one.ready)
# print(two.ready)

# h.test()

# print(one.ready)
# print(two.ready)

import ctypes

from pysoltrace.api.dll import context
from pysoltrace.api.utils import check_return_code, st_function

class batch_record:
    __slots__ = ('ready', 'batch_call', 'value', '__get_res')

    def __init__(self, batch_call, get_res = None):
        self.ready = False
        self.batch_call = batch_call
        self.__get_res = get_res if get_res != None else lambda: None

    @property
    def value(self): return self.__get_res() if self.ready else None

class batch(context):
    def __init__(self, pdll, pcxt):
        super().__init__(pdll, pcxt)


        # keep the struct instances alive — ctypes.cast() does NOT keep a
        # reference, so if these get garbage collected the void* becomes dangling
        self.__stash_batch_args = []
        self.__called = 0
        self.__calls: list[batch_record] = []

    # def dump_batch_args(self):
    #     for args in self.__stash_batch_args: print(args)

    def add(self, api_call, get_res = None):
        br = batch_record(api_call, get_res)
        self.__calls.append(br)
        return br

    def clear(self):
        self.__called = 0
        self.__calls: list[batch_record] = []

    @st_function
    def __call__(self, verbose = False):
        num_calls = len(self.__calls) - self.__called
        assert num_calls > 0, "No batch calls recorded to call"

        callable_brs = self.__calls[self.__called:]
        void_cast = lambda c: ctypes.cast(ctypes.pointer(c), ctypes.c_void_p)

        args_arr = (ctypes.c_void_p * num_calls)(*[
            void_cast(br.batch_call) for br in callable_brs
        ])
        fail_iteration = ctypes.c_uint(0)

        for br in callable_brs: br.ready = True
        return self._pdll.st_batch(self._pcxt,
                                   args_arr,
                                   num_calls,
                                   ctypes.pointer(fail_iteration),
                                   verbose)

