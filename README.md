# Canopy Cavern (Fabric 26.3)

**Canopy Cavern `v0.4.2`** adalah mod eksplorasi **Vanilla-Plus** (dunia, samudra dalam, monumen bawah tanah megah, sistem iklim mikro, zirah & perlengkapan ekspedisi, buku panduan & *auto-shelter* kooperatif, serta revamp kota desa vanilla & desa berpenjaga) untuk **Minecraft 26.3 (Fabric Loader)** tanpa mengubah game menjadi RPG.

> **Kompatibilitas Server & Client (`"environment": "*"`)**: Mod ini berjalan penuh di **Fabric Dedicated Server**, **LAN World**, maupun **Singleplayer Client**, dan kompatibel berdampingan dengan mod server Fabric populer seperti **LuckPerms** (izin/permissions), **Chunky** (pre-generasi chunk), serta mod autentikasi server Fabric `26.3`.

---

## Fitur Utama / Key Features (`v0.4.2`)

**Perbaikan v0.4.2:** auto-shelter menghitung kebutuhan bahan dari blok final, melindungi blok bernilai dan block entity dari penimpaan, menutup pintu kabin, serta membangun struktur dengan urutan yang lebih aman. Termasuk pengujian regresi blueprint. Perbaikan dunia dan struktur v0.4.1 tetap dipertahankan.

