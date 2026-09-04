import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import api

stapi = api()

print(stapi)

print(stapi.runner.get_installed())