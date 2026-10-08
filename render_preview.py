"""Render preview.png (three views of peg-adapter.stl). Run with FreeCAD's Python:
    freecad.cmd -c "exec(open('render_preview.py').read())"
"""
import Mesh, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
m = Mesh.Mesh("peg-adapter.stl")
tris = [[tuple(p) for p in f.Points] for f in m.Facets]
fig = plt.figure(figsize=(18, 5.5))
for i, (el, az, t) in enumerate([(25, -60, "iso (rail runs front-back)"), (0, -90, "end view, looking along rail"), (-35, -60, "from below (plug + sleeve)"), (5, 0, "side view, rail runs left-right")]):
    ax = fig.add_subplot(1, 4, i + 1, projection="3d")
    ax.add_collection3d(Poly3DCollection(tris, facecolor="#6aa0d8", edgecolor="#2b4b6f", linewidth=0.1))
    bb = m.BoundBox
    h = max(bb.XLength, bb.YLength) / 2 + 1
    ax.set_xlim(-h, h); ax.set_ylim(-h, h); ax.set_zlim(0, bb.ZMax); ax.set_box_aspect((2 * h, 2 * h, bb.ZMax))
    ax.view_init(el, az); ax.set_title(t); ax.set_axis_off()
plt.tight_layout(); plt.savefig("preview.png", dpi=110)
print("ok")
