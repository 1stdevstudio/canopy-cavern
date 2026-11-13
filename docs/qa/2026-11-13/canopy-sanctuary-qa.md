# Canopy Sanctuary QA Verification Log (2026-11-13)

- **Branch:** `feat/canopy-sanctuary-20261113`
- **Minecraft / Fabric / Java:** Minecraft `26.3`, Fabric Loader `0.20.1`, Fabric API `0.166.2+26.3`, TerraBlender `26.3.0.0.9`, Java `25` bytecode target
- **Release Target:** `v0.5.0-beta.24` (prerelease, non-destructive over `v0.5.0-beta.21` and `v0.4.2`)

## 1. Automated Unit, Asset & Integrity Verification

Executed `./gradlew clean test build --no-daemon --console=plain`:
- **60 / 60 JUnit 5 tests passed (`0 failed, 0 errors, 0 skipped`)** across 12 test suites:
  - `CanopySanctuarySuiteTest` (`7` tests): all 24 `.nbt` templates (`dataVersion=5023`, <=48 axis bounds, zero hazard palette entries), non-overlapping transform verification across all 4 rotations (`NONE`, `CLOCKWISE_90`, `CLOCKWISE_180`, `COUNTERCLOCKWISE_90`), solid Arrival Pad floor + 4-block headroom in every rotation, `en_us`/`id_id` parity + sign width bounds, zero `net.minecraft.client` imports in server spawn classes & mixins, precondition gates, terrain validator rules, backup ZIP + persistence state transitions, and protection/climate safe zone bounds.
  - `CanopySanctuaryConfigTest` (`4` tests): default opt-out config (`spawnHubEnabled=false`), legacy constructor compatibility, radius clamping (`16..128`), and roundtrip persistence.
  - `StructureExpansionIntegrityTest` (`8` tests), `BiomeAndStructureDataTest` (`6`), `ClimateSimulationTest` (`6`), `EnvironmentTelemetryTest` (`6`), `ExpeditionEnchantmentRulesTest` (`4`), `ClimateUpdatesTest` (`4`), `MiningShaftPlanTest` (`4`), `ShelterBlueprintsTest` (`3`), `V03AssetsAndDataTest` (`5`), `WorldOverhaulDataTest` (`3`).
- `tools/spawn_sanctuary/generate_sanctuary_nbt.py`: `24` modules, envelope `[-95..95, -34..30, -95..95]` (`191x65x191`), `156,359` non-air blocks.

## 2. Isolated Dedicated Server QA (`/Users/yogi/mcfebric`, `127.0.0.1:25566`)

Tested on dedicated Fabric `26.3` server with `fabric-api`, `TerraBlender`, and `LuckPerms-Fabric-5.5.85` (seed `CanopySanctuaryQA2026`):

1. **Default Opt-Out Safety (`spawnHubEnabled=false`)**:
   - Fresh boot wrote `config/canopycavern.json` with `"spawnHubEnabled": false`.
   - `/canopy sanctuary install` aborted cleanly without modifying blocks (`CONFIG_ENABLED`, `WORLD_BACKUP`).
2. **Pre-Install Backup & Preflight Collision Detection**:
   - `/canopy sanctuary backup` flushed chunks and created verified ZIP archives in `world/backups/` (`canopy-sanctuary-20261113-115024.zip`, `215,192` bytes, SHA-256 token `bkp-20261113-115024-215ffbe8b2e5`).
   - Tested `preflight` across `16+` Overworld locations: confirmed rejection of ocean/river sites (`liquids=47..374`), steep ridges (`relief=21..56`), vanilla `igloo`/`shipwreck`/`ruined_portal_ocean`/`village_savanna` overlaps, and mod `canopycavern:reef_lighthouse_keep` overlaps while properly allowing natural `sandstone`, `mossy_cobblestone` (`plains_fieldstone`), flora (`leaf_litter`, `wildflowers`, `bush`), and tree bee nests.
   - Clean site verified at `-336, 116, 1380 (rot=NONE)`: `PASS | relief=15 (Y 111..126, med 115), liquids=0, nonNatural=0, blockEntities=0, structures=0`.
3. **Bounded Multi-Tick Install & Restart Persistence**:
   - `/canopy sanctuary install -336 116 1380 NONE` completed in **`880 ms` across `29` bounded server ticks** (`0` overload warnings during placement).
   - Verified `Status=INSTALLED`, `piecesPlaced=24/24`, `protection=true`.
   - Verified duplicate `/canopy sanctuary install` rejected both while in-progress (`A Canopy Sanctuary installation is already in progress`) and after completion/restart (`IDEMPOTENT_STATE: Sanctuary is already installed in this world`).
   - Verified waxed glowing signs (`is_waxed: 1b, has_glowing_text: 1b`) and lectern `written_book_content` via `/data get block`.
   - Server restarted cleanly (`Done 0.276s`, `Time elapsed: 60 ms`) with zero duplicate placement and persisted `Overworld SavedData`.
