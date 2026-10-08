#!/usr/bin/env python3
"""
Peg-to-rail adapter for the Novilla B-F10014 bed frame centre leg.

The steel centre peg (25 mm round tube) broke off the rail. This adapter
re-seats it: a plug underneath slides down inside the tube, a sleeve (bored out
wide enough to clear the weld seams on the peg) goes around it, the peg rim
butts against the floor, and a U-cradle with two cross bolts closes around the
plain 27 x 27 mm rail.

    rail load -> 3 mm floor -> steel peg rim   (plastic is only in compression)

v3: the v1/v2 snap arms were free-standing posts printed in layers; sideways
force on the bed levered them at the root, across the layer lines, until they
snapped. Here the walls are thick and their tops are tied together by two
bolts over the rail, so the cradle is a closed loop around the rail and
sideways loads are shared by both walls and the bolts.

Coordinates: rail runs along Y, peg axis is Z, floor top (where the rail sits)
is z = 0. The part prints upright, plug end down, no supports.

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

RAIL_W   = 27.0     # width of the rail where the adapter goes
RAIL_H   = 27.0     # height of the rail there
RAIL_CLR = 0.3      # total side clearance around the rail (snug push fit)

FLOOR    = 3.0      # plastic between rail and peg rim (raises the peg this much)
SOCKET   = 40.0     # how far the plug and sleeve go down over the peg (deeper = more
                    # leverage against a sideways kick on the leg)
SLEEVE_BORE = 29.8  # measured 29 mm across the weld seams + 0.4 mm clearance each side
SLEEVE_T = 3.5      # sleeve wall thickness

WALL_BASE = 8.0     # side wall thickness where it meets the floor
WALL_TOP  = 6.0     # side wall thickness at the top
ROOT_CH   = 1.0     # 45 deg chamfer in the inside wall/floor corner; stays under the rail's rounded corner
LENGTH    = 44.0    # length along the rail

BOLT_D    = 6.6     # clearance hole for M6 or 1/4" bolts
BOLT_Y    = 12.0    # bolts sit at y = +/-BOLT_Y along the rail
BOLT_GAP  = 0.2     # gap between the rail top and the bolts (snug them down onto the rail)
BOLT_MEAT = 5.0     # plastic above each bolt hole

# ---------------------------------------------------------------- derived
half_in  = (RAIL_W + RAIL_CLR) / 2        # inside face of the side walls
half_out = half_in + WALL_BASE
bolt_z   = RAIL_H + BOLT_GAP + BOLT_D / 2 # bolt centre height above the floor
wall_h   = bolt_z + BOLT_D / 2 + BOLT_MEAT
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
    """Floor under the rail, plus a 45 deg skirt underneath that carries the
    plate's overhanging corners down onto the sleeve so it prints unsupported."""
    plate = box(-half_out, half_out, -LENGTH / 2, LENGTH / 2, -FLOOR, 0)
    inset = r_sleeve_out / 2 ** 0.5 - 0.2           # square that fits inside the sleeve
    drop = max(half_out - inset, LENGTH / 2 - inset) * 1.4   # keeps every slope steeper than 45 deg
    def rect(hx, hy, z):
        return Part.makePolygon([V(-hx, -hy, z), V(hx, -hy, z), V(hx, hy, z),
                                 V(-hx, hy, z), V(-hx, -hy, z)])
    skirt = Part.makeLoft([rect(half_out, LENGTH / 2, -FLOOR),
                           rect(inset, inset, -FLOOR - drop)], True)
    return plate.fuse(skirt)


def teardrop_x(z, y, r, length):
    """Horizontal hole along X with a 45 deg pointed roof, so it prints without sag."""
    circle = Part.makeCylinder(r, length, V(-length / 2, y, z), V(1, 0, 0))
    tip = r * 2 ** 0.5
    roof = Part.Face(Part.makePolygon([V(-length / 2, y - r / 2 ** 0.5, z + r / 2 ** 0.5),
                                       V(-length / 2, y, z + tip),
                                       V(-length / 2, y + r / 2 ** 0.5, z + r / 2 ** 0.5),
                                       V(-length / 2, y, z),
                                       V(-length / 2, y - r / 2 ** 0.5, z + r / 2 ** 0.5)]))
    return circle.fuse(roof.extrude(V(length, 0, 0)))


def side_wall(sign):
    r"""Thick wall, tapering from WALL_BASE at the floor to WALL_TOP, extruded
    along the rail. Profile (sign = +1 side, rail to the left):

             ______
            |      |   <- WALL_TOP, cross bolts pass through here, above the rail
            |      |
            |       \
            |        \   outer face flares out towards the root
        root \________\  <- WALL_BASE, 1 mm chamfer in the inside corner
    """
    x_in = sign * half_in

    def pt(dx, z):                       # dx measured outward from the wall's inside face
        return V(x_in + sign * dx, -LENGTH / 2, z)

    pts = [pt(-ROOT_CH, 0), pt(WALL_BASE, 0), pt(WALL_TOP, wall_h - 1),
           pt(WALL_TOP - 1, wall_h), pt(0, wall_h),       # 1 mm chamfer on the outer top edge
           pt(0, ROOT_CH), pt(-ROOT_CH, 0)]
    return Part.Face(Part.makePolygon(pts)).extrude(V(0, LENGTH, 0))


def build(full=True):
    depth = SOCKET if full else 10.0
    if full:
        body = floor_plate().fuse(side_wall(+1)).fuse(side_wall(-1))
        for y in (-BOLT_Y, BOLT_Y):
            body = body.cut(teardrop_x(bolt_z, y, BOLT_D / 2, 4 * half_out))
    else:                                # fit test: just a disc of floor over the socket
        body = cyl(r_sleeve_out, -FLOOR, 0)
    # the skirt fills the middle; clear the sleeve bore back out before adding the plug
    body = body.fuse(cyl(r_sleeve_out, -FLOOR - depth, -FLOOR))
    body = body.cut(cyl(r_sleeve_in, -FLOOR - depth - 1, -FLOOR))
    part = body.fuse(socket(depth)).removeSplitter()
    # plug tip is the print bed
    part.translate(V(0, 0, FLOOR + depth))
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
