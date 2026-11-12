# Canopy Cavern (`Minecraft 26.3` · Fabric)

> **🇮🇩 Bahasa Indonesia** | **[🇺🇸 English](#-english)**

---

## 🇮🇩 Bahasa Indonesia

**Canopy Cavern** adalah mod fondasi *client-first* dan **perombakan dunia Permukaan, Gua, Nether, hingga End (*Multi-Dimension Terrain & Cave Overhaul*)** untuk **Minecraft Java Edition `26.3`** (*un-obfuscated* Fabric toolchain, **Java 25**).

Dirancang dengan pemisahan arsitektur yang bersih (`main` vs `client`) agar dapat langsung dimainkan dan diuji di *client*/*singleplayer*, sekaligus siap dikembangkan ke mekanik *hardcore survival* berbasis *server* pada fase berikutnya.

### Fitur Utama (`v0.1.1`)

1. **Kalibrasi *Noise* & Perapian Permukaan (*Overworld Terrain & Surface Overhaul*)**
   - **Bebas Pulau Terbang & Gunung Abstrak**: Menyetel ulang `overworld/sloped_cheese` dan `overworld/base_3d_noise` (`y_scale` rendah, penjangkaran *factor* minimum, serta peredaman puncak *jagged*) agar tebing dan pegunungan tetap alami tanpa blok melayang di udara.
   - **Pembersihan Permukaan Abstrak**: Menghapus *surface lava lakes* dan *lava springs* (`ModificationPhase.REMOVALS`) agar lanskap tetap rapi.
   - **Detail Bioma Permukaan**: Menambahkan *fieldstone* berlumut di `Plains`/`Sunflower Plains`/`Meadow`, *boulder* andesit di tepian sungai (`IS_RIVER`), singkapan *tuff* di pegunungan (`IS_MOUNTAIN`), serta batang ek dan cemara tumbang di hutan/taiga.

2. **Perombakan Gua yang Terstruktur (*Cave & Subterranean Overhaul*)**
   - **Kendali *Noise Caves* & *Entrances***: Mengalibrasi `overworld/caves/entrances`, `final_density`, `spaghetti_roughness_function`, `noodle`, serta *carver* (`cave`, `cave_extra_underground`, `canyon`) untuk meniadakan lubang menganga raksasa yang merusak permukaan, meratakan kontur lantai gua, dan mencegah *noodle fissure* membelah puncak gunung.
   - **Gua Berlumut & Aksentuasi Kedalaman**: Memperkuat *moss patch* & tanaman merambat bersinar di gua atas (`y = -8..62`), gugus batu *tuff* (`y = -52..44`), aksen *glow lichen* (`y = -56..44`), serta *dripstone* di kedalaman (`y = -54..12`).

3. **Perapian Dimensi *Nether* & *The End***
   - **Nether Lebih Rapi**: Mengalibrasi `nether/base_3d_noise` dan *carver* `nether_cave` agar gua Netherrack lebih halus, dapat dijelajahi, dan minim serpihan mengapung abstrak.
   - **End Island Kohesif**: Meredam fluktuasi vertikal pada `end/base_3d_noise` dan `end/sloped_cheese` agar pulau-pulau di The End terbentuk rapi tanpa gumpalan melayang acak.

4. **HUD & Atmosfer *Client-First***
   - **HUD Telemetri Dunia** (tekan **`H`** untuk menampilkan/menyembunyikan): Menampilkan zona ketinggian/kedalaman (*Puncak Tinggi*, *Permukaan*, *Goa Dangkal*, *Goa Dalam*, *Jurang Bawah*), nama bioma, perkiraan suhu (`°C` / `°F`), serta kondisi sekitar.
   - **Partikel Atmosfer & Bahasa**: Partikel dedaunan dan debu gua halus, konfigurasi via `config/canopycavern.json`, serta dukungan bahasa `id_id` & `en_us`.

### Instalasi (Siap Pakai)

1. Pastikan profil menggunakan **Minecraft `26.3`**, **Fabric Loader `>=0.20.1`**, **Java `>=25`**, dan **Fabric API** (`26.3`).
2. Unduh [`canopycavern-0.1.1.jar`](https://github.com/1stdevstudio/canopy-cavern/releases/download/v0.1.1/canopycavern-0.1.1.jar) dari halaman [**Releases**](https://github.com/1stdevstudio/canopy-cavern/releases).
3. Salin file `.jar` ke folder `mods/` pada instance Minecraft Anda, lalu jalankan game.

### Pengembangan Lokal

```bash
# Jalankan unit test (telemetri domain, konfigurasi, & validasi worldgen)
./gradlew test

# Build file JAR mod (hasil di build/libs/)
./gradlew build

# Luncurkan client Minecraft 26.3 untuk pengujian
./gradlew runClient
```

---

## 🇺🇸 English

**Canopy Cavern** is a client-first foundation and **Overworld, Cave, Nether & End World Overhaul** mod for **Minecraft Java Edition `26.3`** (un-obfuscated Fabric toolchain, **Java 25**).

Built with a clean `main` vs `client` split architecture so you can play and iterate on client/singleplayer features immediately while preparing cleanly for server-side hardcore survival expansion in later phases.

### Features (`v0.1.1`)

1. **Noise Calibration & Surface Overhaul (Overworld)**
   - **No Floating Terrain or Abstract Spikes**: Calibrates `overworld/sloped_cheese` and `overworld/base_3d_noise` (gentle vertical noise scale, minimum slope factor clamping, and damped jagged peaks) to eliminate detached floating islands and chaotic mountain spikes.
   - **Abstract Surface Cleanup**: Removes stray surface lava lakes and lava springs (`ModificationPhase.REMOVALS`).
   - **Surface Biome Detail**: Adds mossy fieldstones in `Plains`/`Sunflower Plains`/`Meadow`, `andesite` riverbank boulders (`IS_RIVER`), `tuff` mountain outcrops (`IS_MOUNTAIN`), and fallen oak/spruce logs across forests and taigas.

2. **Structured Cave & Subterranean Overhaul**
   - **Tamed Noise Caves & Entrances**: Recalibrates `overworld/caves/entrances`, `final_density`, `spaghetti_roughness_function`, `noodle`, and carvers (`cave`, `cave_extra_underground`, `canyon`) to suppress gaping sinkhole craters, keep ravines underground, smooth cave floors, and cap noodle fissures below mountain peaks.
   - **Cohesive Living Grottos**: Richer moss patches and hanging glow vines (`y = -8..62`), subterranean tuff clusters (`y = -52..44`), subtle glow-lichen navigation accents (`y = -56..44`), and deep dripstone formations (`y = -54..12`).

3. **Nether & The End Smoothing**
   - **Cleaner Nether Cavern Geometry**: Calibrates `nether/base_3d_noise` and `nether_cave` carvers for cleaner terrain ledges and fewer stray floating scraps.
   - **Cohesive End Islands**: Dampens vertical noise in `end/base_3d_noise` and `end/sloped_cheese` to keep End islands sculpted and grounded.

4. **Client-First Ambient HUD & Atmosphere**
   - **World Telemetry HUD** (toggle anytime with **`H`**): Displays current vertical zone (*High Ridge*, *Surface*, *Shallow Cave*, *Deep Cavern*, *Abyssal Depths*), biome name, apparent temperature (`°C` / `°F`), and local condition.
   - **Atmospheric Particles & Localization**: Woodland and cavern dust particles, JSON config (`config/canopycavern.json`), and `en_us` / `id_id` translations.

### Installation

1. Use **Minecraft `26.3`**, **Fabric Loader `>=0.20.1`**, **Java `>=25`**, and **Fabric API** for `26.3`.
2. Download [`canopycavern-0.1.1.jar`](https://github.com/1stdevstudio/canopy-cavern/releases/download/v0.1.1/canopycavern-0.1.1.jar) from [**Releases**](https://github.com/1stdevstudio/canopy-cavern/releases).
3. Drop the `.jar` file into your instance's `mods/` folder and launch the game.

### Requirements & Local Development

- **Minecraft**: `26.3`
- **Java**: **JDK 25** (`>=25`)
- **Fabric Loader**: `>=0.20.1`
- **Fabric API**: `26.3` (built against `0.166.2+26.3`)

```bash
# Run unit tests (domain telemetry, config, & worldgen schema checks)
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
- `src/main/resources/data/` — Data-driven surface/cave features, carvers, and multi-dimension density functions (Overworld, Nether, End)
- `src/client/java/com/yogi/canopycavern/client/` — HUD overlay, keybindings, client sampling, and ambient particles

## License / Lisensi

CC0-1.0 (see [LICENSE](LICENSE)).
