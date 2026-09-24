#!/usr/bin/env python3
"""
Peg-to-rail adapter for the Novilla B-F10014 bed frame centre leg.

The steel centre peg (25 mm round tube) broke off the rail. This clip
re-seats it: a plug underneath slides down inside the tube, a loose outer
sleeve (bored out wide enough to clear the weld seams on the peg) boxes it in,
the peg rim butts against the floor, and two side walls with snap lips clip
over the plain 27 x 27 mm rail (placed clear of the crossbar and the thicker
plated section). Optional screw holes in the walls as a backup.

    rail load -> 3 mm floor -> steel peg rim   (plastic is only in compression)

Coordinates: rail runs along Y, peg axis is Z, floor top (where the rail sits)
is z = 0. The part prints upright, socket face down, no supports.

Run with FreeCAD's Python:
    freecad.cmd -c "exec(open('peg_adapter.py').read())"
Outputs: peg-adapter.stl (full part), peg-adapter-fittest.stl (floor + 10 mm plug and sleeve, for checking the fit)
"""
import os
import FreeCAD as App
import Part
import Mesh

V = App.Vector
OUT = os.environ.get("OUT_DIR", os.getcwd())

# ---------------------------------------------------------------- parameters
PEG_OD   = 25.0     # measured outside diameter of the steel peg
PEG_ID   = 22.0     # measured inside diameter of the peg
FIT      = 0.25     # radial clearance on each face of the socket (PETG, 0.4 nozzle)
RIB_BITE = 0.35     # how far the crush ribs on the plug reach past PEG_ID/2

RAIL_W   = 27.0     # width of the rail where the adapter clips on
RAIL_H   = 27.0     # height of the rail there
RAIL_CLR = 0.3      # total side clearance around the rail (snug push fit)
LIP      = 1.5      # how far each snap lip reaches over the top edges of the rail
SCREW_D  = 3.5      # hole through each wall for a sheet-metal screw; 0 = none

FLOOR    = 3.0      # plastic between rail and peg rim (raises the peg this much)
SOCKET   = 25.0     # how far the plug and sleeve go down over the peg
SLEEVE_BORE = 29.8  # measured 29 mm across the weld seams + 0.4 mm clearance each side
SLEEVE_T = 3.0      # sleeve wall thickness
WALL_BASE = 5.5     # side wall thickness where it meets the floor (the root takes the bending)
WALL_TOP  = 3.5     # side wall thickness at the lips (thinner = easier snap)
ROOT_CH   = 1.0     # 45 deg chamfer in the inside wall/floor corner; stays under the rail's rounded corner
LENGTH   = 34.0     # length along the rail

# ---------------------------------------------------------------- derived
half_in  = (RAIL_W + RAIL_CLR) / 2        # inside face of the side walls
half_out = half_in + WALL_BASE
top      = RAIL_H + 0.3                   # underside of the snap lips
r_plug       = PEG_ID / 2 - FIT
r_sleeve_in  = SLEEVE_BORE / 2
r_sleeve_out = r_sleeve_in + SLEEVE_T


def box(x0, x1, y0, y1, z0, z1):
    return Part.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def cyl(r, z0, z1):
    return Part.makeCylinder(r, z1 - z0, V(0, 0, z0))


def socket(depth):
    """Plug with crush ribs plus a loose outer sleeve, hanging below z = -FLOOR."""
    z0, z1 = -FLOOR - depth, -FLOOR
    plug = cyl(r_plug, z0, z1)
    # 1 mm lead-in chamfer on the plug tip so it finds the tube
    lead = Part.makeCone(r_plug - 1.0, r_plug, 1.0, V(0, 0, z0))
    plug = plug.cut(cyl(r_plug + 1, z0, z0 + 1.0)).fuse(lead)
    # six crush ribs take up tolerance in the tube ID; an internal weld bead
    # just lands between two ribs
    rib_r = PEG_ID / 2 + RIB_BITE
    for k in range(6):
        rib = box(0, rib_r, -0.6, 0.6, z0 + 3.0, z1)
        rib.rotate(V(0, 0, 0), V(0, 0, 1), 30 + 60 * k)
        plug = plug.fuse(rib)
    sleeve = cyl(r_sleeve_out, z0, z1).cut(cyl(r_sleeve_in, z0, z1))
    return plug.fuse(sleeve)


def floor_plate():
    plate = box(-half_out, half_out, -LENGTH / 2, LENGTH / 2, -FLOOR, 0)
    return plate.fuse(cyl(r_sleeve_out, -FLOOR, 0))


def side_wall(sign):
    r"""Tapered wall with the snap lip on top, extruded along the rail.

    Profile (sign = +1 side, rail to the left):

        lip ramp  /|  <- WALL_TOP
      lip ______/  |
             |     |
             |      \   outer face flares out towards the root
             |       \
        root  \_______\  <- WALL_BASE, 1 mm chamfer in the inside corner
    """
    x_in = sign * half_in
    lip_h = LIP + 0.6

    def pt(dx, z):                       # dx measured outward from the wall's inside face
        return V(x_in + sign * dx, -LENGTH / 2, z)

    pts = [pt(-ROOT_CH, 0), pt(WALL_BASE, 0), pt(WALL_TOP, top + lip_h),
           pt(0, top + lip_h),           # top of the 45 deg lead-in ramp
           pt(-LIP, top + 0.6), pt(-LIP, top), pt(0, top),   # lip: flat underside hooks the rail
           pt(0, ROOT_CH), pt(-ROOT_CH, 0)]
    wall = Part.Face(Part.makePolygon(pts)).extrude(V(0, LENGTH, 0))
    if SCREW_D:
        hole = Part.makeCylinder(SCREW_D / 2, WALL_BASE + 2, V(x_in - sign * 1, 0, RAIL_H / 2),
                                 V(sign, 0, 0))
        wall = wall.cut(hole)
    return wall


def build(full=True):
    part = floor_plate().fuse(socket(SOCKET if full else 10.0))
    if full:
        part = part.fuse(side_wall(+1)).fuse(side_wall(-1))
    part = part.removeSplitter()
    # plug tip is the print bed
    part.translate(V(0, 0, FLOOR + (SOCKET if full else 10.0)))
    return part


def export(shape, name):
    mesh = Mesh.Mesh(shape.tessellate(0.05))
    path = os.path.join(OUT, name)
    mesh.write(path)
    bb = shape.BoundBox
    print(f"{name}: {bb.XLength:.1f} x {bb.YLength:.1f} x {bb.ZLength:.1f} mm, "
          f"{shape.Volume / 1000:.1f} cm3, valid={shape.isValid()}, "
          f"solids={len(shape.Solids)}, facets={mesh.CountFacets}")


export(build(True), "peg-adapter.stl")
export(build(False), "peg-adapter-fittest.stl")