### 1. Tiga Mega-Struktur Samudra & Monumen Bawah Tanah Megah (*Ocean & Subterranean Centers*)
- **Sunken Citadel Vault** (`canopycavern:sunken_citadel_vault`): Kompleks kuil benteng samudra dalam bersayap ganda dari *dark prismarine*, tembaga teroksidasi, serta **Sanctum Vault** kedap air (kering) di dalamnya yang dijaga *Guardian* dan *Elder Guardian* dengan peti harta `chests/sunken_citadel` (struktur terbenam alami di air samudra tanpa memotong kotak udara).
- **Abyssal Thermal Observatory** (`canopycavern:abyssal_thermal_observatory`): Kubah geodesik sferis kaca & tembaga kering di dasar samudra dalam (`#minecraft:is_deep_ocean`), tersambung mulus lewat leher lorong kedap air ke *copper tunnel bridge*, *Airlock Pod*, dan menara bor panas bumi (`chests/thermal_observatory`).
- **Reef Lighthouse Keep & Armada Karam** (`canopycavern:reef_lighthouse_keep`): Pulau karang berbatu alami bermaterial *tuff*/*andesite* dengan rumah penjaga bermotif *calcite* & *dark oak*, mercusuar suar tinggi, brankas penyelundup kering di bawah karang, serta kapal karam bertiang layar tak simetris (`sunken_flagship_wreck`, `chests/armada_treasure`).
- **Abyssal Sanctum Monument** (`canopycavern:abyssal_sanctum_monument`) *[BARU]*: Monumen katedral bawah tanah raksasa (`31x27x31` rotunda + sayap prosesi + ruang harta berlapiskan emas & ametis) yang terbenam di lapisan batu dalam, berhias saluran air reflektif, altar tinggi, lampu kristal gantung raksasa, *Elder Guardian*, *Guardian*, dan *Breeze* (`chests/abyssal_monument`).

### 2. Revamp Menyeluruh 5 Desa Vanilla + Integrasi `Village Sentinel` di Plaza Terbuka
- Seluruh **5 tema desa vanilla** (`plains`, `desert`, `savanna`, `snowy`, `taiga`) dirombak menjadi pemukiman megah (`grand_town_center`, `grand_manor`, `guild_smithy`, `sanctuary_library`, `market_pavilion`, dan `bastion_gatehouse` berlengkung terbuka) melalui *template pool override* resmi sambil mempertahankan varian langka *zombie village*.
- **Penjaga, Tangga & Interior Terpadu (`v0.4.2`)**:
  - **Grand Town Center** menampung **9 `canopycavern:village_sentinel` + 2 `Iron Golem` + 5 `Villager` bertipe bioma** di plaza batu terbuka bagian bawah agar tidak terkurung ruangan.
  - Seluruh kaca jendela (`glass_pane`, `stained_glass_pane`), `iron_bars`, pagar, dan tembok kini tersambung penuh di dalam file `.nbt`, dan rumah 2 lantai memiliki tangga padat menuju lantai atas lengkap dengan perabot, penerangan lentera gantung, dan pagar pengaman.
  - **AI Perilaku `Village Sentinel`**: Bersenjata pedang besi, membantu *Iron Golem* menyerang monster hostile, dapat membuka pintu kayu (`OpenDoorGoal`), dan **membalas serta memperingatkan penjaga lain (`HurtByTargetGoal#setAlertOthers`) bila dipukul**.

### 3. Perlengkapan Samudra, Kompas, Airlock Shelter & Panduan
- **16 Item Kustom** termasuk **Abyssal Tide Compass** (`canopycavern:abyssal_tide_compass` beranimasi 32-frame pengunci mega-struktur laut `#canopycavern:tide_compass_targets`) dan **Sea Glass Charm** (`canopycavern:sea_glass_charm`, *Water Breathing* pasif & aktif *Bubble Pulse*), melengkapi *Peak Thermal Set*, *Mossweave Set*, *Grotto Crystal Pickaxe*, *Alpine Climbing Pick*, *Flare Torch*, *Glow Lantern*, *Grotto Relic Compass* (`#canopycavern:relic_compass_targets`), dan *Canopy Field Guide*.
- **4 Cetak Biru Auto-Shelter** (`G` / Field Guide): `Trailside Camp`, `Peak Stone Cabin`, `Grotto Safe Bunker`, dan **`Abyssal Airlock Dome`** (`canopycavern:abyssal_airlock_dome`) dengan dukungan proteksi iklim di kubah kaca kering bawah air (`PlayerClimateHandler#isEnclosedShelter`).
- **Tab Advancement Khusus**: **`15` advancement** (`Canopy Cavern`) mencakup seluruh lini bioma, perlengkapan, desa berjaga, samudra dalam, hingga monumen bawah tanah.

### 4. Lima Biome Kustom & Empat Peradaban Kota Kustom
- **5 Biome Kustom (`TerraBlender`)**: `whispering_peaks`, `mossy_canopy`, `verdant_grotto`, `crystal_steppe`, dan `amber_caverns` lengkap dengan perombakan bioma vanilla & bijih terstratifikasi.
- **4 Kota/Benteng Kustom & Struktur Eksplorasi**: `crystal_citadel`, `peak_citadel`, `canopy_village`, `grotto_outpost_town`, `peak_watchtower_ruin`, `cavern_shrine`, `canopy_treetop_bastion`, dan `echoing_mineshaft_hub` yang telah diperbaiki tata letak jalan, interior berongga, dan pos penjaga luarnya.

---

## Ketergantungan / Dependencies

- **Minecraft**: `26.3`
- **Fabric Loader**: `>=0.20.1`
- **Java**: `25`
- **Fabric API**: `>=0.166.2+26.3`
- **TerraBlender (Fabric)**: `>=26.3.0.0.9` (`TerraBlender-fabric-26.3-26.3.0.0.9.jar`)

> **Catatan Instalasi (Client Modrinth & Fabric Server)**: Letakkan `canopycavern-0.4.1.jar` bersama `TerraBlender-fabric-26.3-26.3.0.0.9.jar` dan Fabric API di folder `mods/` pada klien Modrinth (seperti *Fabulously Optimized*) maupun Fabric Dedicated Server `26.3`. Kedua sisi (server dan client) wajib memasang mod karena menambahkan bioma, item, dan entitas `village_sentinel`.

---

## Uji Cepat di Dalam Game / In-Game Testing Commands

```mcfunction
/locate structure #canopycavern:tide_compass_targets
/locate structure #canopycavern:relic_compass_targets
/locate structure canopycavern:sunken_citadel_vault
/locate structure canopycavern:abyssal_thermal_observatory
/locate structure canopycavern:reef_lighthouse_keep
/locate structure canopycavern:abyssal_sanctum_monument
/locate structure minecraft:village_plains
/locate structure canopycavern:crystal_citadel
/locate structure canopycavern:canopy_village
/locate structure canopycavern:grotto_outpost_town
/summon canopycavern:village_sentinel ~ ~ ~
```

---

## Build & Development

```bash
./gradlew clean test build --no-daemon
```

Artefak build tersedia di `build/libs/canopycavern-0.4.1.jar`.
