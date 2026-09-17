import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import api, soltrace_constants as stc, dot_h

stapi = api()

print(stapi)

print(stapi.runner.get_installed())

# print(len(stapi.data.optic))
# print(len(stapi.data.element))
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
