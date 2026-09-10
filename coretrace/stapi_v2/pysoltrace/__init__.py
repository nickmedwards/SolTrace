# no outside of pysoltrace dependencies
from pysoltrace.chedder import dot_h, found_in 
from pysoltrace.point import Point
from pysoltrace import soltrace_json
# depend on other pysoltrace modules
from pysoltrace import math_utils # Point
from pysoltrace import soltrace_constants # dot_h
from pysoltrace.stapi_v2 import STAPIv2 # soltrace_constants
from pysoltrace.api import api, STAPIv2Exception # soltrace_constants

from pysoltrace.legacy import legacy as PySolTrace # api, dot_h, soltrace_json, math_utils, Point

# _api = api.STAPIv2()

__all__ = [
    'dot_h',
    'found_in',
    'math_utils',
    'Point',
    'PySolTrace',
    'soltrace_constants',
    'soltrace_json',
    'STAPIv2',
    'api',
    'STAPIv2Exception',
]
