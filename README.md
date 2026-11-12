# Canopy Cavern (Fabric 26.3)

**Canopy Cavern `v0.3.0`** adalah mod eksplorasi **Vanilla-Plus** (dunia, gua, sistem iklim mikro, zirah & perlengkapan ekspedisi, buku panduan & *auto-shelter* kooperatif, serta kota villager berperisai penjaga) untuk **Minecraft 26.3 (Fabric Loader)** tanpa mengubah game menjadi RPG.

---

## Fitur Utama / Key Features (`v0.3.0`)

### 1. Lima Biome Kustom & Perombakan Biome Vanilla / Five Custom Biomes & Vanilla Overhaul
- **Whispering Peaks** (`canopycavern:whispering_peaks`): Dataran tinggi berkabut dengan lereng batu `tuff`, urat `granite`, gugus lumut, dan kantong emerald.
- **Mossy Canopy** (`canopycavern:mossy_canopy`): Hutan kanopi rimbun berlumut dengan `podzol`, kayu tumbang, serta struktur treetop.
- **Verdant Grotto** (`canopycavern:verdant_grotto`): Gua bawah tanah sub-surface kaya lumut, langit-langit `tuff`, cahaya spora `glow_lichen`, dan azalea.
- **Crystal Steppe** (`canopycavern:crystal_steppe`) *[BARU]*: Dataran stepa kristal luas dengan singkapan `calcite`, `smooth_basalt`, geode ametis permukaan, dan kota kristal.
- **Amber Caverns** (`canopycavern:amber_caverns`) *[BARU]*: Biome gua mineral kaya `terracotta`, batu tetes (`dripstone`), urat tembaga & kristal ametis alami.
- **Perombakan Biome Vanilla & Bijih Terstratifikasi**: Batu gurun/badlands (`desert_oasis_boulder`), batu savana (`savanna_acacia_boulder`), rawa gambut (`swamp_peat_patch`), kerikil pantai (`beach_drift_pebble`), kayu tumbang hutan/taiga, aksen Nether (`nether_basalt_accent`) & End (`end_chorus_outcrop`), serta pita bijih terstratifikasi (*copper*, *emerald*, *deep amethyst*).

### 2. Sistem Iklim Mikro, Survival & World HUD
- **HUD Atas-Kiri** (`H` untuk buka/tutup): Menampilkan biome aktif, zona kedalaman, suhu terasa (`°C`/`°F`), kelembapan `% RH`, cuaca mikro (*Clear Air*, *Misty Wind*, *Blizzard Chill*, *Cavern Mist*, *Thermal Steam*), status kenyamanan, dan persentase proteksi zirah.
- **Mekanik Comfort Vanilla-Plus**: Berada di dekat **api unggun menyala** atau **dalam ruangan tertutup beratap** memberikan status *Sheltered* dan memulihkan kedinginan maupun kelelahan tambang tanpa mekanik RPG.

### 3. Perlengkapan Ekspedisi & Zirah Tempa Baru (14 Item)
- **Peak Thermal Set** (`thermal_hood`, `thermal_parka`, `thermal_leggings`, `thermal_boots`): +25% insulasi dingin per bagian; set lengkap 4/4 kebal beku di puncak bersalju.
- **Mossweave Set** (`mossweave_cap`, `mossweave_tunic`, `mossweave_trousers`, `mossweave_boots`): +25% ketahanan lembap/panas per bagian; set lengkap 4/4 kebal pengap/panas plus *Speed I* saat menjelajah gua.
- **Alat Eksplorasi**:
  - **Grotto Crystal Pickaxe** (`canopycavern:grotto_crystal_pickaxe`): +35% kecepatan tambang terhadap `tuff`, `granite`, `deepslate`, dan `cobbled_deepslate`.
  - **Alpine Climbing Pick** (`canopycavern:alpine_climbing_pick`): Dorongan memanjat tebing vertikal ber-cooldown.
  - **Flare Torch** (`canopycavern:flare_torch`): Menembakkan obor menyala ke dinding/langit-langit gua hingga 24 blok.
  - **Glow Lantern** (`canopycavern:glow_lantern`): Mengurangi beban lembap gua dan memicu *Night Vision* singkat.
  - **Grotto Relic Compass** (`canopycavern:grotto_relic_compass`): Kompas magnetik yang berputar mengarah ke `Cavern Shrine`, `Echoing Mineshaft Hub`, atau `Canopy Treetop Bastion` terdekat.
  - **Canopy Field Guide** (`canopycavern:canopy_field_guide`): Diberikan 1x gratis saat pemain bergabung; membuka GUI panduan, pelacak resep inventaris langsung (`✓/✗`), dan pembuat **Auto-Shelter** kooperatif (`Trailside Camp`, `Peak Cabin`, `Grotto Bunker`) — juga bisa dibuka via tombol **`G`**.

### 4. Kota Villager Baru, Security Villager (`Village Sentinel`) & Struktur Berarsitektur
- **Village Sentinel (`canopycavern:village_sentinel`)**: Penjaga keamanan desa bersenjata pedang besi yang berpatroli bersama Iron Golem untuk menyerang monster bermusuhan di sekitar pemukiman.
- **Empat Peradaban Villager**: `crystal_citadel` (Crystal Steppe), `peak_citadel` (Whispering Peaks), `canopy_village` (Mossy Canopy & Hutan), dan kota gua bawah tanah `grotto_outpost_town` (Verdant Grotto & Amber Caverns) lengkap dengan alun-alun air mancur/lonceng, rumah beratap pelana (*gabled*), pandai besi, perpustakaan, pos jaga, Villager, Iron Golem, dan `Village Sentinel`.
- **Struktur Eksplorasi Multi-Ruangan**: `peak_watchtower_ruin` (menara 3 lantai + paviliun), `cavern_shrine` (kuil berkubah + sayap relikuari), `canopy_treetop_bastion` (benteng puncak kanopi berjembatan), dan `echoing_mineshaft_hub` (poros tambang bergema berangkai).
- **Tab Advancement Khusus**: Pohon kemajuan `Canopy Cavern` (`10` advancement dari persiapan ekspedisi hingga penjelajahan kota berjaga & tambang terdalam).

---

## Ketergantungan / Dependencies

- **Minecraft**: `26.3`
- **Fabric Loader**: `>=0.20.1`
- **Java**: `25`
- **Fabric API**: `>=0.166.2+26.3`
- **TerraBlender (Fabric)**: `>=26.3.0.0.9` (`TerraBlender-fabric-26.3-26.3.0.0.9.jar`)

> **Catatan Instalasi**: Letakkan `canopycavern-0.3.0.jar` bersama `TerraBlender-fabric-26.3-26.3.0.0.9.jar` dan Fabric API di folder `mods/` Modrinth / server Fabric `26.3`.

---

## Uji Cepat di Dalam Game / In-Game Testing Commands

```mcfunction
/locate biome canopycavern:crystal_steppe
/locate biome canopycavern:amber_caverns
/locate structure canopycavern:crystal_citadel
/locate structure canopycavern:peak_citadel
/locate structure canopycavern:canopy_village
/locate structure canopycavern:grotto_outpost_town
/locate structure canopycavern:echoing_mineshaft_hub
/locate structure canopycavern:canopy_treetop_bastion
/locate structure canopycavern:peak_watchtower_ruin
/locate structure canopycavern:cavern_shrine
/summon canopycavern:village_sentinel ~ ~ ~
```

---

## Build & Development

```bash
./gradlew clean test build --no-daemon
```

Artefak build tersedia di `build/libs/canopycavern-0.3.0.jar`.
