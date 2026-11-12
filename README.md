# Canopy Cavern (`Minecraft 26.3` · Fabric)

Client-first foundation and **Surface-to-Cave World Overhaul** mod for **Minecraft Java Edition `26.3`** (un-obfuscated Fabric toolchain, **Java 25**).

Designed with a clean split architecture (`main` vs `client`) so you can run and iterate on the client/singleplayer experience immediately, while preparing cleanly for server-side hardcore survival mechanics in the next phase.

---

## Features (Phase 1 — World Overhaul & Client Atmosphere)

### 1. Surface World Overhaul
- **Abstract Surface Cleanup**: Removes stray surface lava lakes and lava springs (`ModificationPhase.REMOVALS`) so forests, plains, and ridges remain cohesive and grounded.
- **Riverbank & Mountain Outcrops**: Adds natural `andesite` riverbank boulders (`IS_RIVER`) and `tuff` ridge outcrops (`IS_MOUNTAIN`).
- **Organic Forest Floors**: Increases natural fallen oak and spruce logs with moss/mushroom decorators across forest and taiga biomes.

### 2. Cave & Subterranean Overhaul
- **Smoother, Connected Cave Carvers**: Refines vanilla `cave` and `cave_extra_underground` carvers (`weird_thickness_bias: false`, smoother floor levels, improved horizontal connectivity).
- **Subterranean Moss & Ceiling Vines (`y = 8..56`)**: Subtle mossy patches on shallow cave floors and ceilings to connect surface ecosystems organically with cave entrances.
- **Underground Tuff Boulders & Mineral Accents (`y = -48..48`)**: Adds natural stone clusters, light glow-lichen accents, and occasional deep dripstone formations.

### 3. Client-First Ambient HUD & Atmosphere
- **World Telemetry HUD** (toggle anytime with **`H`**): Displays current vertical zone (*High Ridge*, *Surface*, *Shallow Cave*, *Deep Cavern*, *Abyssal Depths*), biome name, apparent temperature (`°C` / `°F`), and local condition.
- **Atmospheric Particles**: Subtle floating woodland particles in forests and drifting cavern dust underground.

---

## Requirements & Running Locally

- **Minecraft**: `26.3`
- **Java**: **JDK 25**
- **Fabric Loader**: `>=0.20.1`
- **Fabric API**: `0.166.2+26.3`

### Commands
```bash
# Run unit tests (domain telemetry & config)
./gradlew test

# Build mod JAR (build/libs/)
./gradlew build

# Launch Minecraft 26.3 client for testing
./gradlew runClient
```

---

## Project Architecture

- `src/main/java/com/yogi/canopycavern/core/` — Pure Java 25 domain logic (zero Minecraft runtime dependency, covered by JUnit 5)
- `src/main/java/com/yogi/canopycavern/config/` — JSON config (`config/canopycavern.json`)
- `src/main/java/com/yogi/canopycavern/worldgen/` — `BiomeModifications` & feature registration
- `src/main/resources/data/` — Data-driven surface/cave features & refined cave carvers
- `src/client/java/com/yogi/canopycavern/client/` — HUD overlay, keybindings, client sampling, and ambient particles

## License

CC0-1.0 (see [LICENSE](LICENSE)).
