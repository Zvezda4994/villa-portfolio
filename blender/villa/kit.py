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

    def block(self, mat, f, lo, hi, step=0.08, skip=()):
        """A box lit per vertex with every face a fine grid (cabinet fronts, an island,
        shelves seen from below), so light falling across it stays smooth even from a
        quick draft bake. `mat` must be lit per vertex."""
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        faces = {
            "+y": ((x0, y1, z1), (dx, 0, 0), (0, 0, -dz)),
            "-y": ((x0, y0, z0), (dx, 0, 0), (0, 0, dz)),
            "+x": ((x1, y0, z1), (0, 0, -dz), (0, dy, 0)),
            "-x": ((x0, y0, z0), (0, 0, dz), (0, dy, 0)),
            "+z": ((x0, y0, z1), (dx, 0, 0), (0, dy, 0)),
            "-z": ((x1, y0, z0), (-dx, 0, 0), (0, dy, 0)),
        }
        for name, (o, u, v) in faces.items():
            if name in skip:
                continue
            nu = max(1, round(float(np.linalg.norm(u)) / step))
            nv = max(1, round(float(np.linalg.norm(v)) / step))
            verts, fc, _ = grid(o, u, v, nu, nv)
            self.mesh(mat, f, verts, fc, smooth=False)

    def grain(self, mat, f, lo, hi, step=0.08, skip=(), along=None):
        """Like `block`, for a material with a tiling texture that is lit per vertex
        (the walnut in the living room and the library): every face a fine grid, its
        texture laid in world metres, so the pattern lines up across neighbouring faces.
        The grain runs along the piece's longest side, or along the local axis named by
        `along` ("x", "y" or "z"). (The walnut picture's grain runs across it, along u.)"""
        from .materials import MATS
        tile = MATS[mat].get("tile", 1.0)
        (x0, y0, z0), (x1, y1, z1) = lo, hi
        dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
        local = "xyz".index(along) if along else int(np.argmax(np.abs((dx, dy, dz))))
        e = np.zeros(3)
        e[local] = 1.0
        run = int(np.argmax(np.abs(np.subtract(f(e), f((0, 0, 0))))))         # the grain's world axis
        faces = {
            "+y": ((x0, y1, z1), (dx, 0, 0), (0, 0, -dz)),
            "-y": ((x0, y0, z0), (dx, 0, 0), (0, 0, dz)),
            "+x": ((x1, y0, z1), (0, 0, -dz), (0, dy, 0)),
            "-x": ((x0, y0, z0), (0, 0, dz), (0, dy, 0)),
            "+z": ((x0, y0, z1), (dx, 0, 0), (0, dy, 0)),
            "-z": ((x1, y0, z0), (-dx, 0, 0), (0, dy, 0)),
        }
        for name, (o, u, v) in faces.items():
            if name in skip:
                continue
            nu = max(1, round(float(np.linalg.norm(u)) / step))
            nv = max(1, round(float(np.linalg.norm(v)) / step))
            verts, fc, _ = grid(o, u, v, nu, nv)
            world = f.many(verts)
            n = np.cross(np.subtract(world[nv + 1], world[0]), np.subtract(world[1], world[0])) if nu and nv else (0, 1, 0)
            axis = int(np.argmax(np.abs(n)))
            pick = ((2, 1), (0, 2), (0, 1))[axis]
            if pick[1] == run:
                pick = (pick[1], pick[0])
            uv = [(p[pick[0]] / tile, p[pick[1]] / tile) for p in world]
            self.b.mesh(self.g, mat, world, fc, smooth=False, uvs=[[uv[i] for i in face] for face in fc])

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

    def sweep(self, mat, path, r, segments=12, caps=True, colors=None):
        """A round tube along a path of world points (a lamp's arm, a cable). `r`
        is one radius or one per point. `colors` (a function of a point) paints it
        per vertex, for materials marked "albedo"."""
        verts, faces = sweep_geom(path, r, segments, caps)
        self.b.mesh(self.g, mat, verts, faces, colors=[colors(v) for v in verts] if colors else None)

    def mesh(self, mat, f, verts, faces, smooth=True, uvs=None):
        """Any shape given in local coordinates."""
        self.b.mesh(self.g, mat, f.many(verts), faces, smooth=smooth, uvs=uvs)


def sweep_geom(path, r, segments=12, caps=True):
    """Points and faces of a round tube along a path. Rings are kept from twisting by
    carrying each one's frame along from the last."""
    P = np.asarray(path, float)
    # repeated points give the tube no direction there (NaN points, which the export turns
    # into spikes to the world's origin): keep only points that move on
    keep = np.concatenate([[True], np.linalg.norm(np.diff(P, axis=0), axis=1) > 1e-6])
    P = P[keep]
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
    return verts, faces


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


def panel(kit, mat, origin, u, v, step=0.22):
    """A flat panel in world coordinates lit per vertex on a grid about `step` apart,
    facing along u x v: used to line a furnished room's walls over the house's own, so
    they stay smooth from a draft bake. Lay it at least 12 mm off the house's wall:
    the house file's positions are rounded to a few millimetres (gotcha 22)."""
    nu = max(1, int(round(float(np.linalg.norm(u)) / step)))
    nv = max(1, int(round(float(np.linalg.norm(v)) / step)))
    verts, faces, _ = grid(origin, u, v, nu, nv)
    kit.b.mesh(kit.g, mat, verts, faces, smooth=False)


def wall(kit, mat, origin, u, v, holes=(), step=0.15):
    """A whole wall's lining like `panel`, as one grid with holes left in it: each hole is
    (a0, a1, b0, b1), metres along u and along v from the origin (a door, or a headboard,
    a frame or a cabinet standing against the wall: points buried behind those bake dark,
    gotcha 26). The grid's lines pass through every hole's edges and the pieces share
    their points, so it shows none of the seams that separate panels side by side do."""
    o, u, v = np.asarray(origin, float), np.asarray(u, float), np.asarray(v, float)
    Lu, Lv = float(np.linalg.norm(u)), float(np.linalg.norm(v))
    eu, ev = u / Lu, v / Lv

    def lines(L, cuts):
        cuts = sorted({min(max(c, 0.0), L) for c in cuts})
        n = max(1, int(round(L / step)))
        out = set(cuts) | {0.0, L}
        for i in range(1, n):
            p = L * i / n
            if all(abs(p - c) > 0.3 * step for c in cuts):
                out.add(p)
        return sorted(out)
    As = lines(Lu, [h[0] for h in holes] + [h[1] for h in holes])
    Bs = lines(Lv, [h[2] for h in holes] + [h[3] for h in holes])
    nb = len(Bs)
    faces = []
    for i in range(len(As) - 1):
        for j in range(nb - 1):
            ac, bc = (As[i] + As[i + 1]) / 2, (Bs[j] + Bs[j + 1]) / 2
            if any(a0 < ac < a1 and b0 < bc < b1 for a0, a1, b0, b1 in holes):
                continue
            a, c = i * nb + j, (i + 1) * nb + j
            faces.append((a, c, c + 1, a + 1))
    used = sorted({n for f in faces for n in f})
    index = {n: k for k, n in enumerate(used)}
    verts = [tuple(o + eu * As[n // nb] + ev * Bs[n % nb]) for n in used]
    kit.b.mesh(kit.g, mat, verts, [tuple(index[n] for n in f) for f in faces], smooth=False)


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
