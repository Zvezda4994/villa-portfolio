"""Building blocks for furnishing a room: boxes, cushions, turned and swept
shapes, laid out in a piece of furniture's own frame.

The dining room and the pool deck grew their own versions of these; the rooms
furnished since use this one. A Kit is tied to one builder, one group ("ground"
or "upper", so the furniture shows and hides with its floor) and one lightmap.

Frames come from pool.py: Frame(pos, yaw) turns a local point (x across,
y up, z forward) into the world, with yaw in degrees (+z toward +x).
"""
import math

import numpy as np

from .dining import _lathe, _rounded_box
from .pool import Frame, axes, rot  # noqa: F401  (re-exported for the room scripts)


class Kit:
    def __init__(self, b, group, atlas):
        self.b, self.g, self.atlas = b, group, atlas

    # ---- flat pieces (lightmapped if the material is "baked") -----------------------
    def box(self, mat, f, lo, hi, tilt=0.0, pivot=(0, 0, 0), skip=(), density=1.0, over=None):
        """A box between local corners lo and hi in frame f, optionally tipped about
        its x axis by `tilt` degrees round `pivot`. `over` changes single faces, e.g.
        {"+y": dict(mat="whiteboard", uv=[...], density=2)}."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        corners = {
            "+x": [(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)],
            "-x": [(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)],
            "+y": [(x0, y1, z1), (x1, y1, z1), (x1, y1, z0), (x0, y1, z0)],
            "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            "-z": [(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)],
        }
        T = rot(x=tilt)
        pv = np.asarray(pivot, float)
        for name, pts in corners.items():
            if name in skip:
                continue
            o = dict(mat=mat, density=density, uv=None)
            o.update((over or {}).get(name, {}))
            world = [f(pv + T @ (np.asarray(p, float) - pv)) for p in pts]
            self.b.quad(self.g, o["mat"], world, self.atlas, o["density"], uv=o["uv"])

    def slab(self, mat, f, lo, hi, step=0.06, skip=()):
        """A box lit per vertex whose top is a fine grid, so light falling across it
        (a screen's glow on a desk) comes out smooth even from a quick draft bake."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        self.box(mat, f, lo, hi, skip=tuple(skip) + ("+y",))
        nx, nz = max(1, round((x1 - x0) / step)), max(1, round((z1 - z0) / step))
        verts = [(x0 + (x1 - x0) * i / nx, y1, z0 + (z1 - z0) * j / nz) for i in range(nx + 1) for j in range(nz + 1)]
        faces = [(i * (nz + 1) + j, i * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j + 1, (i + 1) * (nz + 1) + j)
                 for i in range(nx) for j in range(nz)]
        self.b.mesh(self.g, mat, f.many(verts), faces, smooth=False)

    def quad(self, mat, f, pts, density=1.0, uv=None):
        """One rectangle from four local corners, anticlockwise seen from the front."""
        self.b.quad(self.g, mat, f.many(pts), self.atlas, density, uv=uv)

    # ---- curved pieces (lit per vertex) ------------------------------------------------
    def soft(self, mat, f, centre, size, r, n=3, tilt=0.0, pivot=(0, 0, 0), turn=0.0):
        """A box with rounded edges (cushions, keycaps, a monitor's back): local
        centre and size, optionally turned `turn` degrees about its own vertical
        and tipped `tilt` degrees about x round `pivot`."""
        verts, faces = _rounded_box((0, 0, 0), size, r, n)
        R = rot(y=turn)
        c = np.asarray(centre, float)
        T = rot(x=tilt)
        pv = np.asarray(pivot, float)
        world = [f(pv + T @ (c + R @ np.asarray(v, float) - pv)) for v in verts]
        self.b.mesh(self.g, mat, world, faces)

    def lathe(self, mat, f, profile, segments=32, at=(0, 0, 0)):
        """Spin a profile of (radius, height) points, written bottom up, round the
        local vertical through `at`."""
        verts, faces = _lathe(profile[::-1], segments)
        a = np.asarray(at, float)
        self.b.mesh(self.g, mat, [f(a + np.asarray(v)) for v in verts], faces)

    def disc(self, mat, f, centre, r, segments=32, down=False):
        """A flat round disc facing up (or down), at a local centre."""
        cx, cy, cz = centre
        ring = [(cx + r * math.cos(2 * math.pi * k / segments), cy, cz + r * math.sin(2 * math.pi * k / segments))
                for k in range(segments)]
        verts = f.many([(cx, cy, cz)] + ring)
        faces = [(0, (k + 1) % segments + 1, k + 1) if not down else (0, k + 1, (k + 1) % segments + 1)
                 for k in range(segments)]
        self.b.mesh(self.g, mat, verts, faces, smooth=False)

    def tube(self, mat, p0, p1, r, segments=12, r1=None, caps=True, step=0.05):
        """A round rod between two world points (tapering to r1 if given). It gets a
        ring of points every `step` metres: light is baked at the points, and a rod
        whose only rings are buried in what it's fixed to would come out black."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        n = max(1, int(math.ceil(np.linalg.norm(p1 - p0) / step)))
        path = [tuple(p0 + (p1 - p0) * i / n) for i in range(n + 1)]
        self.sweep(mat, path, r if r1 is None else [r, r1], segments, caps)

    def rod(self, mat, p0, p1, thick, n=1):
        """A slim square bar with softened edges between two world points."""
        p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
        d = p1 - p0
        length = float(np.linalg.norm(d))
        M = axes(d, (0.0, 1.0, 0.0) if abs(d[1]) < 0.9 * length else (1.0, 0.0, 0.0))
        V, F = _rounded_box((0, 0, 0), (thick, thick, length), thick * 0.3, n)
        self.b.mesh(self.g, mat, [tuple((p0 + p1) / 2 + M @ np.asarray(v)) for v in V], F)

    def sweep(self, mat, path, r, segments=12, caps=True):
        """A round tube along a path of world points (a lamp's arm, a cable). `r`
        is one radius or one per point. Rings are kept from twisting by carrying
        each one's frame along from the last."""
        P = np.asarray(path, float)
        n = len(P)
        radii = np.broadcast_to(np.asarray(r, float), (n,)) if np.ndim(r) == 0 else np.interp(
            np.linspace(0, 1, n), np.linspace(0, 1, len(r)), np.asarray(r, float))
        tangents = np.gradient(P, axis=0)
        tangents /= np.linalg.norm(tangents, axis=1, keepdims=True)
        ref = np.array([0.0, 1.0, 0.0]) if abs(tangents[0][1]) < 0.9 else np.array([1.0, 0.0, 0.0])
        u = np.cross(tangents[0], ref)
        u /= np.linalg.norm(u)
        verts, faces = [], []
        for i in range(n):
            t = tangents[i]
            u = u - t * np.dot(u, t)
            u /= np.linalg.norm(u)
            v = np.cross(t, u)
            for k in range(segments):
                a = 2 * math.pi * k / segments
                verts.append(tuple(P[i] + radii[i] * (math.cos(a) * u + math.sin(a) * v)))
        for i in range(n - 1):
            for k in range(segments):
                a, c = i * segments + k, i * segments + (k + 1) % segments
                faces.append((a, c, c + segments, a + segments))
        if caps:
            for i, flip in ((0, True), (n - 1, False)):
                centre = len(verts)
                verts.append(tuple(P[i]))
                for k in range(segments):
                    a, c = i * segments + k, i * segments + (k + 1) % segments
                    faces.append((centre, c, a) if flip else (centre, a, c))
        self.b.mesh(self.g, mat, verts, faces)

    def mesh(self, mat, f, verts, faces, smooth=True, uvs=None):
        """Any shape given in local coordinates."""
        self.b.mesh(self.g, mat, f.many(verts), faces, smooth=smooth, uvs=uvs)


def arc(p0, p1, bulge, n=16, up=(0.0, 1.0, 0.0)):
    """Points along a curve from p0 to p1 that bows out `bulge` metres toward `up`."""
    p0, p1, up = np.asarray(p0, float), np.asarray(p1, float), np.asarray(up, float)
    out = []
    for i in range(n + 1):
        t = i / n
        out.append(tuple(p0 + (p1 - p0) * t + up * bulge * math.sin(math.pi * t)))
    return out


def cushion(size, r, n=3, div=8):
    """A rounded box like dining._rounded_box, but with its flat middles divided
    into `div` strips each way, so it can be bent and shaped afterwards (a chair's
    back that wraps round the sitter, a dished seat). Centred on the origin."""
    hx, hy, hz = size[0] / 2, size[1] / 2, size[2] / 2
    ix, iy, iz = max(hx - r, 0), max(hy - r, 0), max(hz - r, 0)
    index, verts, faces = {}, [], []

    def vert(p):
        q = (max(-ix, min(ix, p[0])), max(-iy, min(iy, p[1])), max(-iz, min(iz, p[2])))
        d = (p[0] - q[0], p[1] - q[1], p[2] - q[2])
        m = math.sqrt(d[0] ** 2 + d[1] ** 2 + d[2] ** 2) or 1.0
        out = (q[0] + d[0] / m * r, q[1] + d[1] / m * r, q[2] + d[2] / m * r)
        key = tuple(round(v, 6) for v in out)
        if key not in index:
            index[key] = len(verts)
            verts.append(out)
        return index[key]

    def steps(h, i):
        inner = list(np.linspace(-i, i, div + 1)) if i > 1e-6 else [0.0]
        ramp = [-(i + (h - i) * k / n) for k in range(n, 0, -1)]
        return ramp + inner + [-v for v in reversed(ramp)]

    s = (steps(hx, ix), steps(hy, iy), steps(hz, iz))
    for axis, sign in ((0, 1), (0, -1), (1, 1), (1, -1), (2, 1), (2, -1)):
        a, c = [k for k in range(3) if k != axis]
        grid = []
        for va in s[a]:
            row = []
            for vc in s[c]:
                p = [0.0, 0.0, 0.0]
                p[axis], p[a], p[c] = (hx, hy, hz)[axis] * sign, va, vc
                row.append(vert(p))
            grid.append(row)
        for i in range(len(s[a]) - 1):
            for j in range(len(s[c]) - 1):
                f = (grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1])
                # keep every face pointing outward
                p = [np.array(verts[k]) for k in f]
                nrm = np.cross(p[1] - p[0], p[3] - p[0])
                centre = sum(p) / 4
                faces.append(f if np.dot(nrm, centre) >= 0 else f[::-1])
    return verts, faces


def grid(origin, u, v, nu, nv):
    """A flat grid of quads: origin plus fractions of the edge vectors u and v.
    Faces point along u x v. Returns verts, faces and per-face uvs (0..1)."""
    o, u, v = np.asarray(origin, float), np.asarray(u, float), np.asarray(v, float)
    verts = [tuple(o + u * i / nu + v * j / nv) for i in range(nu + 1) for j in range(nv + 1)]
    faces, uvs = [], []
    for i in range(nu):
        for j in range(nv):
            a, c = i * (nv + 1) + j, (i + 1) * (nv + 1) + j
            faces.append((a, c, c + 1, a + 1))
            uvs.append([(i / nu, j / nv), ((i + 1) / nu, j / nv), ((i + 1) / nu, (j + 1) / nv), (i / nu, (j + 1) / nv)])
    return verts, faces, uvs
