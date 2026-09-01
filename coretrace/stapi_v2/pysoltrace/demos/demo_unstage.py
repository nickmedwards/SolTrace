import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

import numpy as np

from pysoltrace import PySolTrace as pst, Point, STAPIv2

CONVERT_GLOBAL = np.array([[-1., 0., 0.],
                           [ 0., 0., 1.],
                           [ 0., 1., 0.]])

# NSTTF Coordinates (+X = West, +Y = Up, + Z = North)
target_stage_center = np.array([42.1, 47, 7.8])
target_stage_aim = np.array([0, target_stage_center[1], 122])

target_euler = pst.util_calc_euler_angles(target_stage_center, target_stage_aim, 0)
transforms = pst.util_calc_transforms(target_euler)

unstage = lambda m, v: np.dot(m, v)

if __name__ == '__main__':
    print(transforms['rloctoref'])
    print(unstage(transforms['rloctoref'], [0., 0.848048, 0.529919]))
