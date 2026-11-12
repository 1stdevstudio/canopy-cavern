# Canopy Cavern (`Minecraft 26.3` · Fabric)

> **🇮🇩 Bahasa Indonesia** | **[🇺🇸 English](#-english)**

---

## 🇮🇩 Bahasa Indonesia

**Canopy Cavern** adalah mod fondasi *client-first* dan **perombakan dunia Permukaan hingga Gua (*Surface-to-Cave World Overhaul*)** untuk **Minecraft Java Edition `26.3`** (*un-obfuscated* Fabric toolchain, **Java 25**).

Dirancang dengan pemisahan arsitektur yang bersih (`main` vs `client`) agar dapat langsung dimainkan dan diuji di *client*/*singleplayer*, sekaligus siap dikembangkan ke mekanik *hardcore survival* berbasis *server* pada fase berikutnya.

### Fitur Utama (`v0.1.0` — Fase 1)

1. **Perombakan Permukaan (*Surface Overhaul*)**
   - **Pembersihan Permukaan Abstrak**: Menghapus *surface lava lakes* dan *lava springs* (`ModificationPhase.REMOVALS`) agar lanskap hutan, dataran, dan tebing tampak lebih alami.
   - **Batu Sungai & Singkapan Tebing**: Menambahkan *boulder* andesit di tepian sungai (`IS_RIVER`) dan singkapan batu *tuff* di pegunungan (`IS_MOUNTAIN`).
   - **Lantai Hutan Organik**: Menambah batang pohon ek (*oak*) dan cemara (*spruce*) tumbang berlumut di bioma hutan dan taiga.

2. **Perombakan Gua & Bawah Tanah (*Cave Overhaul*)**
   - **Carver Gua Lebih Halus & Terhubung**: Menyempurnakan *carver* vanilla `cave` dan `cave_extra_underground` (`weird_thickness_bias: false`, kontur lantai lebih halus, dan konektivitas horizontal lebih baik).
   - **Lumut Gua Dangkal (`y = 8..56`)**: Tambahan lumut lantai dan tanaman merambat langit-langit untuk transisi alami dari permukaan ke mulut gua.
   - **Gugus Batu & Aksen Mineral (`y = -48..48`)**: Menambahkan gugus batu *tuff*, aksen *glow lichen*, serta formasi *dripstone* di kedalaman.

3. **HUD & Atmosfer *Client-First***
   - **HUD Telemetri Dunia** (tekan **`H`** untuk menampilkan/menyembunyikan): Menampilkan zona ketinggian/kedalaman (*High Ridge*, *Surface*, *Shallow Cave*, *Deep Cavern*, *Abyssal Depths*), nama bioma, perkiraan suhu (`°C` / `°F`), serta kondisi sekitar.
   - **Partikel Atmosfer & Bahasa**: Partikel dedaunan/hutan dan debu gua halus, konfigurasi via `config/canopycavern.json`, serta dukungan bahasa `id_id` & `en_us`.

### Instalasi (Siap Pakai)

1. Pastikan profil menggunakan **Minecraft `26.3`**, **Fabric Loader `>=0.20.1`**, **Java `>=25`**, dan **Fabric API** (`26.3`).
2. Unduh [`canopycavern-0.1.0.jar`](https://github.com/1stdevstudio/canopy-cavern/releases/download/v0.1.0/canopycavern-0.1.0.jar) dari halaman [**Releases v0.1.0**](https://github.com/1stdevstudio/canopy-cavern/releases/tag/v0.1.0).
3. Salin file `.jar` ke folder `mods/` pada instance Minecraft Anda, lalu jalankan game.

### Pengembangan Lokal

```bash
# Jalankan unit test (telemetri domain & konfigurasi)
./gradlew test

# Build file JAR mod (hasil di build/libs/)
./gradlew build

# Luncurkan client Minecraft 26.3 untuk pengujian
./gradlew runClient
```

---

## 🇺🇸 English

**Canopy Cavern** is a client-first foundation and **Surface-to-Cave World Overhaul** mod for **Minecraft Java Edition `26.3`** (un-obfuscated Fabric toolchain, **Java 25**).

Built with a clean `main` vs `client` split architecture so you can play and iterate on client/singleplayer features immediately while preparing cleanly for server-side hardcore survival expansion in later phases.

### Features (`v0.1.0` — Phase 1)

1. **Surface World Overhaul**
   - **Abstract Surface Cleanup**: Removes stray surface lava lakes and lava springs (`ModificationPhase.REMOVALS`) so forests, plains, and ridges feel grounded and cohesive.
   - **Riverbank & Mountain Outcrops**: Adds natural `andesite` riverbank boulders (`IS_RIVER`) and `tuff` ridge outcrops (`IS_MOUNTAIN`).
   - **Organic Forest Floors**: Increases natural fallen oak and spruce logs across forest and taiga biomes.

2. **Cave & Subterranean Overhaul**
   - **Smoother, Connected Cave Carvers**: Refines vanilla `cave` and `cave_extra_underground` carvers (`weird_thickness_bias: false`, smoother floor levels, and improved horizontal connectivity).
   - **Subterranean Moss & Ceiling Vines (`y = 8..56`)**: Subtle mossy patches on shallow cave floors and ceilings to connect surface ecosystems organically with cave entrances.
   - **Underground Tuff Boulders & Mineral Accents (`y = -48..48`)**: Adds natural stone clusters, light glow-lichen accents, and occasional deep dripstone formations.

3. **Client-First Ambient HUD & Atmosphere**
   - **World Telemetry HUD** (toggle anytime with **`H`**): Displays current vertical zone (*High Ridge*, *Surface*, *Shallow Cave*, *Deep Cavern*, *Abyssal Depths*), biome name, apparent temperature (`°C` / `°F`), and local condition.
   - **Atmospheric Particles & Localization**: Subtle woodland particles in forests, drifting cavern dust underground, JSON config (`config/canopycavern.json`), and `en_us` / `id_id` translations.

### Installation

1. Use **Minecraft `26.3`**, **Fabric Loader `>=0.20.1`**, **Java `>=25`**, and **Fabric API** for `26.3`.
2. Download [`canopycavern-0.1.0.jar`](https://github.com/1stdevstudio/canopy-cavern/releases/download/v0.1.0/canopycavern-0.1.0.jar) from [**Releases v0.1.0**](https://github.com/1stdevstudio/canopy-cavern/releases/tag/v0.1.0).
3. Drop the `.jar` file into your instance's `mods/` folder and launch the game.

### Requirements & Local Development

- **Minecraft**: `26.3`
- **Java**: **JDK 25** (`>=25`)
- **Fabric Loader**: `>=0.20.1`
- **Fabric API**: `26.3` (built against `0.166.2+26.3`)

```bash
# Run unit tests (domain telemetry & config)
./gradlew test

# Build mod JAR (output in build/libs/)
./gradlew build

# Launch Minecraft 26.3 client for testing
./gradlew runClient
```

---

## Project Architecture / Arsitektur Proyek

- `src/main/java/com/yogi/canopycavern/core/` — Pure Java 25 domain logic (zero Minecraft runtime dependency, covered by JUnit 5)
- `src/main/java/com/yogi/canopycavern/config/` — JSON config (`config/canopycavern.json`)
- `src/main/java/com/yogi/canopycavern/worldgen/` — `BiomeModifications` & feature registration
- `src/main/resources/data/` — Data-driven surface/cave features & refined cave carvers
- `src/client/java/com/yogi/canopycavern/client/` — HUD overlay, keybindings, client sampling, and ambient particles

## License / Lisensi

CC0-1.0 (see [LICENSE](LICENSE)).
