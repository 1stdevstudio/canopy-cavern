# Canopy Sanctuary — Server Spawn Hub (Design v1)

**Project:** Canopy Cavern, Minecraft Java 26.3, Fabric server/client
**Baseline:** `main` at `55fe5634ab6f56364c5ba63bb84c377b4e7b9dc0` (v0.5.0-beta.21)
**Status:** Design specification only. No generated structures, placement logic, commands, or server world have been changed.
**Scope:** A multiplayer-safe **server spawn hub**, not a hostile-mob spawner or a new naturally generated village.

## 1. Goals / Non-goals

Goals:
- Provide a memorable, traversable player arrival space themed around Canopy Cavern's mossy forest canopy, ancient stone, glowing grotto crystal and expedition lore.
- Give all new players a simple path from their arrival pad to the guide, trading/service area, surface exploration and cavern expedition route.
- Support Fabric dedicated servers and LAN worlds without requiring Paper/Bukkit, server plugins or a shader.
- Never silently overwrite an existing world's spawn buildings, blocks, protected claims, villagers or player inventories.
- Keep chunk loading, client rendering and server tick cost predictable; remain usable with vanilla textures.

Non-goals for v1:
- No automatically placed hub in all worlds, villages, or all spawn chunks.
- No mandatory teleports, inventory clearing, forced gamemode, privileged item grants, paid-shop mechanics or fake functional portals.
- No assumption that LuckPerms provides block protection. Block protection needs a separate compatible server mechanism or dedicated mod implementation.
- No mob grinder, hostile mob spawner or unsafe combat near the player arrival point.

## 2. Concept, footprint & levels

**Working title:** Canopy Sanctuary
**Target footprint:** ~192 x 192 blocks including landscape transitions, with actual buildings composed from independent modular templates.
**Default center:** The admin-selected world-spawn location; do not assume origin (0,0).
**Suggested vertical organization:**
- `Y0`: Central arrival plaza, relatively flat and open.
- `Y0+4..+28`: Tree canopies, pavilion roofs, ancient stone columns and bridges.
- `Y0-12..-34`: Deliberately excavated subterranean grotto entrance and optional cavern exhibition.
- Terrain elevation is variable; these are *relative* design elevations, not hard world coordinates.

Zones (not to scale):

```
                            NORTH
                 [ Expedition / Adventure Gate ]
                  forest lookout + route signs
                             ||||
 [ Nature Garden ] -- [ CENTRAL ARRIVAL PLAZA ] -- [ Guild / Field Guide ]
                      crystal tree & safe pad
                             ||||
                [ Trading / Rest Pavilion ]
                             ||||
               [ Grotto Descent + Cave Gallery ]
                            SOUTH
```

Suggested proportions:
- Central plaza 49 x 49; safe spawn pad 13 x 13, continuous solid floor and broad 3-block-high unobstructed headroom.
- North adventure gate 31 x 25 (decorative arch + visible trail leading out of hub).
- East guild quarter 35 x 27 (field-guide displays, map boards, noticeboards).
- West garden / shaded market 35 x 27 (covered, wheelchair-equivalent level paths using wide ramps rather than mandatory jumping).
- South pavilion and cavern access 45 x 30 (staircase with guardrails, optional elevator-style access only if implemented and tested).
- Circumferential paths >= 5 blocks clear width; primary paths >= 7 blocks where crowds gather.
- Buildings remain inside the core envelope; trees, landscaping and natural cliffs extend towards the 192-block visual envelope.

## 3. Visual composition

Palette:
- Foundation: stone bricks, mossy stone bricks, polished andesite, deepslate tiles, tuff bricks.
- Timber: dark oak and spruce logs/planks, stripped dark oak, trapdoors for layered roof details.
- Nature: moss blocks/carpet, azalea leaves, flowering azalea, hanging roots, vines, lantern-lit planter beds.
- Cavern highlights: calcite, amethyst clusters, tinted glass in safe non-walkable decorative recesses, glow lichen and subdued copper.
- Lighting: lanterns, sea lanterns or glowstone concealed under floors/leaves, occasional existing Canopy Cavern Glow Lantern for themed display only when compatible.

