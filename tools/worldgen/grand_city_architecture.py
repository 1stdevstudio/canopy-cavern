"""Shared non-boxy grand city architecture & branching street network generator for all biome villager cities."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import math
from typing import Callable
from uuid import NAMESPACE_URL, uuid5

from generate_v04_ocean_and_villages import V4StructureBuilder, v3

LOOT_SUPPLY = "canopycavern:chests/village_supply"


@dataclass(frozen=True)
class CityPalette:
    city_id: str
    biomes: tuple[str, ...]
    villager_type: str
    profile: str
    plinth: str
    plinth_alt: str
    wall: str
    wall_alt: str
    log: str
    floor: str
    road: str
    roof_stair: str
    roof_slab: str
    roof_solid: str
    accent_roof: str
    fence: str
    door: str
    pane: str
    stained_pane: str
    bed: str
    flower: str
    awning_a: str
    awning_b: str
    garden_soil: str
    foundation: str
    stilt_height: int = 0
    allow_water: bool = False
    max_water_depth: int = 0
    min_piece_y_above_sea: int = -64
    min_rigid_pieces: int = 4
    core_relief: int = 6
    piece_relief: int = 7
    core_probe_radius: int = 8
    max_foundation_depth: int = 6
    max_piece_embed: int = 3
    start_y: int = 0
    terrain_adaptation: str = "beard_thin"
    use_expansion_hack: bool = False


def _solid_ground_block(sb: V4StructureBuilder, x: int, z: int, deck_y: int, block: str, p: CityPalette, force_pier: bool = False):
    sb.set(x, deck_y, z, block)
    if deck_y > 0 and (force_pier or (x % 4 == 0 and z % 4 == 0)):
        pillar = (p.log, {"axis": "y"})
        for py in range(0, deck_y):
            sb.set(x, py, z, pillar)


def _clear_column_air(sb: V4StructureBuilder, x: int, y0: int, y1: int, z: int):
    for y in range(y0, y1 + 1):
        sb.set(x, y, z, "minecraft:air")


def _place_pillar(sb: V4StructureBuilder, x: int, y0: int, y1: int, z: int, p: CityPalette, deck_y: int):
    _solid_ground_block(sb, x, z, deck_y, p.plinth_alt, p, force_pier=True)
    log_state = (p.log, {"axis": "y"})
    for y in range(y0, y1 + 1):
        sb.set(x, y, z, log_state if y > y0 else p.plinth_alt)


def _stamp_uuids(sb: V4StructureBuilder, key_prefix: str):
    for idx, ent in enumerate(sb.entities):
        uid = uuid5(NAMESPACE_URL, f"canopycavern:{key_prefix}/{idx}").bytes
        ent["nbt"]["UUID"] = v3.nbt_int_array(
            [int.from_bytes(uid[i:i + 4], "big", signed=True) for i in range(0, 16, 4)]
        )


def _stamp_non_boxy_roof(
    sb: V4StructureBuilder,
    mask: set[tuple[int, int]],
    y_eave: int,
    p: CityPalette,
    peak_cap: int = 5,
    include_eave_ring: bool = True,
):
    """Build a watertight non-boxy multi-tier roof automatically following any irregular 2D mask."""
    if not mask:
        return

    xs = [x for x, _ in mask]
    zs = [z for _, z in mask]
    min_x, max_x = min(xs) - 1, max(xs) + 1
    min_z, max_z = min(zs) - 1, max(zs) + 1

    eave_cells: set[tuple[int, int]] = set(mask)
    if include_eave_ring:
        for x, z in mask:
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    nx, nz = x + dx, z + dz
                    if 0 <= nx < sb.sx and 0 <= nz < sb.sz:
                        eave_cells.add((nx, nz))

    # Distance from exterior border of eave_cells via multi-source BFS
    dist: dict[tuple[int, int], int] = {}
    q: deque[tuple[int, int]] = deque()
    for x in range(max(0, min_x - 1), min(sb.sx, max_x + 2)):
        for z in range(max(0, min_z - 1), min(sb.sz, max_z + 2)):
            if (x, z) not in eave_cells:
                dist[(x, z)] = -1
                q.append((x, z))
    for x, z in eave_cells:
        if x in (0, sb.sx - 1) or z in (0, sb.sz - 1):
            if (x, z) not in dist:
                dist[(x, z)] = 0
                q.append((x, z))
    while q:
        cx, cz = q.popleft()
        cd = dist[(cx, cz)]
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = cx + dx, cz + dz
            if (nx, nz) in eave_cells and (nx, nz) not in dist:
                dist[(nx, nz)] = cd + 1
                q.append((nx, nz))

    if p.profile == "adobe":
        # Pueblo stepped terrace deck with parapet corners & jutting viga log ends
        for x, z in mask:
            d = dist.get((x, z), 0)
            sb.set(x, y_eave, z, p.floor)
            is_outer = any((x + dx, z + dz) not in mask for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if is_outer:
                sb.set(x, y_eave + 1, z, p.plinth_alt if (x + z) % 2 == 0 else p.wall_alt)
                if (x + z) % 3 == 0:
                    sb.slab(x, y_eave + 2, z, p.roof_slab, "bottom")
            elif d >= 3:
                # Raised clerestory terrace monitor on wide wings
                sb.set(x, y_eave + 1, z, p.wall)
                sb.set(x, y_eave + 2, z, p.roof_solid)
        # Jutting viga beam ends on outer walls one block below terrace
        for x, z in mask:
            for dx, dz, axis in ((1, 0, "x"), (-1, 0, "x"), (0, 1, "z"), (0, -1, "z")):
                ox, oz = x + dx, z + dz
                if (ox, oz) not in mask and (ox + oz) % 3 == 0 and 0 <= ox < sb.sx and 0 <= oz < sb.sz:
                    sb.set(ox, y_eave, oz, (p.log, {"axis": axis}))
        return

    if p.profile == "mushroom":
        # Rounded organic fungal cap following irregular shape distance
        max_d = max((dist.get(c, 0) for c in eave_cells), default=1)
        for x, z in eave_cells:
            d = min(dist.get((x, z), 0), peak_cap)
            cap_y = y_eave + (0 if d == 0 else min(peak_cap, int(round(peak_cap * math.sqrt(d / max(1, max_d))))))
            block = p.roof_solid
            if d == 0:
                block = p.roof_solid if (x + z) % 2 == 0 else p.accent_roof
            elif d == 1:
                block = p.wall_alt if (x * 3 + z * 5) % 7 == 0 else p.roof_solid
            elif (x * 5 + z * 3) % 11 == 0:
                block = p.accent_roof
            sb.set(x, cap_y, z, block)
            if d >= 1 and (x, z) in mask:
                # Close vertical shoulder cleanly to wall top without clipping interior below y_eave
                sb.set(x, y_eave, z, p.floor)
        return

    # Pitched / Pagoda / Alpine / Crystal / Jungle directional stair-stepped roof
    for x, z in eave_cells:
        d = min(dist.get((x, z), 0), peak_cap)
        y_cur = y_eave + d
        if p.profile == "pagoda" and d == 0:
            # Upturned eave tips at sharp outer pagoda corners
            adj_count = sum(1 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, z + dz) in eave_cells)
            if adj_count <= 2:
                sb.slab(x, y_cur, z, p.roof_slab, "top")
                continue

        lower_dirs = []
        for dname, dx, dz, opp in (
            ("east", -1, 0, "east"),
            ("west", 1, 0, "west"),
            ("south", 0, -1, "south"),
            ("north", 0, 1, "north"),
        ):
            nd = dist.get((x + dx, z + dz), -1)
            if nd < d:
                lower_dirs.append(opp)

        if d >= peak_cap or not lower_dirs:
            sb.set(x, y_cur, z, p.roof_solid)
            if p.profile in ("crystal", "pagoda", "canopy"):
                sb.slab(x, y_cur + 1, z, p.roof_slab, "bottom")
        elif len(lower_dirs) == 1:
            sb.stairs(x, y_cur, z, p.roof_stair, lower_dirs[0])
        else:
            # Corner hip transition
            if d == 0:
                sb.slab(x, y_cur, z, p.roof_slab, "top")
            else:
                sb.stairs(x, y_cur, z, p.roof_stair, lower_dirs[0])

        # Seal diagonal step transitions cleanly above eave base
        if d >= 1 and (x, z) in mask:
            for fill_y in range(y_eave, y_cur):
                if (x, z) in mask and dist.get((x, z), 0) <= 1:
                    sb.set(x, fill_y, z, p.wall)


def _extrude_footprint(
    sb: V4StructureBuilder,
    mask: set[tuple[int, int]],
    y_bot: int,
    y_top: int,
    p: CityPalette,
    deck_y: int,
    window_ys: tuple[int, ...] = (2, 3),
    stained_windows: bool = False,
):
    """Build floor + exterior walls/pillars + interior air strictly over a non-boxy 2D mask."""
    # Precompute boundary, corners, and straight flat walls suitable for framed window panes.
    boundary = {
        (x, z) for (x, z) in mask
        if any((x + dx, z + dz) not in mask for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    }
    corners = {
        (x, z) for (x, z) in boundary
        if sum(1 for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, z + dz) in mask) <= 2
    }
    straight_walls = {
        (x, z) for (x, z) in boundary - corners
        if (
            ((x - 1, z) in boundary and (x + 1, z) in boundary and (x, z - 1) not in boundary and (x, z + 1) not in boundary)
            or ((x, z - 1) in boundary and (x, z + 1) in boundary and (x - 1, z) not in boundary and (x + 1, z) not in boundary)
        )
    }

    for x, z in mask:
        if (x, z) in corners:
            _place_pillar(sb, x, y_bot, y_top, z, p, deck_y)
        elif (x, z) in boundary:
            _solid_ground_block(sb, x, z, deck_y, p.plinth, p, force_pier=((x + z) % 3 == 0))
            for y in range(y_bot, y_top + 1):
                if y == y_bot:
                    sb.set(x, y, z, p.plinth)
                elif y == y_top:
                    sb.set(x, y, z, p.plinth_alt)
                elif (x, z) in straight_walls and (y - deck_y) in window_ys and (x + z) % 3 == 0:
                    sb.set(x, y, z, p.stained_pane if stained_windows else p.pane)
                else:
                    sb.set(x, y, z, p.wall if (y - deck_y) != 4 else p.wall_alt)
        else:
            _solid_ground_block(sb, x, z, deck_y, p.floor, p)
            _clear_column_air(sb, x, y_bot, y_top, z)


def _crown_lantern(sb: V4StructureBuilder, x: int, z: int, p: CityPalette):
    """Place a finial pedestal & lantern directly on top of the highest structural block at (x, z)."""
    highest = max(
        (y for (bx, y, bz), (bid, _) in sb.grid.items()
         if bx == x and bz == z and bid not in ("minecraft:air", "minecraft:structure_void")),
        default=p.stilt_height + 1,
    )
    top_y = min(highest, sb.sy - 3)
    sb.set(x, top_y, z, p.plinth_alt)
    sb.lantern(x, top_y + 1, z, hanging=False)


def _validate_city_piece(sb: V4StructureBuilder, label: str, deck_y: int, require_golem_clear: bool = True):
    # Ensure every entity stands on full floor & inside air without full-cube collisions,
    # and every lantern attaches cleanly to solid support.
    sb.validate(label, require_outdoor_sentinel=False)
    for (lx, ly, lz), (bid, props) in sb.grid.items():
        if bid in ("minecraft:lantern", "minecraft:soul_lantern"):
            is_hanging = dict(props).get("hanging", "false") == "true"
            anchor_pos = (lx, ly + 1, lz) if is_hanging else (lx, ly - 1, lz)
            anchor = sb.grid.get(anchor_pos, ("minecraft:structure_void", ()))[0]
            if anchor in ("minecraft:air", "minecraft:structure_void") or anchor.endswith(("_bed", "_carpet", "_door")):
                raise AssertionError(f"{label}: lantern at {(lx, ly, lz)} unsupported by {anchor}")
    for ent in sb.entities:
        eid = ent["nbt"]["id"]
        px, py, pz = ent["pos"].value
        bx, by, bz = int(math.floor(px)), int(math.floor(py)), int(math.floor(pz))
        under = sb.grid.get((bx, by - 1, bz), ("minecraft:structure_void", ()))[0]
        if not sb._is_full_face_solid(under):
            raise AssertionError(f"{label}: {eid} at {(bx, by, bz)} lacks solid floor (got {under})")
        if require_golem_clear and eid == "minecraft:iron_golem":
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    for dy in (0, 1, 2):
                        cell = sb.grid.get((bx + dx, by + dy, bz + dz), ("minecraft:structure_void", ()))[0]
                        if sb._is_full_face_solid(cell):
                            raise AssertionError(f"{label}: golem at {(bx, by, bz)} collides with {cell} at {(bx+dx, by+dy, bz+dz)}")


def _set_wall_column(sb: V4StructureBuilder, x: int, walk_y: int, z: int, p: CityPalette, middle_block: str | None = None):
    """Build a solid 4-block ground-story wall column (with optional window pane at middle height)."""
    mid = middle_block or p.wall
    sb.set(x, walk_y - 1, z, p.plinth)
    sb.set(x, walk_y, z, p.plinth)
    sb.set(x, walk_y + 1, z, mid)
    sb.set(x, walk_y + 2, z, mid)
    sb.set(x, walk_y + 3, z, p.wall_alt)


def _make_doorway_opening(sb: V4StructureBuilder, x: int, walk_y: int, z: int, p: CityPalette, facing: str, open_arch: bool = False):
    if open_arch:
        for dy in (0, 1, 2):
            sb.set(x, walk_y + dy, z, "minecraft:air")
    else:
        sb.set(x, walk_y - 1, z, p.plinth)
        jambs = ((x - 1, z), (x + 1, z)) if facing in ("north", "south") else ((x, z - 1), (x, z + 1))
        for jx, jz in jambs:
            cur = sb.grid.get((jx, walk_y + 1, jz), ("minecraft:air", ()))[0]
            # Preserve existing corner pillars; replace air gaps or adjacent glass panes with solid door jambs.
            if cur != p.log:
                _set_wall_column(sb, jx, walk_y, jz, p)
        sb.door(x, walk_y, z, p.door, facing)
        sb.set(x, walk_y + 2, z, p.wall_alt)
        sb.set(x, walk_y + 3, z, p.wall_alt)


# ===========================================================================
# 1. GRAND OCTAGONAL CIVIC PLAZA (`town_center`)
# ===========================================================================
def build_grand_octagonal_plaza(p: CityPalette, street_pool: str) -> V4StructureBuilder:
    sy = 24 + p.stilt_height
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(21, sy, 21, fill_block="minecraft:structure_void")

    # Non-boxy chamfered octagon + 4 projecting cardinal causeways
    plaza_mask: set[tuple[int, int]] = set()
    for x in range(21):
        for z in range(21):
            dx, dz = abs(x - 10), abs(z - 10)
            in_oct = max(dx, dz) <= 8 and (dx + dz <= 12)
            in_causeway = dx <= 2 or dz <= 2
            if in_oct or in_causeway:
                plaza_mask.add((x, z))
                is_road = dx <= 1 or dz <= 1
                is_trim = dx + dz == 12 or max(dx, dz) == 8 or dx == 2 or dz == 2
                tile = p.road if is_road else (p.plinth_alt if is_trim or (x + z) % 4 == 0 else p.plinth)
                _solid_ground_block(sb, x, z, deck_y, tile, p, force_pier=(dx in (0, 2, 8) and dz in (0, 2, 8)))
                _clear_column_air(sb, x, walk_y, walk_y + 5, z)

    # Central Octagonal 4-Arch Bell Pavilion (x=7..13, z=7..13)
    pillars = [(7, 8), (8, 7), (12, 7), (13, 8), (13, 12), (12, 13), (8, 13), (7, 12)]
    for px, pz in pillars:
        _place_pillar(sb, px, walk_y, walk_y + 5, pz, p, deck_y)
    # Grand Pavilion Crown & Tiered Spire (y = walk_y+5 .. walk_y+16)
    pav_mask = {
        (x, z) for x in range(7, 14) for z in range(7, 14)
        if abs(x - 10) + abs(z - 10) <= 5
    }
    for x, z in pav_mask:
        sb.set(x, walk_y + 5, z, p.plinth_alt)
    _stamp_non_boxy_roof(sb, pav_mask, walk_y + 6, p, peak_cap=4, include_eave_ring=True)
    # Lantern Beacon Finial at center spire (10, y, 10)
    top_y = min(sy - 3, walk_y + 11)
    sb.fill(9, walk_y + 6, 9, 11, walk_y + 8, 11, p.wall_alt)
    for y in range(walk_y + 9, top_y + 1):
        sb.set(10, y, 10, p.accent_roof)
    _crown_lantern(sb, 10, 10, p)

    # Central ornamental stone pedestal + glowing crystal/bell + water-free safe fountain mosaic
    sb.set(10, deck_y, 10, p.plinth_alt)
    sb.set(10, walk_y, 10, p.plinth_alt)
    sb.set(10, walk_y + 1, 10, p.accent_roof)
    sb.lantern(10, walk_y + 2, 10, hanging=False)
    sb.set(10, walk_y + 4, 10, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    for fx, fz in ((8, 8), (12, 8), (8, 12), (12, 12)):
        sb.set(fx, walk_y, fz, p.fence)
        sb.lantern(fx, walk_y + 1, fz, hanging=False)

    # Four Quadrant Civic Kiosks & Lush Gardens (strictly inside chamfered octagon at dx,dz=4..6)
    # NW Market Stall (4..6, 4..6) + Supply Chest
    for kx, kz in ((4, 4), (6, 4), (4, 6), (6, 6)):
        sb.set(kx, walk_y, kz, p.fence)
        sb.set(kx, walk_y + 1, kz, p.fence)
    for ax in range(4, 7):
        for az in range(4, 7):
            sb.set(ax, walk_y + 2, az, p.awning_a if (ax + az) % 2 == 0 else p.awning_b)
    sb.set(5, walk_y, 5, ("minecraft:barrel", {"facing": "south", "open": "false"}))
    sb.chest(4, walk_y, 5, "west", LOOT_SUPPLY)
    # NE Herbal Garden (14..16, 4..6)
    for gx in range(14, 17):
        for gz in range(14, 17):
            sb.set(gx, deck_y, gz, p.garden_soil)
            if (gx, gz) in ((14, 14), (16, 16)):
                sb.set(gx, walk_y, gz, p.fence)
                sb.lantern(gx, walk_y + 1, gz, hanging=False)
            else:
                sb.set(gx, walk_y, gz, p.flower)
    # SW Herb/Flower Arbor (4..6, 14..16)
    for gx in range(4, 7):
        for gz in range(14, 17):
            sb.set(gx, deck_y, gz, p.garden_soil)
            sb.set(gx, walk_y, gz, p.flower if (gx, gz) != (5, 15) else p.accent_roof)
    # NE Smith/Registry Kiosk (14..16, 4..6)
    sb.set(15, walk_y, 5, ("minecraft:lectern", {"facing": "south", "has_book": "false"}))
    sb.set(16, walk_y, 4, p.fence)
    sb.lantern(16, walk_y + 1, 4, hanging=False)

    # 4 Cardinal Street Sockets
    sb.jigsaw(10, walk_y, 0, "north_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(10, walk_y, 20, "south_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(20, walk_y, 10, "east_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(0, walk_y, 10, "west_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")

    # Civic Population on Wide Open Flagstone Walkways
    sb.add_villager(9, walk_y, 6, p.villager_type, "minecraft:cartographer")
    sb.add_villager(11, walk_y, 14, p.villager_type, "minecraft:librarian")
    sb.add_villager(6, walk_y, 9, p.villager_type, "minecraft:cleric")
    sb.add_villager(14, walk_y, 11, p.villager_type, "minecraft:farmer")
    sb.add_golem(10, walk_y, 3)
    sb.add_golem(10, walk_y, 17)
    sb.add_sentinel(3, walk_y, 10)
    sb.add_sentinel(17, walk_y, 10)

    _stamp_uuids(sb, f"{p.city_id}/town_center")
    _validate_city_piece(sb, f"{p.city_id}/town_center", deck_y)
    return sb


# ===========================================================================
# 2. ORGANIC BRANCHING STREET NETWORK (6 Street Shapes + 2 Terminators)
# ===========================================================================
def _street_curb_lamp(sb: V4StructureBuilder, x: int, deck_y: int, z: int, p: CityPalette):
    _solid_ground_block(sb, x, z, deck_y, p.plinth_alt, p, force_pier=True)
    sb.set(x, deck_y + 1, z, p.fence)
    sb.set(x, deck_y + 2, z, p.fence)
    sb.lantern(x, deck_y + 3, z, hanging=False)


def build_street_boulevard(p: CityPalette, street_pool: str, building_pool: str, dual_sided: bool = True) -> V4StructureBuilder:
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(5, 8 + deck_y, 21, fill_block="minecraft:structure_void")
    for z in range(21):
        _solid_ground_block(sb, 0, z, deck_y, p.plinth, p, force_pier=(z % 5 == 0))
        _solid_ground_block(sb, 4, z, deck_y, p.plinth, p, force_pier=(z % 5 == 0))
        for rx in (1, 2, 3):
            _solid_ground_block(sb, rx, z, deck_y, p.road, p)
            _clear_column_air(sb, rx, walk_y, walk_y + 3, z)
    for lz in (3, 17):
        _street_curb_lamp(sb, 0, deck_y, lz, p)
        _street_curb_lamp(sb, 4, deck_y, lz, p)

    sb.jigsaw(2, walk_y, 0, "north_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(2, walk_y, 20, "south_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(0, walk_y, 10, "west_up", "minecraft:building_entrance", "minecraft:building_entrance", building_pool, "minecraft:air", "aligned")
    if dual_sided:
        sb.jigsaw(4, walk_y, 10, "east_up", "minecraft:building_entrance", "minecraft:building_entrance", building_pool, "minecraft:air", "aligned")
    else:
        # Scenic planter bench on opposite side
        for z in (9, 11):
            sb.set(4, walk_y, z, p.fence)
        sb.set(4, walk_y, 10, p.garden_soil)
        sb.set(4, walk_y + 1, 10, p.flower)
    _stamp_uuids(sb, f"{p.city_id}/street_boulevard_{'dual' if dual_sided else 'single'}")
    _validate_city_piece(sb, f"{p.city_id}/street_boulevard", deck_y)
    return sb


def build_street_curve(p: CityPalette, street_pool: str, turn_right: bool) -> V4StructureBuilder:
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(15, 7 + deck_y, 15, fill_block="minecraft:structure_void")
    pivot_x = 14 if turn_right else 0
    for x in range(15):
        for z in range(15):
            r = math.hypot(x - pivot_x, z)
            in_straight_in = (z == 0 and 5 <= x <= 9)
            in_straight_out = ((x == 14 if turn_right else x == 0) and 5 <= z <= 9)
            if in_straight_in or in_straight_out or 4.8 <= r <= 9.2:
                is_road = (5.7 <= r <= 8.3) or (z == 0 and 6 <= x <= 8) or ((x == 14 if turn_right else x == 0) and 6 <= z <= 8)
                _solid_ground_block(sb, x, z, deck_y, p.road if is_road else p.plinth, p, force_pier=(not is_road and (x + z) % 4 == 0))
                _clear_column_air(sb, x, walk_y, walk_y + 3, z)

    # Inner bend planter monument attached cleanly to inner curve curb
    ix = 11 if turn_right else 3
    _solid_ground_block(sb, ix, 3, deck_y, p.garden_soil, p, force_pier=True)
    sb.set(ix, walk_y, 3, p.flower)
    _street_curb_lamp(sb, 10 if turn_right else 4, deck_y, 4, p)

    sb.jigsaw(7, walk_y, 0, "north_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    exit_x, exit_ori = (14, "east_up") if turn_right else (0, "west_up")
    sb.jigsaw(exit_x, walk_y, 7, exit_ori, "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/street_turn_{'right' if turn_right else 'left'}")
    _validate_city_piece(sb, f"{p.city_id}/street_turn", deck_y)
    return sb


def build_street_junction(p: CityPalette, street_pool: str, building_pool: str, crossroad: bool = False) -> V4StructureBuilder:
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(15, 9 + deck_y, 15, fill_block="minecraft:structure_void")
    for x in range(15):
        for z in range(15):
            dx, dz = abs(x - 7), abs(z - 7)
            in_roundabout = max(dx, dz) <= 5 and (dx + dz <= 7)
            in_arms = (dx <= 2 and (crossroad or z <= 7)) or dz <= 2
            if in_roundabout or in_arms:
                is_road = dx <= 1 or (dz <= 1) or (dx + dz <= 5 and (x + z) % 2 == 0)
                if not crossroad and z > 7 and dx > 2 and (dx + dz > 5):
                    continue
                _solid_ground_block(sb, x, z, deck_y, p.road if is_road else p.plinth, p, force_pier=(dx in (2, 4) and dz in (2, 4)))
                _clear_column_air(sb, x, walk_y, walk_y + 4, z)

    if crossroad:
        # Four decorative corner lantern posts around wide roundabout
        for lx, lz in ((4, 4), (10, 4), (4, 10), (10, 10)):
            _street_curb_lamp(sb, lx, deck_y, lz, p)
        sb.add_villager(6, walk_y, 7, p.villager_type, "minecraft:farmer")
    else:
        for lx, lz in ((4, 4), (10, 4)):
            _street_curb_lamp(sb, lx, deck_y, lz, p)
        sb.set(7, walk_y, 9, p.garden_soil)
        sb.set(7, walk_y + 1, 9, p.flower)

    sb.jigsaw(7, walk_y, 0, "north_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(0, walk_y, 7, "west_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(14, walk_y, 7, "east_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    if crossroad:
        sb.jigsaw(7, walk_y, 14, "south_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    else:
        # Radial T-avenue focal building slot at the south apex!
        sb.jigsaw(7, walk_y, 10, "south_up", "minecraft:building_entrance", "minecraft:building_entrance", building_pool, "minecraft:air", "aligned")

    kind = "street_crossroad_plaza" if crossroad else "street_t_junction"
    _stamp_uuids(sb, f"{p.city_id}/{kind}")
    _validate_city_piece(sb, f"{p.city_id}/{kind}", deck_y)
    return sb


def build_street_diagonal_zig(p: CityPalette, street_pool: str) -> V4StructureBuilder:
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(11, 7 + deck_y, 19, fill_block="minecraft:structure_void")
    for z in range(19):
        t = min(1.0, max(0.0, (z - 3) / 12.0))
        cx = int(round(2 + 6 * t))
        for dx in range(-2, 3):
            x = cx + dx
            if 0 <= x < 11:
                is_curb = abs(dx) == 2
                _solid_ground_block(sb, x, z, deck_y, p.plinth if is_curb else p.road, p, force_pier=(is_curb and z % 5 == 0))
                _clear_column_air(sb, x, walk_y, walk_y + 3, z)
    _street_curb_lamp(sb, 0, deck_y, 3, p)
    _street_curb_lamp(sb, 10, deck_y, 15, p)
    sb.jigsaw(2, walk_y, 0, "north_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    sb.jigsaw(8, walk_y, 18, "south_up", "minecraft:street", "minecraft:street", street_pool, "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/street_diagonal_zig")
    _validate_city_piece(sb, f"{p.city_id}/street_diagonal_zig", deck_y)
    return sb


def build_terminator_gate(p: CityPalette) -> V4StructureBuilder:
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(9, 10 + deck_y, 5, fill_block="minecraft:structure_void")
    for x in range(9):
        for z in range(5):
            if 2 <= x <= 6 or z <= 2:
                _solid_ground_block(sb, x, z, deck_y, p.road if 3 <= x <= 5 else p.plinth, p, force_pier=(x in (1, 7) and z in (1, 3)))
                _clear_column_air(sb, x, walk_y, walk_y + 4, z)
    for px in (1, 7):
        _place_pillar(sb, px, walk_y, walk_y + 4, 2, p, deck_y)
        sb.set(px, walk_y + 1, 1, p.fence)
        sb.lantern(px, walk_y + 2, 1, hanging=False)
    gate_mask = {(x, z) for x in range(1, 8) for z in range(1, 4)}
    for x, z in gate_mask:
        sb.set(x, walk_y + 4, z, p.plinth_alt)
    _stamp_non_boxy_roof(sb, gate_mask, walk_y + 5, p, peak_cap=3)
    sb.lantern(4, walk_y + 3, 2, hanging=True)
    sb.jigsaw(4, walk_y, 0, "north_up", "minecraft:street", "minecraft:street", "minecraft:empty", "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/terminator_gate")
    _validate_city_piece(sb, f"{p.city_id}/terminator_gate", deck_y)
    return sb


def build_side_garden(p: CityPalette, is_terminator: bool = False) -> V4StructureBuilder:
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(11, 11 + deck_y, 11, fill_block="minecraft:structure_void")
    pav_mask: set[tuple[int, int]] = set()
    for x in range(11):
        for z in range(11):
            dx, dz = abs(x - 5), abs(z - 5)
            in_oct = max(dx, dz) <= 4 and (dx + dz <= 6)
            in_entry = z <= 1 and 4 <= x <= 6
            if in_oct or in_entry:
                if in_oct:
                    pav_mask.add((x, z))
                is_border = dx + dz == 6 or max(dx, dz) == 4
                is_soil = dx <= 2 and dz <= 2 and (dx == 2 or dz == 2)
                tile = p.garden_soil if is_soil else (p.plinth_alt if is_border else p.road)
                _solid_ground_block(sb, x, z, deck_y, tile, p, force_pier=(dx == 2 and dz == 2))
                _clear_column_air(sb, x, walk_y, walk_y + 4, z)
                if is_soil and (x, z) not in ((3, 3), (7, 3), (3, 7), (7, 7)):
                    sb.set(x, walk_y, z, p.flower)
    for px, pz in ((3, 3), (7, 3), (3, 7), (7, 7)):
        _place_pillar(sb, px, walk_y, walk_y + 4, pz, p, deck_y)
    arbor_mask = {(x, z) for x in range(3, 8) for z in range(3, 8)}
    _stamp_non_boxy_roof(sb, arbor_mask, walk_y + 4, p, peak_cap=3)
    sb.set(5, walk_y, 5, p.plinth_alt)
    sb.set(5, walk_y + 1, 5, p.accent_roof)
    sb.lantern(5, walk_y + 2, 5, hanging=False)
    sb.add_villager(5, walk_y, 3, p.villager_type, "minecraft:farmer")
    conn_type = "minecraft:street" if is_terminator else "minecraft:building_entrance"
    sb.jigsaw(5, walk_y, 0, "north_up", conn_type, conn_type, "minecraft:empty", "minecraft:air", "aligned")
    label = "terminator_roundabout" if is_terminator else "side_garden"
    _stamp_uuids(sb, f"{p.city_id}/{label}")
    _validate_city_piece(sb, f"{p.city_id}/{label}", deck_y)
    return sb


# ===========================================================================
# 3. FIVE DISTINCT NON-BOXY GRAND ARCHITECTURAL BUILDINGS
# ===========================================================================
def build_villa_l_wing(p: CityPalette) -> V4StructureBuilder:
    """17x17 L-Shaped Two-Story Merchant Villa + Covered Garden Patio (zero square outline!)."""
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(17, 17 + deck_y, 17, fill_block="minecraft:structure_void")

    main_mask = {(x, z) for x in range(1, 11) for z in range(4, 16)}
    side_mask = {(x, z) for x in range(10, 16) for z in range(9, 16)}
    full_mask = main_mask | side_mask
    _extrude_footprint(sb, full_mask, walk_y, walk_y + 4, p, deck_y, window_ys=(2, 3))

    # Entrance stoop + L-notch courtyard patio garden
    for x in range(4, 7):
        for z in range(0, 4):
            _solid_ground_block(sb, x, z, deck_y, p.road, p, force_pier=(z == 0 and x in (4, 6)))
            _clear_column_air(sb, x, walk_y, walk_y + 3, z)
    for x in range(11, 15):
        for z in range(6, 9):
            is_edge = x == 14 or z == 6
            _solid_ground_block(sb, x, z, deck_y, p.garden_soil if (x, z) == (13, 7) else (p.plinth if is_edge else p.road), p, force_pier=is_edge)
            _clear_column_air(sb, x, walk_y, walk_y + 3, z)
    sb.set(13, walk_y, 7, p.flower)
    _place_pillar(sb, 14, walk_y, walk_y + 3, 6, p, deck_y)
    for x in range(11, 15):
        sb.set(x, walk_y + 4, 6, p.fence)
    sb.set(12, walk_y, 7, p.fence)
    sb.lantern(12, walk_y + 1, 7, hanging=False)

    # Open internal archway connecting Main Wing <-> Side Wing cleanly!
    for z in range(10, 14):
        _make_doorway_opening(sb, 10, walk_y, z, p, "east", open_arch=True)
    # Front doorway + Courtyard doorway + porch lamps
    _make_doorway_opening(sb, 5, walk_y, 4, p, "south", open_arch=False)
    _make_doorway_opening(sb, 12, walk_y, 9, p, "south", open_arch=False)
    sb.set(4, walk_y, 3, p.fence); sb.lantern(4, walk_y + 1, 3, hanging=False)
    sb.set(6, walk_y, 3, p.fence); sb.lantern(6, walk_y + 1, 3, hanging=False)

    # Second Story strictly over Main Wing (x=1..10, z=4..15) so roof is multi-level L-profile!
    # Stamp East Side-Wing lower roof first so Main Wing's 2nd story walls cleanly border it.
    side_eave = {(x, z) for (x, z) in side_mask if x >= 11}
    _stamp_non_boxy_roof(sb, side_eave, walk_y + 4, p, peak_cap=3)
    _extrude_footprint(sb, main_mask, walk_y + 5, walk_y + 8, p, deck_y, window_ys=(6, 7))
    # Ceiling & 2nd floor deck over Main Wing
    for x, z in main_mask:
        if 2 <= x <= 9 and 5 <= z <= 14:
            sb.set(x, walk_y + 4, z, p.floor)
    # Stairs from Main floor up to 2nd floor along x=2, z=9..12 (solid under-stringer!)
    sb.set(2, walk_y, 10, p.plinth_alt)
    sb.set(2, walk_y, 11, p.plinth_alt); sb.set(2, walk_y + 1, 11, p.plinth_alt)
    sb.set(2, walk_y, 12, p.plinth_alt); sb.set(2, walk_y + 1, 12, p.plinth_alt); sb.set(2, walk_y + 2, 12, p.plinth_alt)
    sb.stairs(2, walk_y, 9, p.roof_stair, "south")
    sb.stairs(2, walk_y + 1, 10, p.roof_stair, "south")
    sb.stairs(2, walk_y + 2, 11, p.roof_stair, "south")
    sb.stairs(2, walk_y + 3, 12, p.roof_stair, "south")
    for sz in (9, 10, 11, 12):
        sb.set(2, walk_y + 4, sz, "minecraft:air")
    sb.set(3, walk_y + 5, 10, p.fence); sb.set(3, walk_y + 5, 11, p.fence); sb.set(3, walk_y + 5, 12, p.fence)

    # Tall 2-story roof over Main Wing
    _stamp_non_boxy_roof(sb, main_mask, walk_y + 9, p, peak_cap=4)

    # Interior furnishings & beds
    sb.set(8, walk_y, 14, ("minecraft:smoker", {"facing": "north", "lit": "true"}))
    sb.set(7, walk_y, 14, "minecraft:crafting_table")
    sb.set(6, walk_y, 14, ("minecraft:barrel", {"facing": "north", "open": "false"}))
    sb.chest(9, walk_y, 6, "west", LOOT_SUPPLY)
    sb.set(14, walk_y, 14, "minecraft:cartography_table")
    sb.set(14, walk_y, 12, ("minecraft:lectern", {"facing": "west", "has_book": "false"}))
    sb.lantern(6, walk_y + 3, 10, hanging=True)
    # Upstairs bedroom suite & downstairs study bunk
    sb.bed(4, walk_y + 5, 13, p.bed, "south")
    sb.bed(6, walk_y + 5, 13, p.bed, "south")
    sb.bed(8, walk_y + 5, 13, p.bed, "south")
    sb.bed(12, walk_y, 14, p.bed, "south")
    sb.set(8, walk_y + 5, 5, "minecraft:bookshelf")
    for bx in range(2, 10):
        sb.set(bx, walk_y + 9, 9, (p.log, {"axis": "x"}))
    sb.lantern(6, walk_y + 8, 9, hanging=True)

    sb.add_villager(6, walk_y, 9, p.villager_type, "minecraft:cartographer")
    sb.add_villager(12, walk_y, 12, p.villager_type, "minecraft:farmer")
    sb.jigsaw(5, walk_y, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance", "minecraft:empty", "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/villa_l_wing")
    _validate_city_piece(sb, f"{p.city_id}/villa_l_wing", deck_y)
    return sb


def build_rotunda_observatory(p: CityPalette) -> V4StructureBuilder:
    """15x21x15 Chamfered Octagonal Observatory & Grand Sanctuary Library with Domed Spire."""
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(15, 21 + deck_y, 15, fill_block="minecraft:structure_void")

    oct_mask = {
        (x, z) for x in range(1, 14) for z in range(1, 14)
        if max(abs(x - 7), abs(z - 7)) <= 6 and (abs(x - 7) + abs(z - 7) <= 8)
    }
    _extrude_footprint(sb, oct_mask, walk_y, walk_y + 7, p, deck_y, window_ys=(2, 3, 5, 6), stained_windows=True)

    # Projecting entrance stoop at z=0 only (never clear the z=1 facade wall or corner pillars).
    for x in range(5, 10):
        _solid_ground_block(sb, x, 0, deck_y, p.road if 6 <= x <= 8 else p.plinth, p, force_pier=(x in (5, 9)))
        _clear_column_air(sb, x, walk_y, walk_y + 3, 0)
    _make_doorway_opening(sb, 7, walk_y, 1, p, "south", open_arch=False)
    sb.set(5, walk_y, 0, p.fence); sb.lantern(5, walk_y + 1, 0, hanging=False)
    sb.set(9, walk_y, 0, p.fence); sb.lantern(9, walk_y + 1, 0, hanging=False)

    # Mezzanine gallery ring at y = walk_y+4 (open center atrium 6..8, 6..8!)
    for x, z in oct_mask:
        if 2 <= x <= 12 and 2 <= z <= 12 and abs(x - 7) + abs(z - 7) < 7:
            if not (6 <= x <= 8 and 6 <= z <= 8):
                sb.set(x, walk_y + 4, z, p.floor)
    # Wall ladder on interior West facet (x=2, z=7) climbing cleanly to mezzanine (x=3, walk_y+5, z=7)
    for ly in range(walk_y, walk_y + 5):
        sb.set(2, ly, 7, ("minecraft:ladder", {"facing": "east", "waterlogged": "false"}))
    sb.set(2, walk_y + 4, 7, "minecraft:air")
    sb.set(3, walk_y + 4, 7, p.floor)
    sb.set(4, walk_y + 5, 7, "minecraft:air")

    # Stepped Octagonal Domed Cupola Spire (y = walk_y+8 .. +17)
    _stamp_non_boxy_roof(sb, oct_mask, walk_y + 8, p, peak_cap=5)
    cupola = {(x, z) for x in range(5, 10) for z in range(5, 10) if abs(x - 7) + abs(z - 7) <= 3}
    for x, z in cupola:
        sb.set(x, walk_y + 12, z, p.plinth_alt)
        sb.set(x, walk_y + 13, z, p.stained_pane if (x in (5, 9) or z in (5, 9)) else p.roof_solid)
    _stamp_non_boxy_roof(sb, cupola, walk_y + 14, p, peak_cap=2, include_eave_ring=False)
    _crown_lantern(sb, 7, 7, p)

    # Ground Archive + Upstairs Reading Mezzanine
    sb.set(7, walk_y, 7, "minecraft:enchanting_table")
    for bx in (5, 9):
        sb.set(bx, walk_y, 12, "minecraft:bookshelf")
        sb.set(bx, walk_y + 1, 12, "minecraft:bookshelf")
    sb.set(4, walk_y, 9, ("minecraft:lectern", {"facing": "east", "has_book": "false"}))
    sb.chest(10, walk_y, 9, "west", LOOT_SUPPLY)
    sb.bed(5, walk_y + 5, 4, p.bed, "north")
    sb.bed(5, walk_y + 5, 10, p.bed, "south")
    sb.bed(9, walk_y + 5, 10, p.bed, "south")
    sb.lantern(7, walk_y + 3, 4, hanging=True)

    sb.add_villager(6, walk_y, 6, p.villager_type, "minecraft:librarian")
    sb.add_villager(8, walk_y, 8, p.villager_type, "minecraft:cartographer")
    sb.jigsaw(7, walk_y, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance", "minecraft:empty", "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/rotunda_observatory")
    _validate_city_piece(sb, f"{p.city_id}/rotunda_observatory", deck_y)
    return sb


def build_market_t_hall(p: CityPalette) -> V4StructureBuilder:
    """19x16x15 T-Shaped Grand Colonnade Bazaar Arcade & Rear Guildhall."""
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(19, 16 + deck_y, 15, fill_block="minecraft:structure_void")

    front_plaza = {(x, z) for x in range(1, 18) for z in range(2, 7)}
    rear_hall = {(x, z) for x in range(5, 14) for z in range(7, 15)}
    _extrude_footprint(sb, rear_hall, walk_y, walk_y + 5, p, deck_y, window_ys=(2, 3))

    # Open street entrance apron z=0..1 + Open-Air Market Arcade (front cross-bar of the T!)
    for x in range(7, 12):
        for z in (0, 1):
            _solid_ground_block(sb, x, z, deck_y, p.road, p, force_pier=(z == 0 and x in (7, 11)))
            _clear_column_air(sb, x, walk_y, walk_y + 4, z)
    for x, z in front_plaza:
        is_rim = x in (1, 17) or z == 2
        _solid_ground_block(sb, x, z, deck_y, p.plinth if is_rim else p.road, p, force_pier=(x in (1, 5, 13, 17) and z in (2, 6)))
        _clear_column_air(sb, x, walk_y, walk_y + 5, z)

    # Colonnade pillars & striped awnings along Front Arcade
    for px in (1, 5, 7, 11, 13, 17):
        _place_pillar(sb, px, walk_y, walk_y + 4, 2, p, deck_y)
    for x in range(1, 18):
        for z in range(2, 7):
            sb.set(x, walk_y + 4, z, p.awning_a if (x + z) % 2 == 0 else p.awning_b)
    # Raised T-crossbar timber roof gallery spanning x=2..16, z=3..6 above awnings
    cross_roof = {(x, z) for x in range(2, 17) for z in range(3, 7)}
    _stamp_non_boxy_roof(sb, cross_roof | rear_hall, walk_y + 5, p, peak_cap=4)

    # Framed front doorway between Market Arcade <-> Rear Guildhall with symmetric flanked windows
    _make_doorway_opening(sb, 9, walk_y, 7, p, "south", open_arch=False)
    for wx in (7, 11):
        _set_wall_column(sb, wx, walk_y, 7, p, middle_block=p.pane)
    # Market stalls cleanly against inner corners of Front Arcade (3x3 center around (9,4) open for Iron Golem!)
    sb.set(2, walk_y, 5, ("minecraft:barrel", {"facing": "south", "open": "false"}))
    sb.set(3, walk_y, 5, ("minecraft:smoker", {"facing": "south", "lit": "true"}))
    sb.set(16, walk_y, 5, "minecraft:composter")
    sb.set(15, walk_y, 5, "minecraft:cauldron")
    sb.set(4, walk_y, 3, p.fence); sb.lantern(4, walk_y + 1, 3, hanging=False)
    sb.set(14, walk_y, 3, p.fence); sb.lantern(14, walk_y + 1, 3, hanging=False)

    # Rear Apothecary & Guildhall interior
    sb.set(6, walk_y, 13, "minecraft:brewing_stand")
    sb.set(7, walk_y, 13, ("minecraft:barrel", {"facing": "north", "open": "false"}))
    sb.chest(12, walk_y, 9, "west", LOOT_SUPPLY)
    sb.bed(7, walk_y, 11, p.bed, "south")
    sb.bed(11, walk_y, 11, p.bed, "south")
    sb.bed(9, walk_y, 13, p.bed, "south")
    sb.bed(11, walk_y, 13, p.bed, "south")
    for bx in range(6, 13):
        sb.set(bx, walk_y + 5, 10, (p.log, {"axis": "x"}))
    sb.lantern(9, walk_y + 4, 10, hanging=True)

    sb.add_villager(4, walk_y, 4, p.villager_type, "minecraft:butcher")
    sb.add_villager(14, walk_y, 4, p.villager_type, "minecraft:cleric")
    sb.add_villager(9, walk_y, 10, p.villager_type, "minecraft:farmer")
    sb.add_golem(9, walk_y, 4)
    sb.jigsaw(9, walk_y, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance", "minecraft:empty", "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/market_t_hall")
    _validate_city_piece(sb, f"{p.city_id}/market_t_hall", deck_y)
    return sb


def build_foundry_bastion(p: CityPalette) -> V4StructureBuilder:
    """17x20x17 Stepped Courtyard Forge & Tall Chamfered Watchtower Keep."""
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(17, 20 + deck_y, 17, fill_block="minecraft:structure_void")

    forge_hall = {(x, z) for x in range(1, 9) for z in range(6, 14)}
    tower_keep = {
        (x, z) for x in range(8, 16) for z in range(8, 16)
        if not (x in (8, 15) and z in (8, 15))
    }
    # Open stone-curbed forge yard in front (x=2..8, z=1..5) + entrance stoop
    for x in range(2, 9):
        for z in range(0, 6):
            if z == 0 and x not in (4, 5, 6):
                continue
            is_curb = x in (2, 8) and z > 0
            _solid_ground_block(sb, x, z, deck_y, p.plinth if is_curb else p.road, p, force_pier=(z == 0 or (is_curb and z in (2, 5))))
            _clear_column_air(sb, x, walk_y, walk_y + 4, z)

    # Low open-fronted forge workshop + tall 3-tier chamfered Watchtower Keep
    _extrude_footprint(sb, forge_hall | tower_keep, walk_y, walk_y + 4, p, deck_y, window_ys=(2, 3))
    _extrude_footprint(sb, tower_keep, walk_y + 5, walk_y + 11, p, deck_y, window_ys=(6, 7, 10))
    for x, z in tower_keep:
        if 9 <= x <= 14 and 9 <= z <= 14:
            sb.set(x, walk_y + 4, z, p.floor)
            sb.set(x, walk_y + 8, z, p.floor)

    # Open 3-wide interior arch between Forge Hall <-> Tower Keep & framed front forge door
    for z in range(10, 13):
        _make_doorway_opening(sb, 8, walk_y, z, p, "east", open_arch=True)
    _make_doorway_opening(sb, 5, walk_y, 6, p, "south", open_arch=False)

    # Ladder inside Tower Keep along East wall (x=14, z=11) rising to 2nd & 3rd floor
    for ly in range(walk_y, walk_y + 10):
        sb.set(14, ly, 11, ("minecraft:ladder", {"facing": "west", "waterlogged": "false"}))
    sb.set(14, walk_y + 4, 11, "minecraft:air")
    sb.set(14, walk_y + 8, 11, "minecraft:air")
    sb.set(13, walk_y + 4, 11, p.floor)
    sb.set(13, walk_y + 8, 11, p.floor)

    # Roofs: low pitched roof over Forge Hall + towering belfry spire over Watchtower Keep!
    _stamp_non_boxy_roof(sb, forge_hall, walk_y + 5, p, peak_cap=3)
    _stamp_non_boxy_roof(sb, tower_keep, walk_y + 12, p, peak_cap=5)
    # Stone Chimney Stack rising beside forge wall (x=2, z=13) with safe high campfire
    for cy in range(walk_y, walk_y + 9):
        sb.set(2, cy, 13, p.plinth_alt)
    sb.set(2, walk_y + 9, 13, ("minecraft:campfire", {"facing": "north", "lit": "true", "signal_fire": "false", "waterlogged": "false"}))

    # Forge Yard & Tower Furnishings
    sb.set(3, walk_y, 3, ("minecraft:anvil", {"facing": "east"}))
    sb.set(7, walk_y, 3, "minecraft:grindstone")
    sb.set(3, walk_y, 12, ("minecraft:blast_furnace", {"facing": "north", "lit": "true"}))
    sb.set(4, walk_y, 12, ("minecraft:blast_furnace", {"facing": "north", "lit": "true"}))
    sb.set(6, walk_y, 12, "minecraft:smithing_table")
    sb.chest(5, walk_y, 12, "north", LOOT_SUPPLY)
    sb.bed(10, walk_y + 5, 13, p.bed, "south")
    sb.bed(12, walk_y + 5, 13, p.bed, "south")
    sb.bed(10, walk_y + 9, 13, p.bed, "south")
    sb.bed(12, walk_y + 9, 13, p.bed, "south")
    for bx in range(9, 15):
        sb.set(bx, walk_y + 12, 11, (p.log, {"axis": "x"}))
    sb.set(11, walk_y + 11, 11, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    for bx in range(2, 8):
        sb.set(bx, walk_y + 4, 9, (p.log, {"axis": "x"}))
    sb.lantern(5, walk_y + 3, 9, hanging=True)

    sb.add_villager(5, walk_y, 9, p.villager_type, "minecraft:weaponsmith")
    sb.add_villager(11, walk_y, 11, p.villager_type, "minecraft:armorer")
    sb.add_sentinel(4, walk_y, 2)
    sb.jigsaw(5, walk_y, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance", "minecraft:empty", "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/foundry_bastion")
    _validate_city_piece(sb, f"{p.city_id}/foundry_bastion", deck_y)
    return sb


def build_cruciform_guildhall(p: CityPalette) -> V4StructureBuilder:
    """19x22x19 Grand Cruciform (+) Town Guildhall & Crossing Lantern Dome."""
    deck_y = p.stilt_height
    walk_y = deck_y + 1
    sb = V4StructureBuilder(19, 22 + deck_y, 19, fill_block="minecraft:structure_void")

    cross_mask = {
        (x, z) for x in range(1, 18) for z in range(1, 18)
        if (5 <= x <= 13 and 2 <= z <= 16) or (2 <= x <= 16 and 5 <= z <= 13)
    }
    _extrude_footprint(sb, cross_mask, walk_y, walk_y + 5, p, deck_y, window_ys=(2, 3), stained_windows=True)

    # Entrance stoop z=0..1 + wide open portico arch
    for x in range(7, 12):
        for z in (0, 1):
            _solid_ground_block(sb, x, z, deck_y, p.road, p, force_pier=(z == 0 and x in (7, 11)))
            _clear_column_air(sb, x, walk_y, walk_y + 4, z)
    _make_doorway_opening(sb, 9, walk_y, 2, p, "south", open_arch=False)
    for wx in (7, 11):
        _set_wall_column(sb, wx, walk_y, 2, p, middle_block=p.stained_pane)
    sb.set(7, walk_y, 1, p.fence); sb.lantern(7, walk_y + 1, 1, hanging=False)
    sb.set(11, walk_y, 1, p.fence); sb.lantern(11, walk_y + 1, 1, hanging=False)

    # Cross-gabled roof + Towering Central Octagonal Crossing Lantern Spire (6..12, 6..12)
    _stamp_non_boxy_roof(sb, cross_mask, walk_y + 6, p, peak_cap=5)
    lantern_core = {
        (x, z) for x in range(6, 13) for z in range(6, 13)
        if abs(x - 9) + abs(z - 9) <= 4
    }
    for x, z in lantern_core:
        is_rim = abs(x - 9) == 3 or abs(z - 9) == 3 or abs(x - 9) + abs(z - 9) == 4
        sb.set(x, walk_y + 11, z, p.plinth_alt)
        for y in range(walk_y + 12, walk_y + 15):
            sb.set(x, y, z, (p.stained_pane if (x == 9 or z == 9) else p.plinth_alt) if is_rim else "minecraft:air")
    _stamp_non_boxy_roof(sb, lantern_core, walk_y + 15, p, peak_cap=3, include_eave_ring=False)
    _crown_lantern(sb, 9, 9, p)

    # Grand Nave & Wing Alcoves (center 3x3 around (9,9) clear for Iron Golem!)
    for bx in range(6, 13):
        sb.set(bx, walk_y + 6, 9, (p.log, {"axis": "x"}))
        sb.set(bx, walk_y + 5, 6, (p.log, {"axis": "x"}))
        sb.set(bx, walk_y + 5, 12, (p.log, {"axis": "x"}))
    sb.set(9, walk_y + 5, 9, ("minecraft:bell", {"attachment": "ceiling", "facing": "north", "powered": "false"}))
    sb.set(3, walk_y, 9, "minecraft:bookshelf"); sb.set(3, walk_y + 1, 9, "minecraft:bookshelf")
    sb.set(15, walk_y, 9, "minecraft:smithing_table")
    sb.set(15, walk_y, 7, ("minecraft:lectern", {"facing": "west", "has_book": "false"}))
    sb.bed(4, walk_y, 6, p.bed, "north")
    sb.bed(4, walk_y, 12, p.bed, "south")
    sb.bed(7, walk_y, 14, p.bed, "south")
    sb.bed(11, walk_y, 14, p.bed, "south")
    sb.chest(6, walk_y, 13, "east", LOOT_SUPPLY)
    sb.lantern(9, walk_y + 4, 6, hanging=True)
    sb.lantern(9, walk_y + 4, 12, hanging=True)

    sb.add_villager(6, walk_y, 7, p.villager_type, "minecraft:cleric")
    sb.add_villager(12, walk_y, 7, p.villager_type, "minecraft:toolsmith")
    sb.add_villager(9, walk_y, 12, p.villager_type, "minecraft:librarian")
    sb.add_golem(9, walk_y, 9)
    sb.jigsaw(9, walk_y, 0, "north_up", "minecraft:building_entrance", "minecraft:building_entrance", "minecraft:empty", "minecraft:air", "aligned")
    _stamp_uuids(sb, f"{p.city_id}/cruciform_guildhall")
    _validate_city_piece(sb, f"{p.city_id}/cruciform_guildhall", deck_y)
    return sb


# ===========================================================================
# 4. COMPLETE WORLDGEN CITY SUITE EMITTER
# ===========================================================================
def generate_city(
    p: CityPalette,
    write_json: Callable[[str, dict], None],
    *,
    salt: int | None = None,
    spacing: int = 24,
    separation: int = 8,
    write_structure_set: bool = True,
):
    """Build & write all non-boxy city NBT templates, pools, biome tag, and structure JSON."""
    cid = p.city_id
    street_pool = f"canopycavern:{cid}/streets"
    building_pool = f"canopycavern:{cid}/buildings"
    terminator_pool = f"canopycavern:{cid}/terminators"

    build_grand_octagonal_plaza(p, street_pool).save(f"{cid}/town_center.nbt")

    street_specs = [
        ("street_boulevard_dual", build_street_boulevard(p, street_pool, building_pool, dual_sided=True), 4),
        ("street_boulevard_single", build_street_boulevard(p, street_pool, building_pool, dual_sided=False), 3),
        ("street_turn_left", build_street_curve(p, street_pool, turn_right=False), 3),
        ("street_turn_right", build_street_curve(p, street_pool, turn_right=True), 3),
        ("street_t_junction", build_street_junction(p, street_pool, building_pool, crossroad=False), 3),
        ("street_crossroad_plaza", build_street_junction(p, street_pool, building_pool, crossroad=True), 2),
        ("street_diagonal_zig", build_street_diagonal_zig(p, street_pool), 2),
    ]
    for name, builder, _ in street_specs:
        builder.save(f"{cid}/{name}.nbt")

    term_specs = [
        ("terminator_gate", build_terminator_gate(p), 2),
        ("terminator_roundabout", build_side_garden(p, is_terminator=True), 1),
    ]
    for name, builder, _ in term_specs:
        builder.save(f"{cid}/{name}.nbt")

    building_specs = [
        ("villa_l_wing", build_villa_l_wing(p), 4),
        ("rotunda_observatory", build_rotunda_observatory(p), 3),
        ("market_t_hall", build_market_t_hall(p), 3),
        ("foundry_bastion", build_foundry_bastion(p), 3),
        ("cruciform_guildhall", build_cruciform_guildhall(p), 2),
        ("side_garden", build_side_garden(p, is_terminator=False), 2),
    ]
    for name, builder, _ in building_specs:
        builder.save(f"{cid}/{name}.nbt")

    def pool_elem(piece: str, proj: str, w: int) -> dict:
        return {
            "element": {
                "element_type": "minecraft:single_pool_element",
                "location": f"canopycavern:{cid}/{piece}",
                "processors": {"processors": []},
                "projection": proj,
            },
            "weight": w,
        }

    # Stilt boardwalk cities keep rigid level docks; land cities use terrain_matching so streets flow on slopes
    street_proj = "rigid" if p.stilt_height > 0 else "terrain_matching"

    write_json(f"worldgen/template_pool/{cid}/start.json", {
        "elements": [pool_elem("town_center", "rigid", 1)],
        "fallback": "minecraft:empty",
    })
    write_json(f"worldgen/template_pool/{cid}/streets.json", {
        "elements": [pool_elem(name, street_proj, w) for name, _, w in street_specs],
        "fallback": terminator_pool,
    })
    write_json(f"worldgen/template_pool/{cid}/terminators.json", {
        "elements": [pool_elem(name, street_proj, w) for name, _, w in term_specs],
        "fallback": "minecraft:empty",
    })
    write_json(f"worldgen/template_pool/{cid}/buildings.json", {
        "elements": [pool_elem(name, "rigid", w) for name, _, w in building_specs],
        "fallback": "minecraft:empty",
    })

    write_json(f"tags/worldgen/biome/has_structure/{cid}.json", {
        "replace": False,
        "values": list(p.biomes),
    })

    write_json(f"worldgen/structure/{cid}.json", {
        "type": "canopycavern:surface_jigsaw",
        "biomes": f"#canopycavern:has_structure/{cid}",
        "max_distance_from_center": 112,
        "project_start_to_heightmap": "WORLD_SURFACE_WG",
        "size": 7,
        "spawn_overrides": {},
        "start_height": {"absolute": p.start_y},
        "start_pool": f"canopycavern:{cid}/start",
        "step": "surface_structures",
        "terrain_adaptation": p.terrain_adaptation,
        "terrain_guard": {
            "allow_water": p.allow_water,
            "core_probe_radius": p.core_probe_radius,
            "foundation_block": p.foundation,
            "max_core_relief": p.core_relief,
            "max_foundation_depth": p.max_foundation_depth,
            "max_piece_embed": p.max_piece_embed,
            "max_piece_relief": p.piece_relief,
            "max_water_depth": p.max_water_depth,
            "min_piece_y_above_sea": p.min_piece_y_above_sea,
            "min_rigid_pieces": p.min_rigid_pieces,
        },
        "use_expansion_hack": p.use_expansion_hack,
    })

    if write_structure_set and salt is not None:
        write_json(f"worldgen/structure_set/{cid}.json", {
            "placement": {
                "type": "minecraft:random_spread",
                "salt": salt,
                "separation": separation,
                "spacing": spacing,
            },
            "structures": [{"structure": f"canopycavern:{cid}", "weight": 1}],
        })
