import os, sys
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import matplotlib.pyplot as plt
sys.path.insert(1, os.path.join(sys.path[0], '../..'))

from pysoltrace import api, dot_h, math_utils
import pysoltrace.soltrace_constants as _STC
import pysoltrace.soltrace_json as stJSON
from pysoltrace.point import Point

"""init api"""
stapi = api()

"""NSTTF information"""
DNI = 930 # [W/m^2]
LATITUDE  = 35.962278    # [deg], NSTTF original tower latitude (approximate)
LONGITUDE = -106.5122622 # [deg], NSTTF original tower longitude (approximate)
TZ     = 'MST'
TZINFO = ZoneInfo("America/Denver")
ST_LOC = _STC.sun_location(LATITUDE, LONGITUDE, -7.0)
# TODO: util to convert built-in datetime to st_datetime
ST_DT  = _STC.sun_datetime(2025, # year
                                 6,    # month
                                 20,   # day
                                 12,   # hour
                                 34,   # minute
                                 56)   # second

"""
convert between (+x: west, +y: zenith, +z: north)
            and (+x: east, +y: north,  +z: zenith)
"""
CONVERT_COORDS = np.array([[-1., 0., 0.],
                           [ 0., 0., 1.],
                           [ 0., 1., 0.]])

# file set up
current_dir = Path(__file__).parent
data_dir    = current_dir / 'nsttf_data'
coords_f    = data_dir / 'coordinates.csv'
ids_f       = data_dir / 'ids.csv'
canting_dir = data_dir / 'internal_canting'

def pretty(struct):
    s = type(struct).__name__ + ': {\n'
    for field in struct._fields_:
        s += f'  {field[0]}: {getattr(struct, field[0])}\n'
    s += '}\n'
    return s

# TODO: def create_nsttf(stapi, sun_pos): stapi.clear() .. stapi.batch.clear() ...
#       def update_nsttf(stapi, sun_pos): stapi.batch.clear() ...

################################
# set up optical property sets #
################################