Keep sightlines wide and the arrival pad clean. Avoid excessive signs, particle effects, command-block fireworks and aggressive gradients. Architecture should look assembled by experienced Minecraft builders, not a giant perfectly symmetrical box. Detail density increases near the plaza and decreases at the perimeter.

Landmarks:
1. **The Heartroot** — one organic 24–32-block-tall giant tree with embedded luminous crystal; canopy split asymmetrically to preserve sky visibility.
2. **The Ring** — circular mossy stone terrace with deliberate worn edges and small bridges.
3. **The Expedition Arch** — ancient stone and dark-oak gateway, no unsupported promise of teleportation.
4. **The Guild Hall** — readable area containing Canopy Field Guide guidance and an expedition route map.
5. **The Cavern Stair** — guarded, lit descent to a crystal observatory; no unavoidable drops, lava or flowing water.

## 4. Player journey

- Arrive facing north on a 13 x 13 protected solid pad; no liquids, foliage, slabs that obstruct spawn detection, damaging blocks, portals or vehicles in the arrival footprint.
- Within ~8 blocks, see a simple welcome message or sign and a two-choice decision: **Explore Surface** / **Explore Cavern**.
- Field Guide introduction is discoverable, but not forced and not automatically granted multiple times.
- Trading pavilion / rest space provides neutral landmarks without automatically allocating villager workstations or spawning NPCs. Any later decorative villagers must be explicitly opt-in with population limits and supported navigation.
- Surface and underground exits connect into natural terrain, never dead-end on an unloaded chunk.
- Emergency escape signage from the cavern and at least two traversable routes back to the plaza.

## 5. Placement strategy (important)

**Default `spawnHubEnabled = false`**. Design for an admin-triggered placement flow only, never automatic worldgen on an existing server.

Recommended implementation sequence:
1. **Preview**: admin selects a center, dimension, orientation and optional terrain blending. Present computed bounding boxes and hazards before any modification.
2. **Preflight**: server-only permission check; Overworld-only by default; within world border; load only necessary chunks at a bounded rate; check build height, surface solidity, water/lava, steep slopes, caves and block entities.
3. **Collision check**: do not replace non-natural/player-built blocks, inventories, villages, existing structures or claimed regions. Since natural-vs-player-placed blocks cannot always be reliably distinguished, fail closed on uncertainty, and require explicit admin-approved placement in a fresh dedicated area.
4. **Backup / transactional approach**: require independent world backup before placing large structures; stage templates, persist placement journal, abort safely on preflight failure. Do not claim rollback exists unless implemented.
5. **Modular build**: split into templates <= 48 blocks on each horizontal axis where practical, bounded per-tick placement, deterministic rotations and manifest-referenced blocks; do not attempt one 192 x 192 x 64 monolithic NBT.
6. **Idempotency**: persist world/dimension/center + schema version so restart or repeated admin command cannot accidentally duplicate the hub.
7. **World spawn**: update the world's spawn point *only after* full successful placement, and only with an explicit administrator choice. Preserve each player's bed/respawn anchor.
8. **Uninstall**: do not delete placed structures automatically if the mod is removed.

If a server already uses a separate lobby/spawn plugin or Fabric mod, support using the build purely as decoration and leave the existing spawn manager authoritative.

## 6. Protection, safety and compatibility

