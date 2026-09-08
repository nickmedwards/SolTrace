class is_ready:
    def __init__(self):
        self.ready = False

class holder:
    _slots_ = ('readys')

    def __init__(self):
        self.readys = []

    def add(self):
        n = is_ready()
        self.readys.append(n)
        return n

    def test(self):
        self.readys[0].ready = True

h = holder()

one = h.add()
two = h.add()

print(one.ready)
print(two.ready)

h.test()

print(one.ready)
print(two.ready)

from pysoltrace.api.dll import context

class batch_record:
    __slots__ = ('ready', '__batch_call', 'value', '__get_res')

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
