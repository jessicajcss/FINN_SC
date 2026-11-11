"""Map furniture shared by the figures: the north rose.

Added in the layout revision of 2026-10-16, at the authors' request for a better designed
north symbol, placed above the scale bar in every map. Since 2026-11-04 (authors' request) the rose is aligned to the
right end of the scale bar (align='right' in rose_above_bar) instead of centred over it.

The rose is an eight-point compass rose. The north point is the longest and is drawn in black and white; the east, south
and west points are shorter and drawn in dark grey and white; four short intercardinal points (light grey and white)
and a thin ring complete the rose. Each point is split along its axis into a dark and a light half, which gives the
usual bevelled look. An "N" sits above the north point. The shape is drawn in points (1/72 inch) around an anchor given
in data coordinates, so it keeps its proportions on maps with any aspect ratio.
"""
from __future__ import annotations

import numpy as np
from matplotlib.patches import Circle, Polygon
from matplotlib.transforms import Affine2D, ScaledTranslation


def north_rose(ax, x, y, size=16.0, dy=0.0, fontsize=None, zorder=8, dx=0.0):
    """Draw the north rose centred dx points to the right of and dy points above (x, y), a point in data coordinates. size = length of the north
    point in points (the east, south and west points are 0.62 x size, the intercardinal points 0.42 x size). Returns a
    list of (name, artist) pairs (names start with 'north'), so that the layout check can measure each piece."""
    fig = ax.figure
    tr = Affine2D().translate(dx / 72.0, dy / 72.0) + fig.dpi_scale_trans + ScaledTranslation(x, y, ax.transData)   # inches
    s = size / 72.0
    out = []

    def point(ang, length, waist, dark, z, name):
        a = np.radians(ang)
        tip = (length * np.cos(a), length * np.sin(a))
        for half, (side, fc) in enumerate(((a + np.pi / 4, dark), (a - np.pi / 4, 'white'))):   # counter-clockwise half dark
            p = Polygon([(0, 0), tip, (waist * np.cos(side), waist * np.sin(side))], closed=True, transform=tr,
                        facecolor=fc, edgecolor='black', lw=0.45, joinstyle='miter', zorder=z)
            ax.add_patch(p)
            out.append((f'north rose {name}{half}', p))

    ring = Circle((0, 0), 0.46 * s, transform=tr, fill=False, edgecolor='black', lw=0.45, zorder=zorder - 0.2)
    ax.add_patch(ring)
    out.append(('north rose ring', ring))
    for ang, nm in ((45, 'NE'), (135, 'NW'), (225, 'SW'), (315, 'SE')):
        point(ang, 0.42 * s, 0.13 * s, '0.62', zorder - 0.1, nm)
    for ang, nm in ((0, 'E'), (270, 'S'), (180, 'W')):
        point(ang, 0.62 * s, 0.26 * s, '0.35', zorder, nm)
    point(90, s, 0.26 * s, 'black', zorder, 'N')
    n = ax.annotate('N', (x, y), xytext=(dx, dy + size + 1.5), textcoords='offset points', ha='center', va='bottom',
                    fontsize=fontsize or max(6.0, 0.55 * size), fontweight='bold', zorder=zorder)
    out.append(('north N', n))
    return out


def rose_above_bar(ax, x, y_top, label_fs, size=16.0, gap=3.0, align='center'):
    """North rose over a scale bar whose top edge is at y_top in data coordinates and whose labels (font size
    label_fs) sit 2 points above that edge: the south point of the rose starts gap points above the labels.
    align='center': x is the centre of the bar and the rose is centred on it; align='right': x is the right end of
    the bar and the east point of the rose ends at it (rose right-justified above the bar)."""
    dx = -0.62 * size if align == 'right' else 0.0
    return north_rose(ax, x, y_top, size=size, dy=2.0 + 1.25 * label_fs + gap + 0.62 * size, dx=dx)
