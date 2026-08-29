import math
import numpy as np

try:
    from point import Point
except ImportError:
    from .point import Point

# Freedman–Diaconis rule
def freedman_diaconis_np(arr, fudge: float = 1.0):
    min_val, iqr25, iqr75, max_val = np.quantile(arr, [0, .25, .75, 1])
    bin_width = 2 * (iqr75 - iqr25) * len(arr) ** (-1/3)
    return int(np.ceil(fudge * (max_val - min_val) / bin_width))

def arbitrary_rotation(theta: float,
                       axis:  Point | list,
                       axloc: Point | list,
                       pt:    Point | list):
    """
    Basically, copypasta from pysoltrace.
    
    Rotation of a point 'pt' about an arbitrary axis with direction 'axis' centered at point 'axloc'.
    The point is rotated through 'theta' radians.

    Parameters
    ----------
    theta : float
        Angle of rotation (rad)
    axis : list or np.ndarray
        Vector (x=i,y=j,z=k) indicating direction of axis for rotation
    axloc : list or np.ndarray
        Location of the axis origin
    pt : list or np.ndarray
        Location of the point that is to be rotated

    Returns
    -----------
    np.ndarray
        Point after rotation
    """

    a = axloc[0]     #Point through which the axis passes
    b = axloc[1]
    c = axloc[2]
    x = pt[0]        #Point that we're rotating
    y = pt[1]
    z = pt[2]
    u = axis[0]        #Direction of the axis that we're rotating about
    v = axis[1]
    w = axis[2]

    sinth = math.sin(theta)
    costh = math.cos(theta)

    return Point((a*(v*v+w*w) - u*(b*v + c*w - u*x - v*y - w*z))*(1.-costh) + x*costh + (-c*v + b*w - w*y + v*z)*sinth,
                 (b*(u*u+w*w) - v*(a*u + c*w - u*x - v*y - w*z))*(1.-costh) + y*costh + ( c*u - a*w + w*x - u*z)*sinth,
                 (c*(u*u+v*v) - w*(a*u + b*v - u*x - v*y - w*z))*(1.-costh) + z*costh + (-b*u + a*v - v*x + u*y)*sinth)

def zrot_from_azel(vect: Point | list) -> float: # TODO: expose a st_util_calc_zrot_azel
    if isinstance(vect, (Point, list)) or hasattr(vect, '__getitem__'):
        vect_i, vect_j, vect_k = vect[0], vect[1], vect[2]
    else:
        raise TypeError("Function expects 'vect' of type List or Point")

    az = math.atan2(vect_i, vect_j)
    az = (az + 2.*math.pi) if az < 0. else az

    el = math.asin(vect_k)

    #Calculate Euler angles
    alpha = math.atan2(vect_i, vect_k);                                        #Rotation about the Y axis
    bsign = 1 if vect_j > 0. else -1
    beta = -bsign * math.acos( 
            (math.pow(vect_i,2) + math.pow(vect_k,2)) /
            max(math.sqrt(math.pow(vect_i,2) + math.pow(vect_k,2)), 1.e-8))    #Rotation about the modified X axis

    #Calculate the modified axis vector
    modax = Point(math.cos(alpha), 0., - math.sin(alpha))

    #Rotation references - axis point. Set as origin
    axpos = Point(0., 0., 0.)
    #sp_point to rotate. lower edge of heliostat
    pbase = Point(0., -1., 0.)

    #Rotated point
    protv = arbitrary_rotation(beta, modax, axpos, pbase).unitize()

    #Azimuth/elevation reference vector (vector normal to where the base of the heliostat should be)
    azelref = Point(
        math.sin(az)*math.sin(el),
        math.cos(az)*math.sin(el),
        -math.cos(el)
    )
    # the sign of the rotation angle is determined by whether the 'k' component of the cross product
    # vector is positive or negative.
    cp = Point(
        protv.y*azelref.z - protv.z*azelref.y,
        protv.z*azelref.x - protv.x*azelref.z,
        protv.x*azelref.y - protv.y*azelref.x
    )

    gamma = math.asin(cp.radius())
    gsign = (1 if cp.z > 0. else -1.) * (1 if vect_j > 0. else -1.)

    return gamma * gsign * 180./math.pi