- Distinguish server world-spawn from player respawn anchors and beds; do not forcibly override personal respawn locations.
- Region protection must be explicit: vanilla spawn-protection is limited and not a substitute for complete region claims. Fabric compatibility must be validated; no hard dependency on LuckPerms.
- No hostile spawns, open magma/lava, unguarded 3+ block drops, bubble-column traps or accessible mob spawners in a 48-block radius of arrival. Verify spawn-proofing using actual hostile-spawn conditions in-game rather than treating a fixed light level as sufficient.
- Use safe solid stairs/ramps, non-climbable decoration where needed, guardrails, at least two open evacuation routes, lighted tunnels, anti-suffocation checks and unobstructed entrances.
- Keep villagers, block entities, containers, item frames and redstone clocks near spawn to a minimum. No repeating command blocks, tick-loop structure placement, infinite particle emitters, forced chunk tickets or chunk loaders.
- Respect Fabric dedicated server classloading: no net.minecraft.client references in server-side placement code.
- Test with Canopy Cavern's existing TerraBlender biomes, underground structures, climate effects, and multiplayer server environments. An arrival safe zone must not expose new players to unavoidable cold/heat penalties (a later optional configurable climate-safe zone can be added).
- No interference with vanilla village structure pools, existing worldgen structure sets, underground mining city or the `Village Sentinel` logic.
- Any custom signs, translations and sounds need `en_us` and `id_id` parity.

## 7. Implementation tickets (incremental, isolated)

**SPAWN-01 — Template & asset package**
- Handcraft modular `.nbt` pieces using the in-game Structure Block workflow: center, north arch, guild hall, garden, south pavilion, descent and terrain transitions.
- Store under `src/main/resources/data/canopycavern/structure/server_spawn/`.
- Define a versioned piece manifest with origin offset, rotation options, footprint and connection points.
- Validate NBT palette references, piece bounds, marker blocks, supports and orientation without placing anything in worlds.

**SPAWN-02 — Server-only opt-in placement service**
- New isolated package such as `world/spawn/` to provide preflight, bounded chunk work, placement journal and explicit admin actions.
- New JSON config flags must be backfilled without invalidating existing config; default disabled.
- No automatic install-time placement. Avoid invasive mixins to world spawn routines.

**SPAWN-03 — Welcome/wayfinding**
- Minimal field-guide signs / message; add correct bilingual text.
- Escape routes and neutral signboards should work with no external plugins.
- No inventory edits or permanent forced teleport.

**SPAWN-04 — QA, performance and release**
- Tests for config migration, safe coordinate selection, rejection on block entities/occupied areas, 4 rotations, repeated commands, partial failure, restart, bed respawns and world-border limits.
- Verify safe player arrival for many concurrent players; dedicated Fabric and singleplayer smoke tests; survival and spectator; vanilla textures and shader-free performance.
- Generate and inspect in-game screenshots at day/night, on dry land/near coast/steep terrain, different seeds, and after server restart.
- Release only after both static validation and live world verification. Do not update a published JAR just because docs exist.

## 8. Acceptance criteria

- [ ] Templates load with no missing blocks or invalid palette IDs.
- [ ] Every module connects correctly in all supported rotations.
- [ ] A new player cannot spawn in suffocating blocks, liquid, a portal or a damaging surface.
- [ ] Spawn pad and main paths remain navigable during 20+ simultaneous joins.
- [ ] Hostile mobs cannot naturally spawn inside the protected arrival zone under normal difficulty settings.
- [ ] Preflight refuses occupied/protected/unsafe placement and makes **no** world changes when rejected.
- [ ] No global world-spawn relocation without explicit confirmation and completed placement.
- [ ] Existing player beds/anchors, inventory, towns and chunks remain untouched.
- [ ] Restart and command retry do not create duplicate hubs.
- [ ] Server and client can join without optional external dependencies.
- [ ] No avoidable client FPS drop or server tick spikes from entities, block entities or chunk loading (measure, do not assume).
- [ ] Human in-game visual review and survival playtest completed; no promise of bug-free operation.

---

**Decision record:** The conversational request said "update spawn server" followed by "lanjutkan design spawner". This specification treats that as the **server spawn hub**. It intentionally does **not** add monster spawning logic.
