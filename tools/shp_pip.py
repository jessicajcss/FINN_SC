"""Minimal shapefile (polygon) reader and point-in-polygon assignment
(matplotlib.path, non-zero winding) used to attribute FINN fire records to
IBGE municipalities / mesoregions. No GIS dependencies required."""
import struct, numpy as np
from matplotlib.path import Path

def read_dbf(p, enc='latin-1'):
    with open(p, 'rb') as fh:
        nrec, hlen, rlen = struct.unpack('<xxxxIHH20x', fh.read(32))
        fields = []
        while True:
            d = fh.read(32)
            if d[0] == 0x0D: break
            fields.append((d[:11].split(b'\x00')[0].decode(), d[16]))
        fh.seek(hlen); rows = []
        for _ in range(nrec):
            r = fh.read(rlen)[1:]; pos = 0; row = {}
            for n, ln in fields:
                row[n] = r[pos:pos + ln].decode(enc, 'replace').strip(); pos += ln
            rows.append(row)
    return rows

def read_polygons(p):
    """Return list of (bbox, Path) per record, in record order."""
    out = []
    with open(p, 'rb') as fh:
        fh.seek(100)
        while True:
            h = fh.read(8)
            if len(h) < 8: break
            _, clen = struct.unpack('>ii', h)
            content = fh.read(clen * 2)
            stype = struct.unpack('<i', content[:4])[0]
            if stype == 0:
                out.append((None, None)); continue
            xmin, ymin, xmax, ymax = struct.unpack('<4d', content[4:36])
            nparts, npts = struct.unpack('<ii', content[36:44])
            parts = struct.unpack('<%di' % nparts, content[44:44 + 4 * nparts])
            pts = np.frombuffer(content[44 + 4 * nparts:44 + 4 * nparts + 16 * npts], dtype='<f8').reshape(npts, 2)
            verts, codes = [], []
            bounds = list(parts) + [npts]
            for i in range(nparts):
                ring = pts[bounds[i]:bounds[i + 1]]
                verts.append(ring); c = np.full(len(ring), Path.LINETO, dtype=np.uint8); c[0] = Path.MOVETO; codes.append(c)
            out.append(((xmin, ymin, xmax, ymax), Path(np.vstack(verts), np.concatenate(codes))))
    return out

def assign(lon, lat, polys, names):
    """Assign each point to the first polygon containing it; '' if none."""
    lon = np.asarray(lon, float); lat = np.asarray(lat, float)
    res = np.array([''] * len(lon), dtype=object)
    xy = np.column_stack([lon, lat])
    for (bb, path), nm in zip(polys, names):
        if bb is None: continue
        m = (lon >= bb[0]) & (lon <= bb[2]) & (lat >= bb[1]) & (lat <= bb[3]) & (res == '')
        if not m.any(): continue
        idx = np.where(m)[0]
        inside = path.contains_points(xy[idx])
        res[idx[inside]] = nm
    return res

def utm_forward(lon, lat, lon0=-51.0, south=True, a=6378137.0, f=1/298.257223563, k0=0.9996):
    """WGS84 geographic -> Transverse Mercator (Snyder 1987, eqs. 8-9 to 8-15);
    default UTM zone 22S. Sub-metre accuracy within the zone."""
    lon = np.radians(np.asarray(lon, float)); lat = np.radians(np.asarray(lat, float)); l0 = np.radians(lon0)
    e2 = f * (2 - f); ep2 = e2 / (1 - e2)
    N = a / np.sqrt(1 - e2 * np.sin(lat) ** 2); T = np.tan(lat) ** 2; C = ep2 * np.cos(lat) ** 2
    A = (lon - l0) * np.cos(lat)
    M = a * ((1 - e2/4 - 3*e2**2/64 - 5*e2**3/256) * lat - (3*e2/8 + 3*e2**2/32 + 45*e2**3/1024) * np.sin(2*lat)
             + (15*e2**2/256 + 45*e2**3/1024) * np.sin(4*lat) - (35*e2**3/3072) * np.sin(6*lat))
    x = k0 * N * (A + (1 - T + C) * A**3 / 6 + (5 - 18*T + T**2 + 72*C - 58*ep2) * A**5 / 120) + 500000.0
    y = k0 * (M + N * np.tan(lat) * (A**2/2 + (5 - T + 9*C + 4*C**2) * A**4/24 + (61 - 58*T + T**2 + 600*C - 330*ep2) * A**6/720))
    if south: y = y + 10000000.0
    return x, y
