"""Layout checks for the figures: labels and map furniture must not cover relevant features.

Added in the layout revision of 2026-10-16.

Every check works in display (pixel) coordinates of the drawn figure:

* each label (text, legend, colour bar, north arrow, scale bar, annotation) is reduced to its bounding box,
  enlarged by a small pad;
* features that a label must not touch are given as shapely geometries in data coordinates (boundary lines,
  coastlines, markers, filled land areas) and transformed to display coordinates with the axes transform;
* a label must not intersect another label, any of the features listed for it, or leave its allowed frame
  (the axes for labels inside a map or plot; the figure for everything else).

The helpers return a list of human-readable problems; the figure scripts print the list (stdout only, so the
logs in results/logs/ are unchanged) and the tests call the same functions. An empty list means that no label
overlaps another label or a listed feature.
"""
from __future__ import annotations

from itertools import combinations

import numpy as np
import shapely
from shapely.geometry import Point, box


def renderer(fig):
    fig.canvas.draw()
    return fig.canvas.get_renderer()


def bbox(artist, r, pad=1.0):
    """Bounding box of an artist (Text, Legend, Axes, Patch, Annotation...) as a shapely box in pixels. For an
    annotation with text, only the text is measured (its leader line is meant to reach the feature)."""
    from matplotlib.text import Annotation, Text
    if isinstance(artist, Annotation) and artist.get_text():
        artist.update_positions(r)
        bb = Text.get_window_extent(artist, r)
    else:
        bb = artist.get_window_extent(r)
    return box(bb.x0 - pad, bb.y0 - pad, bb.x1 + pad, bb.y1 + pad)


def to_display(ax, geom):
    """Data-coordinate geometry -> display-coordinate geometry."""
    return shapely.transform(geom, lambda c: ax.transData.transform(c))


def points_display(ax, xy, radius_px):
    """Markers as small discs in display coordinates."""
    pts = ax.transData.transform(np.asarray(xy, float).reshape(-1, 2))
    return shapely.union_all([Point(p).buffer(radius_px) for p in pts])


def check(labels, features=None, frame=None, ignore_pairs=()):
    """labels: dict name -> (shapely box in pixels, list of feature names it must avoid, frame name or None);
    features: dict name -> geometry in pixels; frame: dict name -> shapely box in pixels.
    Returns a list of problems (empty when the layout is clean)."""
    features = features or {}
    frame = frame or {}
    out = []
    names = list(labels)
    for a, b in combinations(names, 2):
        if (a, b) in ignore_pairs or (b, a) in ignore_pairs:
            continue
        if labels[a][0].intersects(labels[b][0]):
            out.append(f'label "{a}" overlaps label "{b}"')
    for n in names:
        geom, avoid, fr = labels[n]
        for f in avoid:
            if f in features and geom.intersects(features[f]):
                out.append(f'label "{n}" covers {f}')
        if fr is not None and not frame[fr].contains(geom):
            out.append(f'label "{n}" leaves its frame ({fr})')
    return out


def report(name, problems, printer=print):
    if problems:
        for p in problems:
            printer(f'LAYOUT {name}: {p}')
    else:
        printer(f'LAYOUT {name}: no overlaps')
    return problems


def place_point_labels(ax, r, xy, texts, avoid_boxes=(), marker_px=5.0, fontsize=6.8, color='0.32',
                       offsets_pt=((4, 3), (4, -9), (-4, 3), (-4, -9), (6, -3), (-6, -3), (0, 6), (0, -12),
                                   (9, 6), (9, -12), (-9, 6), (-9, -12), (14, -3), (-14, -3))):
    """Greedy placement of point labels (scatter plots): for each point, the first offset whose text box does not
    overlap any marker, any label already placed, the given boxes, or the edge of the axes, and that is closer to its
    own point than to any other point (so that each label is read with its point). Offsets are in points;
    a positive x offset left-aligns the text, a negative one right-aligns it. texts may hold None for points that
    are not labelled. Returns (Text artists, their boxes, marker discs, problems)."""
    pts = ax.transData.transform(np.asarray(xy, float))
    markers = [Point(p).buffer(marker_px) for p in pts]
    frame = bbox(ax, r, pad=0)
    placed, arts, failed = [], [], []
    for i, (p, t) in enumerate(zip(xy, texts)):
        if t is None:                          # unlabelled point: its marker is still avoided
            continue
        best = None
        for dx, dy in offsets_pt:
            ha = 'left' if dx > 0 else ('right' if dx < 0 else 'center')
            art = ax.annotate(t, p, xytext=(dx, dy), textcoords='offset points', fontsize=fontsize, color=color,
                              ha=ha, va='bottom')
            g = bbox(art, r, pad=0.8)
            own = g.distance(Point(pts[i]))
            clash = (not frame.contains(g) or any(g.intersects(m) for j, m in enumerate(markers))
                     or any(g.intersects(q) for q in placed) or any(g.intersects(q) for q in avoid_boxes)
                     or any(g.distance(Point(q)) < own for j, q in enumerate(pts) if j != i))   # unambiguous: nearest to its point
            if not clash:
                best = (art, g)
                break
            art.remove()
        if best is None:                       # no free slot: keep the first offset and report it
            failed.append(f'point label "{t}" has no free position')
            dx, dy = offsets_pt[0]
            art = ax.annotate(t, p, xytext=(dx, dy), textcoords='offset points', fontsize=fontsize, color=color,
                              ha='left', va='bottom')
            best = (art, bbox(art, r, pad=0.8))
        placed.append(best[1]); arts.append(best[0])
    return arts, placed, markers, failed


def place_first_free(make, candidates, r, avoid, placed=(), frame=None, pad=1.5):
    """Generic greedy placement: make(candidate) draws an artist; the first candidate whose bounding box touches
    none of the geometries in `avoid`, none of the boxes in `placed` and stays inside `frame` is kept (the others
    are removed). Returns (artist, box, index of the candidate used or None when no candidate was free, in which
    case the first candidate is kept so that the problem is visible and reported by check())."""
    first = None
    for i, c in enumerate(candidates):
        art = make(c)
        g = bbox(art, r, pad=pad)
        ok = (frame is None or frame.contains(g)) and not any(g.intersects(a) for a in avoid) \
            and not any(g.intersects(q) for q in placed)
        if ok:
            if first is not None:
                first[0].remove()
            return art, g, i
        if first is None:
            first = (art, g)
        else:
            art.remove()
    return first[0], first[1], None


def ring_offsets(steps, angles=16):
    """Candidate offsets (dx, dy) on rings of increasing radius, starting with (0, 0)."""
    out = [(0.0, 0.0)]
    for s in steps:
        for k in range(angles):
            a = 2 * np.pi * k / angles
            out.append((s * np.cos(a), s * np.sin(a)))
    return out
