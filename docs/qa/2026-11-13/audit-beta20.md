# Audit Canopy Cavern v0.5.0-beta.20

Kedua pemasangan lokal, Fabulously Optimized dan febricserver, identik dengan JAR build sebelum audit. Audit ini bersifat baca saja terhadap mod dan dunia pemain.

## Temuan

| Prioritas | Temuan | Langkah verifikasi atau perbaikan |
| --- | --- | --- |
| Tinggi | Bordes atas poros membuka kedua lajur, meski hanya satu lajur yang mencapai permukaan. Lajur lain dapat menjadi jalur jatuh. | Pasang pembatas pada sisi lajur yang tidak aktif. Uji turun-naik pada kedua orientasi bordes. |
| Tinggi | Seleksi medan tambang hanya mengambil sampel z=-12, 0, 12. Bagian belakang kompleks 89×33 melewati sampel itu. Pondasi template juga belum mengikuti cekungan. | Periksa seluruh jejak bangunan berdasarkan orientasi bordes. Uji pondasi pada lereng dan cekungan. |
| Sedang | Torchkeeper dan Resonant Survey memakai tag beliung vanilla. Grotto Crystal Pickaxe tidak termasuk dalam tag tersebut. Zirah Thermal dan Mossweave juga belum masuk tag slot zirah vanilla yang dipakai enchantment ekspedisi. | Tambahkan daftar beliung yang didukung dan uji pemasangan melalui anvil. |
| Sedang | Flare Torch memasang blok langsung dan belum mengecek izin pemain terhadap posisi tujuan. | Gunakan aturan penempatan vanilla dan kurangi stok hanya setelah penempatan berhasil. |
| Sedang | Deskripsi enchantment tersedia dalam terjemahan dan panduan, tetapi belum ditampilkan melalui tooltip buku. | Tampilkan cara pakai pada buku enchantment. |

## Cakupan dan bukti

- `./gradlew clean build --no-daemon` exit 0. 49 tes Java dan 52 tes Python lulus.
- Audit 843 template dan 126 pool exit 0. Pemeriksaan statis tidak mendeteksi referensi hilang, koordinat rusak, atau tabrakan yang dicakup pemeriksaan.
- 40 dari 52 definisi vanilla mendapat perubahan dengan kedalaman berbeda. JAR mengganti 249 template dan 79 pool vanilla.
- 12 definisi belum disentuh. Bastion Remnant, Trail Ruins, Trial Chambers, Swamp Hut, Mineshaft, Mineshaft Mesa, Stronghold, Ocean Monument, Desert Pyramid, Nether Fortress, Buried Treasure, Jungle Pyramid.
- Uji server beta.20 sebelumnya berhasil menempatkan kota tambang di dunia datar. Generasi alami lintas seed, perjalanan penuh ke Y=-32, rutinitas villager, efek 10 enchantment saat bermain, FPS, dan performa multiplayer belum terverifikasi. Angka performa dari beta sebelumnya tidak berlaku sebagai bukti performa beta.20.