rec_set  = _STC.optical_properties_set(b'receiver', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
rec_face = _STC.optical_properties_face(0, 0, .95, .2, _STC.optical_error_dist.GAUSSIAN.value)
RECEIVER_OPTICAL_REF = stapi.data.optic.add(rec_set, rec_face, rec_face)

helio_set   = _STC.optical_properties_set(b'heliostat', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
helio_front = _STC.optical_properties_face(0, 0.885, 1.2, .05, _STC.optical_error_dist.GAUSSIAN.value)
helio_back  = _STC.optical_properties_face(0, 0, 1.2, .05, _STC.optical_error_dist.GAUSSIAN.value)
HELIOSTAT_OPTICAL_REF = stapi.data.optic.add(helio_set, helio_front, helio_back)

ap_set   = _STC.optical_properties_set(b'aperture', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
ap_front = _STC.optical_properties_face(1, 0.5, 523.6, 0.1, _STC.optical_error_dist.GAUSSIAN.value)
ap_back  = _STC.optical_properties_face(1, 0, 523.6, 0.1, _STC.optical_error_dist.GAUSSIAN.value)
APERTURE_OPTICAL_REF = stapi.data.optic.add(ap_set, ap_front, ap_back)

tower_set  = _STC.optical_properties_set(b'tower', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
tower_face = _STC.optical_properties_face(1, 0, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
TOWER_OPTICAL_REF = stapi.data.optic.add(tower_set, tower_face, tower_face)

snout_set   = _STC.optical_properties_set(b'snout', 1.1, 1.1, _STC.optical_interaction.REFLECTION.value)
snout_front = _STC.optical_properties_face(0, 0.2, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
snout_back  = _STC.optical_properties_face(0, 0, 0.95, 0.2, _STC.optical_error_dist.GAUSSIAN.value)
SNOUT_OPTICAL_REF = stapi.data.optic.add(snout_set, snout_front, snout_back)

########################
# set up G3P3 receiver #
########################

g3p3_stage_pos = np.array([-40, 8.5, 44.8177])
g3p3_stage_aim = np.array([0,   122, 44.8177])
g3p3_unstager = math_utils.get_unstager(g3p3_stage_pos, g3p3_stage_aim, 0)

G3P3_GROUP = 0
G3P3 = {}

# aperture
ap_el_args = _STC.element(*g3p3_unstager([0, 0, 0.662347]),
                          *g3p3_unstager([0, 1, 0.662347]),
                          0, True, False,
                          _STC.aperture.RECTANGLE.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
APERTURE_ID = \
    stapi.data.element.add(ap_el_args,
                           APERTURE_OPTICAL_REF,
                           [1.32475, 1.32475], [])
G3P3[APERTURE_ID] = ap_el_args

# tunnel bottom
tb_el_args = _STC.element(*g3p3_unstager([0, 0, 0]),
                          *g3p3_unstager([0, 0.608432, 0.793606]),
                          0, True, False,
                          _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
TUNNEL_BOTTOM_ID = \
    stapi.data.element.add(tb_el_args,
                           SNOUT_OPTICAL_REF,
                           [0.662347, 0, -0.662347, 0, -1.65, -0.945053, 1.65, -0.945053], [])
G3P3[TUNNEL_BOTTOM_ID] = tb_el_args

# tunnel east
te_el_args = _STC.element(*g3p3_unstager([0.662347, 0, 0]),
                          *g3p3_unstager([0.057569, 0.796394, 0]),
                          0, True, False,
                          _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
TUNNEL_EAST_ID = \
    stapi.data.element.add(te_el_args,
                           SNOUT_OPTICAL_REF,
                           [0, 1.32475, -1.24012, 1.175, -1.24012, -0.575, 0, 0], [])
G3P3[TUNNEL_EAST_ID] = te_el_args

# tunnel west
tw_el_args = _STC.element(*g3p3_unstager([-0.662347, 0, 0]),
                          *g3p3_unstager([-0.057569, 0.796394, 0]),
                          0, True, False,
                          _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
TUNNEL_WEST_ID = \
    stapi.data.element.add(tw_el_args,
                           SNOUT_OPTICAL_REF,
                           [1.24012, 1.175, 0, 1.32475, 0, 0, 1.24012, -0.575], [])
G3P3[TUNNEL_WEST_ID] = tw_el_args

# tunnel top
tt_el_args = _STC.element(*g3p3_unstager([0, 0, 1.32475]),
                          *g3p3_unstager([0, 0.195795, 0.344105]),
                          0, True, False,
                          _STC.aperture.IRREGULAR_QUADRILATERAL.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
TUNNEL_TOP_ID = \
    stapi.data.element.add(tt_el_args,
                           SNOUT_OPTICAL_REF,
                           [0.662347, 0, -0.662347, 0, -1.65, -0.764803, 1.65, -0.764803], [])
G3P3[TUNNEL_TOP_ID] = tt_el_args

# shield northeast
sne_el_args = _STC.element(*g3p3_unstager([2.65, 0.75, 2.175]),
                           *g3p3_unstager([2.65, 1.75, 2.175]),
                           0, True, False,
                           _STC.aperture.RECTANGLE.value,
                           _STC.surface.FLAT.value,
                           G3P3_GROUP)
SHIELD_NORTHEAST_ID = \
    stapi.data.element.add(sne_el_args,
                           SNOUT_OPTICAL_REF,
                           [2, 2], [])
G3P3[SHIELD_NORTHEAST_ID] = sne_el_args

# shield north
sn_el_args = _STC.element(*g3p3_unstager([0, 0.75, 2.175]),
                          *g3p3_unstager([0, 1.75, 2.175]),
                          0, True, False,
                          _STC.aperture.RECTANGLE.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
SHIELD_NORTH_ID = \
    stapi.data.element.add(sn_el_args,
                           SNOUT_OPTICAL_REF,
                           [3.3, 2], [])
G3P3[SHIELD_NORTH_ID] = sn_el_args

# shield northwest
snw_el_args = _STC.element(*g3p3_unstager([-2.65, 0.75, 2.175]),
                           *g3p3_unstager([-2.65, 1.75, 2.175]),
                           0, True, False,
                           _STC.aperture.RECTANGLE.value,
                           _STC.surface.FLAT.value,
                           G3P3_GROUP)
SHIELD_NORTHWEST_ID = \
    stapi.data.element.add(snw_el_args,
                           SNOUT_OPTICAL_REF,
                           [2, 2], [])
G3P3[SHIELD_NORTHWEST_ID] = snw_el_args

# shield east
se_el_args = _STC.element(*g3p3_unstager([2.65, 0.75, 0.375]),
                          *g3p3_unstager([2.65, 1.75, 0.245313]),
                          0, True, False,
                          _STC.aperture.RECTANGLE.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
SHIELD_EAST_ID = \
    stapi.data.element.add(se_el_args,
                           SNOUT_OPTICAL_REF,
                           [2, 1.75], [])
G3P3[SHIELD_EAST_ID] = se_el_args

# shield west
sw_el_args = _STC.element(*g3p3_unstager([-2.65, 0.75, 0.375]),
                          *g3p3_unstager([-2.65, 1.75, 0.245313]),
                          0, True, False,
                          _STC.aperture.RECTANGLE.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
SHIELD_WEST_ID = \
    stapi.data.element.add(sw_el_args,
                           SNOUT_OPTICAL_REF,
                           [2, 1.75], [])
G3P3[SHIELD_WEST_ID] = sw_el_args

# shield southeast
sse_el_args = _STC.element(*g3p3_unstager([2.65, 0.75, -1.575]),
                           *g3p3_unstager([2.65, 1.75, -1.575]),
                           0, True, False,
                           _STC.aperture.RECTANGLE.value,
                           _STC.surface.FLAT.value,
                           G3P3_GROUP)
SHIELD_SOUTHEAST_ID = \
    stapi.data.element.add(sse_el_args,
                           SNOUT_OPTICAL_REF,
                           [2, 2], [])
G3P3[SHIELD_SOUTHEAST_ID] = sse_el_args

# shield south
ss_el_args = _STC.element(*g3p3_unstager([0, 0.75, -1.575]),
                          *g3p3_unstager([0, 1.75, -1.575]),
                          0, True, False,
                          _STC.aperture.RECTANGLE.value,
                          _STC.surface.FLAT.value,
                          G3P3_GROUP)
SHIELD_SOUTH_ID = \
    stapi.data.element.add(ss_el_args,
                           SNOUT_OPTICAL_REF,
                           [3.3, 2], [])
G3P3[SHIELD_SOUTH_ID] = ss_el_args

# shield southwest
ssw_el_args = _STC.element(*g3p3_unstager([-2.65, 0.75, -1.575]),
                           *g3p3_unstager([-2.65, 1.75, -1.575]),
                           0, True, False,
                           _STC.aperture.RECTANGLE.value,
                           _STC.surface.FLAT.value,
                           G3P3_GROUP)
SHIELD_SOUTHWEST_ID = \
    stapi.data.element.add(ssw_el_args,
                           SNOUT_OPTICAL_REF,
                           [2, 2], [])
G3P3[SHIELD_SOUTHWEST_ID] = ssw_el_args

# measurement plane
# curtain

########################
# Solar 1 target setup #
########################

SOLAR_1_TARGET  = [5.65, 4.25, 64.54]
target_aim      = [5.65, 100, 64.54] # looking directly north
SOLAR_1_GROUP   = G3P3_GROUP + 1
solar_1_el_args = _STC.element(*SOLAR_1_TARGET, 
                               *target_aim,
                               0, True, False,
                               _STC.aperture.RECTANGLE.value,
                               _STC.surface.FLAT.value,
                               SOLAR_1_GROUP)
SOLAR_1_ID = \
    stapi.data.element.add(ssw_el_args,
                           RECEIVER_OPTICAL_REF,
                           [2, 2], [])

# heliostat and facet information
PED_HEIGHT = 4.02           # [m], heliostat pedistal height
TRACK_ERR  = 0.0005         # [rad], heliostat tracking error
PIV_OFFSET = 0.1778         # [m], facet pivot offset
RECT_AP    = 1.2192         # [m], facet side length
PARA_SURF  = .5 / 0.0034203 # [m], parabolic focal length
CANT_ERR   = 0.0017         # [rad], facet canting error

# debugging plotting utils
def _plot_projection(ax, pairs, axis_pair, labels):
    """Draw a single 2D projection (quiver plot) onto the given axes.
 
    axis_pair: tuple of indices into the 3D point, e.g. (0, 1) for X-Y.
    labels: tuple of axis label strings, e.g. ("X", "Y").
    """
    i, j = axis_pair
 
    starts_i, starts_j = [], []
    vecs_i, vecs_j = [], []
 
    for start, end in pairs:
        starts_i.append(start[i])
        starts_j.append(start[j])
        vecs_i.append(end[i] - start[i])
        vecs_j.append(end[j] - start[j])
 
    starts_i = np.array(starts_i)
    starts_j = np.array(starts_j)
    vecs_i = np.array(vecs_i)
    vecs_j = np.array(vecs_j)
 
    ax.quiver(
        starts_i, starts_j, vecs_i, vecs_j,
        angles="xy", scale_units="xy", scale=1,
        color="steelblue", width=0.003,
        headwidth=4, headlength=5, alpha=0.85,
    )
 
    # Include both start and end points when setting axis limits so
    # every arrow is fully visible, with a little padding.
    all_i = np.concatenate([starts_i, starts_i + vecs_i])
    all_j = np.concatenate([starts_j, starts_j + vecs_j])
    if len(all_i) > 0:
        pad_i = max((all_i.max() - all_i.min()) * 0.05, 1.0)
        pad_j = max((all_j.max() - all_j.min()) * 0.05, 1.0)
        ax.set_xlim(all_i.min() - pad_i, all_i.max() + pad_i)
        ax.set_ylim(all_j.min() - pad_j, all_j.max() + pad_j)
 
    ax.set_xlabel(labels[0])
    ax.set_ylabel(labels[1])
    ax.set_title(f"{labels[0]}-{labels[1]} projection")
    # ax.set_aspect("equal", adjustable="datalim")
    ax.grid(True, linestyle="--", alpha=0.4)
 
 
def plot_all_projections(pairs, show=True, save_prefix=None):
    """Create three separate figures: X-Y, Y-Z, and X-Z projections of
    the given list of (start, end) 3D point pairs.
 
    Parameters
    ----------
    pairs : list of ((x1,y1,z1), (x2,y2,z2))
    show : bool -- whether to call plt.show() at the end
    save_prefix : str or None -- if given, each figure is saved as
        "<save_prefix>_xy.png", "<save_prefix>_yz.png", "<save_prefix>_xz.png"
    """
    projections = [
        ((0, 1), ("X", "Y"), "xy"),
        ((1, 2), ("Y", "Z"), "yz"),
        ((0, 2), ("X", "Z"), "xz"),
    ]
 
    figures = []
    for axis_pair, labels, tag in projections:
        fig, ax = plt.subplots(figsize=(7, 7))
        _plot_projection(ax, pairs, axis_pair, labels)
        fig.tight_layout()
        figures.append(fig)
        if save_prefix:
            fig.savefig(f"{save_prefix}_{tag}.png", dpi=150)
 
    if show:
        plt.show()
 
    return figures


if __name__ == '__main__':
    # print(pretty(ap_el_args))
    # print(type(ap_el_args))
    # print(type(ctypes.pointer(ap_el_args)))
    # test_unstager = math_utils.get_unstager(CONVERT_COORDS @ g3p3_stage_pos, CONVERT_COORDS @ g3p3_stage_aim, 0)

    # print(test_unstager(CONVERT_COORDS @ np.array([0, 0, 0.662347])))
    # print(test_unstager(CONVERT_COORDS @ np.array([0, 0, 0.662347])))

    print(__file__)
    # print(Path(__file__).parent / 'nsttf_data')
    # print(Path(__file__).parent / 'nsttf_data' / 'coordinates.csv')
    # print(Path(__file__).parent / 'nsttf_data' / 'ids.csv')

    # print(math_utils.zrot_from_azel([0, 1, 0]))
    # # test batch
    # stapi.batch(True)

    # print(stapi.data.optic.num())
    # print(stapi.data.element.num())

    # print(stapi.data.element.get(1)[0])
    # print(stapi.data.element.get(2)[0])
    # print(stapi.data.element.get(2)[1])
    # print(stapi.data.element.get(3)[0])

    pairs = [
        ([el.x, el.y, el.z], [el.ax, el.ay, el.az])
        for el in G3P3.values()
    ]
    # pairs.append(([solar_1_el_args.x, solar_1_el_args.y, solar_1_el_args.z], [solar_1_el_args.ax, solar_1_el_args.ay, solar_1_el_args.az]))

    plot_all_projections(pairs)
