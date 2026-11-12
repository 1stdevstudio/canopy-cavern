# Canopy Cavern (Fabric 26.3)

**Canopy Cavern** adalah mod perombakan dunia, gua, biome baru, struktur berharta, dan telemetri atmosfer untuk **Minecraft 26.3 (Fabric Loader)** tanpa mengandalkan dimensi tambahan — dirancang agar dunia survival, dataran tinggi, dan gua bawah tanah terasa jauh lebih hidup, rapi, dan memuaskan untuk dijelajahi.

*English summary below / Ringkasan Bahasa Inggris tersedia di bawah.*

---

## Fitur Utama / Key Features (`v0.2.0`)

### 1. Tiga Biome Baru / Three Custom Biomes (via TerraBlender)
- **Whispering Peaks** (`canopycavern:whispering_peaks`): Puncak tinggi berkabut dengan lereng batu `tuff`, urat permukaan `granite`, gugusan `moss_block`, hutan pinus/meadow, dan urat emerald.
- **Mossy Canopy** (`canopycavern:mossy_canopy`): Hutan kanopi lembap dengan kombinasi permukaan `podzol`, `moss_block`, boulder batu, pakis tinggi, dan jamur hutan tua.
- **Verdant Grotto** (`canopycavern:verdant_grotto`): Biome gua bawah tanah sub-surface yang kaya `moss_block`, langit-langit `tuff`, cahaya lembut `glow_lichen`, `cave_vines`, pohon azalea berakar, dan kantong emerald.

### 2. Struktur & Loot Chest Baru / Custom Structures & Loot Tables
- **Peak Watchtower Ruin** (`canopycavern:peak_watchtower_ruin`): Menara pengawas batu tua berlumut yang muncul di `whispering_peaks`, `mossy_canopy`, dan dataran tinggi; menyimpan peti harta **`canopycavern:chests/peak_watchtower`** (iron ingot, emerald, spyglass, compass, perlengkapan iron bershir/enchanted, golden apple).
- **Cavern Shrine** (`canopycavern:cavern_shrine`): Kuil bawah tanah berarsitektur `deepslate_bricks`, `tuff_bricks`, `amethyst_block`, `shroomlight`, dan `soul_lantern` (`y = -36..-8`); menyimpan peti relik **`canopycavern:chests/cavern_shrine`** (diamond, amethyst shard, gold, emerald, buku & diamond pickaxe enchanted, golden apple).

### 3. Kalibrasi Terrain & Gua (Overworld, Nether, The End)
- Penyesuaian *density function* dan *carver* Overworld (`sloped_cheese`, `base_3d_noise`, `final_density`, `caves/entrances`, `noodle`, `spaghetti_roughness_function`) untuk merapikan lereng gunung abstrak, mengurangi dataran melayang, dan mengecilkan mulut gua raksasa yang bolong di permukaan.
- Pengurangan kolam lava permukaan abstrak serta penambahan `plains_fieldstone`, gugus batu gua (`moss_block`, boulder batu), dan `glow_lichen`.
- Kalibrasi *noise* Nether dan The End agar siluet pulau End serta gua Nether lebih rapi dan alami.

### 4. Client HUD & Atmosfer
- **Top-Left World HUD Overlay** (toggle default dengan tombol **`H`**, dapat diubah lewat Key Binds): menampilkan biome aktif, koordinat, elevasi (`Y`), status lingkungan (`Surface` / `Cavern` / `Highlands`), serta suhu biome (`°C`/`°F`).
- Partikel spora/debu atmosfer halus di dalam gua yang dalam dan dataran tinggi berkabut.
- Konfigurasi tersimpan di `config/canopycavern.json`.

---

## Ketergantungan / Dependencies

- **Minecraft**: `26.3`
- **Fabric Loader**: `>=0.20.1`
- **Java**: `25`
- **Fabric API**: `>=0.166.2+26.3`
- **TerraBlender (Fabric)**: `>=26.3.0.0.9` (`TerraBlender-fabric-26.3-26.3.0.0.9.jar`)

> **Catatan Instalasi / Installation Note**: Pastikan file `.jar` **TerraBlender (Fabric 26.3)** terpasang di folder `mods/` bersama `canopycavern-0.2.0.jar`.

---

## Uji Cepat di Dalam Game / In-Game Testing Commands

Buat **World baru** (disarankan mode Kreatif atau Survival baru agar *chunk* langsung menggunakan aturan generasi dunia terbaru), lalu gunakan perintah berikut untuk mengetes langsung:

```mcfunction
/locate biome canopycavern:whispering_peaks
/locate biome canopycavern:mossy_canopy
/locate biome canopycavern:verdant_grotto
/locate structure canopycavern:peak_watchtower_ruin
/locate structure canopycavern:cavern_shrine
```

---

## Build & Development

```bash
./gradlew clean test build --no-daemon
```

Artefak build tersedia di `build/libs/canopycavern-0.2.0.jar`.
