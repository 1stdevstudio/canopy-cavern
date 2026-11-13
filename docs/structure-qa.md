# Structure Overhaul — QA & Release Gates (v0.5.0 candidate)

## Scope of this branch

Existing vanilla village themes: plains, desert, savanna, snowy and taiga (5).
Existing custom civilizations: crystal citadel, peak citadel, canopy village and grotto outpost (4).
New biome-specific settlements: jungle, mangrove/swamp, badlands, cherry/meadow, mushroom fields, frozen ridge (6).
New underground village: Underground Hollow Village (1).
New rare ruin: Abandoned Mega Village (1).
New hostile structure: Frontier Pillager Outpost (1), additive to the vanilla outpost.
Existing ocean megastructures and cavern ruins are retained; their NBT is not claimed to be fully redesigned in this patch.

## CI gates

- `./gradlew clean test build --no-daemon`
- `StructureExpansionIntegrityTest`: all new resource IDs resolve; structure sets have valid spacing; NBT GZIP parses and palette indices are in bounds; every block lies in template bounds; no duplicate positions; living villages contain villagers, beds and guards; abandoned village contains loot and no living villager; custom jigsaw references resolve.
- `BiomeAndStructureDataTest`: existing structures, revamps and custom town structure sets.
- Additional check before stable tag: launch dedicated server from a clean run with Fabric API and TerraBlender. Validate datapack registry loading without errors.

## Manual gameplay gate — required before stable release

1. **Fresh world seeds**: test at least 3 unrelated world seeds and check each new structure through `/locate structure canopycavern:<id>` in creative/spectator and survival. Structure location does not imply actual successful pieces or safe spawn terrain.
2. **Vanilla structures**: locate plains/desert/savanna/taiga/snow villages, ancient city, stronghold, mineshaft, trial chamber, mansion, ocean monument, bastion and fortress. They must remain reachable and generate without illegal terrain clipping or crashes.
3. **Housing and jobs**: villagers walk through doors, reach beds, bell and job site, retain professions, restock, reproduce when conditions allow; sentinels do not trap villagers.
4. **Subterranean**: Grotto Outpost and Underground Hollow Village must not be sealed inside solid terrain or flood with water/lava. Check routes from natural cave entrances, collision with lava pools and deepslate and light levels.
5. **Swamp/mangrove**: test water-level variations, shallow flooded banks, deep water, muddy slopes and chunk borders; doors, beds and profession blocks must remain dry and accessible.
6. **Steep slopes**: test frozen ridge, badlands and highlands on steep terrain. No inaccessible floating houses, broken stairs, suffocation or missing foundations.
7. **Pillager Frontier Outpost**: check ladder path through all levels, pillager spawn aggression, unobstructed loot chest, doors, Iron Golem cage, pillager raid balance, and the original vanilla Pillager Outpost still spawning.
8. **Abandoned village**: no living villagers on generation; verify loot access, zombie-villager spawns, Peaceful difficulty behavior and navigable ruined houses.
9. **Ocean megastructures**: waterlogging, airlock seams, cross-chunk placement, underwater player access, chest availability and guardian behavior.
10. **Persistence and performance**: day/night cycle, relaunch/reload, server with 4 players, pregeneration with Chunky, 20+ minutes exploration, and 2+ hours idle with loaded villages; inspect server log and TPS/heap.
11. **Upgrade safety**: back up a real v0.4.2 world and verify the mod starts. New structures generate only in unexplored chunks; old built structures are not retroactively replaced.

## Release decision

Do NOT label this branch as bug-free solely because tests pass. Merge and tag stable only after completing the in-game checks above or explicitly accept a **beta/pre-release** with known gaps. Unverified: terrain entrance paths for underground structures, mangrove water infiltration, AI pathfinding on generated geometry, vanilla structure cross-mod compatibility.

## Quick commands

```mcfunction
/locate structure canopycavern:frontier_pillager_outpost
/locate structure canopycavern:jungle_canopy_hamlet
/locate structure canopycavern:mangrove_marsh_village
/locate structure canopycavern:badlands_pueblo
/locate structure canopycavern:cherry_grove_hamlet
/locate structure canopycavern:mushroom_island_outpost
/locate structure canopycavern:frozen_ridge_village
/locate structure canopycavern:underground_hollow_village
/locate structure canopycavern:abandoned_mega_village
/locate structure canopycavern:grotto_outpost_town
/locate structure minecraft:village_plains
/locate structure minecraft:ancient_city
/locate structure minecraft:stronghold
```