4. **Permissions, Explosion Guard, Mob Suppression & Player Respawn**:
   - Verified LuckPerms query on non-OP player `QATester`: `canopycavern.command.sanctuary -> undefined` (denied by `PermissionLevel.ADMINS` fallback).
   - Detonated primed TNT (`summon minecraft:tnt -334 117 1380 {fuse:5}`) on Arrival Pad: Arrival Pad & adjacent blocks remained intact (`FLOOR_IS_SOLID`, `ADJ_IS_SOLID`).
   - Set Overworld to midnight (`18000`) with `doMobSpawning true`: zero undead/hostile spawns within `48` blocks.
   - Verified personal respawn preservation (`spawnpoint QATester -200 117 1380` preserved across `canopy sanctuary set-spawn`).
   - Fixed initial `respawn_radius=10` canopy spawn scattering discovered during `QATester` join by setting `GameRules.RESPAWN_RADIUS = 0` during `setWorldSpawnToSanctuary`; re-verified with fresh player `FreshJoinQA` landing squarely on Arrival Pad at `(-335.5, 117.0, 1380.5)` on both initial login and bedless death respawn.
   - Server performance with player connected: `/tick query` averaged **`22.0 ms/tick` (`20.0 TPS`)**.

## 3. Client-Server Connection & Observed Scope Limits

- Connected real Fabric `26.3` client (`./gradlew runClient`) as `QATester` and `FreshJoinQA` to `127.0.0.1:25566`: OpenGL terrain & shader atlases compiled, `canopycavern:canopy_field_guide` granted on join, zero Mixin/networking disconnects.
- **Unverified / Environment Limits (`v0.5.0-beta.24`)**:
  - `screencapture` from background agent shells on macOS is gated by Screen Recording TCC permission (`could not create image from window`/`display`), so visual screenshots were not captured automatically by the agent; day/night structural & clearance checks were instead performed via live client+server connection and targeted world-block queries.
  - Only the isolated local QA server (`/Users/yogi/mcfebric`) received test deployment; `/Users/yogi/Downloads/febricserver` was left untouched and no production server rollout was executed.

## 4. Compact Hub Update Verification (`v0.5.0-beta.25`)

Following live player feedback in `/Users/yogi/mcfebric` requesting a tighter, less sprawling arrival footprint:
- **Branch & Target:** `feat/compact-canopy-sanctuary-20261113` -> prerelease `v0.5.0-beta.25`.
- **Compacted Geometry (`tools/spawn_sanctuary/generate_sanctuary_nbt.py`):**
  - Consolidated `24` modules (`191x65x191`, `156,359` non-air blocks) into **`10` modules** spanning **`81x59x81`** (`[-40..40, -29..29, -40..40]`, `41,110` non-air blocks) with zero pairwise AABB overlaps and all `19` localized signs + `3` lecterns intact and structurally supported.
  - All 4 cardinal wings (`north_expedition_gate`, `east_guild_hall`, `west_nature_garden`, `south_trading_pavilion`) attach flush to `plaza_core` (`31x31`), while `cavern_descent_upper` and `crystal_grotto_gallery` preserve twin descent stairs plus all 3 daylight return staircases.
- **Automated Test Verification:** `./gradlew clean test build --no-daemon --console=plain` -> **`60 / 60` JUnit 5 tests passed (`0 fail, 0 err, 0 skip`)** across `12` test suites, including `CanopySanctuarySuiteTest` (`7` tests) and `CanopyCavernConfigTest` (`4` tests).
- **Live Dedicated Server (`/Users/yogi/mcfebric`, `*:25565`) Re-Verification:**
  - Restored pre-install world from `world/backups/canopy-sanctuary-20261113-115024.zip`, updated server & Modrinth client (`Fabulously Optimized`) mods to `canopycavern-0.5.0-beta.25.jar`.
  - Executed `canopy sanctuary backup` (`canopy-sanctuary-20261113-130227.zip`), `preflight -336 116 1380 NONE` (`PASS | relief=15`), `preview`, `install -336 116 1380 NONE` (completed in **`312 ms` across `10` bounded ticks**), and `set-spawn` (`-336, 117, 1380`, `yaw=180`).
  - Verified `Status=INSTALLED`, `piecesPlaced=10/10`, `protection=true`, waxed glowing signs (`welcome` at `-340 118 1373`, `grotto_exit` at `-333 94 1397`), resolved lectern books (`-332 117 1387`, `-312 117 1376`), Grotto floor/headroom (`-336 92 1414`), Pavilion Bell (`-339 118 1402`), Daylight Escape Stair endpoints, and `/tick query` (`0.2 ms/tick` avg, `20.0 TPS`).
- **Remaining Unverified Limits:** Same macOS TCC Screen Recording restriction applies to background `screencapture` (no agent-taken PNG screenshots); `/Users/yogi/Downloads/febricserver` (`beta.23`) and earlier GitHub releases remained untouched.
