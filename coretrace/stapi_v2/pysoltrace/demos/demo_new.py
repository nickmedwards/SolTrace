import os, sys
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import api

stapi = api.STAPIv2()

print(stapi)