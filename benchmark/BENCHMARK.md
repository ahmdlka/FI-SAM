# Benchmark SAM dan FI-SAM

Tanggal: 2026-11-18T01:25:13.361711+07:00

Perbandingan utama memakai **SAM baseline terkoreksi** dan FI-SAM. SAM_raw adalah program asal dengan adaptasi I/O saja dan inisialisasi indeks diagnostik; hasilnya disimpan sebagai pembanding tambahan, bukan bukti dampak fit score.

## Metodologi

- 69 pasangan `.in`/`.out`; seluruh input diperiksa seimbang. Batas iterasi pada kedua source telah dihapus sesuai permintaan; testcase tidak diedit.
- Compiler: gcc (Rev8, Built by MSYS2 project) 15.2.0; flag `-std=c99 -O2 -Wall -Wextra`.
- Lingkungan: Windows-11-10.0.26300-SP0; CPU: Intel64 Family 6 Model 170 Stepping 4, GenuineIntel.
- Adapter SAM: path input melalui argv, pembacaan header berhenti di EOF, penutupan file, dan inisialisasi FLC/SLC agar cetakan diagnostik tidak membaca nilai yang belum diisi. Aturan tie breaker asli dipertahankan.
- Pada baseline SAM terkoreksi, pembanding AS untuk SLC memakai `slc[q]`, sama seperti FI-SAM. `SAM_raw` tetap memakai `q`; indeks ini bisa melewati batas jumlah baris, sehingga hasilnya mengandung risiko undefined behavior.
- Tidak ada batas iterasi maupun timeout eksekusi algoritma. Setiap run berakhir melalui kondisi tidak ada ER; kelayakan alokasi diperiksa terpisah.
- Feasible berarti alokasi nonnegatif, jumlah setiap baris sama dengan supply, setiap kolom sama dengan demand, dan biaya keluaran sama dengan biaya hasil hitung ulang. Biaya tidak feasible tidak dimasukkan ke gap atau peringkat.
- Biaya acuan berasal dari `.out`; benchmark ini tidak membuktikan ulang optimalitas file acuan. Gap (%) = 100 × (biaya hasil − biaya acuan) / biaya acuan; rata-rata gap tidak dibobot menurut skala biaya.
- Transfer adalah jumlah langkah pemindahan aktual; counter iterasi turut disimpan dalam data hasil.
- Waktu tanpa batas iterasi: 7 sampel per testcase, median mikrodetik per pemanggilan; batch adaptif minimal 20 ms, 5 warmup dan satu pemeriksaan hasil awal. SAM dan FI-SAM diukur bergantian urutannya antartestcase. QueryPerformanceCounter dipakai dalam proses; startup proses, kompilasi, dan logging dikeluarkan. Pembacaan file, perhitungan, dan penutupan file tetap diukur. Cache file menjadi hangat; hasil menggambarkan mesin dan sesi pengujian ini.
- Seluruh `printf` dihilangkan hanya pada build timing; biaya akhir tetap dikonsumsi melalui volatile sink dan diperiksa terhadap hasil build fungsional sebelum pengukuran.

## Ringkasan

### Sampai algoritma selesai, tanpa batas iterasi

| Metrik | SAM baseline terkoreksi | FI-SAM |
|---|---:|---:|
| Feasible | 69 | 69 |
| Mencapai batas iterasi | 0 | 0 |
| Sama dengan biaya acuan (hanya feasible) | 48 | 50 |
| Rata-rata gap (%) pada hasil feasible | 2.1154 | 2.0064 |
| Rata-rata transfer pada hasil feasible | 5.4203 | 5.4058 |

Dari 69 testcase yang feasible pada keduanya: FI-SAM lebih murah pada **3**, sama pada **64**, dan lebih mahal pada **2**. Rata-rata perubahan biaya relatif terhadap SAM: penghematan 0.1054%. Rata-rata gap pada himpunan yang sama: SAM 2.1154%, FI-SAM 2.0064%. Total transfer: 374 → 373.

FI-SAM belum feasible: tidak ada.

## Mengapa menang 3 kasus tetapi mencapai acuan bertambah 2?

Menang dibanding SAM dan menyamai acuan adalah dua ukuran berbeda. N05 (430 → 410, acuan 410) dan N32 (1820 → 1780, acuan 1780) menambah dua hasil yang menyamai acuan. S02 (1194 → 1152, acuan 1080) lebih murah daripada SAM tetapi belum menyamai acuan. Pada S05 dan S06, FI-SAM lebih mahal, tetapi kedua metode sama-sama belum menyamai acuan. Jadi kemenangan/kekalahan adalah 3/2 dengan 64 seri; jumlah hasil yang menyamai acuan tetap 48 → 50. Selisih jumlah menang dan kalah sebesar 1 bukan berarti FI-SAM hanya menang pada satu testcase.

## Terminasi

Batas 20 pada source awal merupakan pembatas implementasi. Batas itu sekarang dihapus pada kedua program. Kondisi keluar algoritma adalah tidak ada ER. Suatu algoritma iteratif membutuhkan argumen terminasi untuk dijamin selalu berhenti; pada kode ini transfer dapat membuat ER baru, sehingga jumlah ER tidak selalu turun pada setiap langkah. Ini tidak membuktikan SAM mengalami siklus. Hasil pengujian menunjukkan seluruh 69 testcase berhenti secara alami dengan alokasi valid; pengujian tersebut bukan bukti terminasi untuk semua kemungkinan input.

## Waktu eksekusi (tanpa batas iterasi)

| Metrik | SAM baseline terkoreksi | FI-SAM |
|---|---:|---:|
| Rata-rata median per testcase (µs) | 50.482 | 51.837 |
| Jumlah median untuk satu suite 69 testcase (ms) | 3.483 | 3.577 |

Rata-rata geometrik rasio waktu FI-SAM/SAM: **1.0222×**. Jumlah median suite merupakan agregasi median, bukan satu pengukuran suite utuh. Perbedaan pada durasi mikrodetik sensitif terhadap noise OS dan overhead pembacaan file.

Median IQR relatif antar-sampel: 12.17%; maksimum 68.57%. Selisih rerata waktu kedua metode sangat kecil dibanding variasi pengukuran; angka ini tidak membuktikan salah satu metode lebih cepat.

## Hasil setiap testcase (tanpa batas iterasi)

Δ biaya (%) = 100 × (FI-SAM − SAM) / SAM; negatif berarti FI-SAM lebih murah. Status `OK` hanya jika kedua hasil feasible.

| Testcase | Ukuran | Acuan | SAM | FI-SAM | Δ biaya (%) | Transfer SAM/FI | Waktu SAM/FI (µs) | Status |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 01_N01 | 3×3 | 5600 | 5600 | 5600 | +0.000 | 3/2 | 31.25/33.36 | OK |
| 02_N02 | 3×4 | 28 | 28 | 28 | +0.000 | 1/1 | 39.50/36.53 | OK |
| 03_N03 | 5×5 | 1102 | 1134 | 1134 | +0.000 | 6/6 | 44.40/36.00 | OK |
| 04_N04 | 3×5 | 1580 | 1580 | 1580 | +0.000 | 3/3 | 32.90/33.01 | OK |
| 05_N05 | 4×4 | 410 | 430 | 410 | -4.651 | 4/4 | 33.87/40.91 | OK |
| 06_N06 | 4×4 | 7750 | 7750 | 7750 | +0.000 | 6/6 | 42.14/40.02 | OK |
| 07_N07 | 3×4 | 1160 | 1165 | 1165 | +0.000 | 3/3 | 41.92/43.93 | OK |
| 08_N09 | 4×4 | 111 | 111 | 111 | +0.000 | 2/2 | 31.29/36.35 | OK |
| 09_N10 | 3×4 | 910 | 960 | 960 | +0.000 | 2/2 | 28.85/44.81 | OK |
| 10_N11 | 3×4 | 2460 | 2500 | 2500 | +0.000 | 2/2 | 40.20/40.62 | OK |
| 11_N12 | 3×3 | 425 | 425 | 425 | +0.000 | 2/2 | 39.72/41.19 | OK |
| 12_N13 | 3×3 | 4525 | 4525 | 4525 | +0.000 | 2/2 | 40.33/42.25 | OK |
| 13_N14 | 3×4 | 920 | 920 | 920 | +0.000 | 2/2 | 41.84/28.95 | OK |
| 14_N15 | 3×4 | 156 | 156 | 156 | +0.000 | 2/2 | 28.12/30.09 | OK |
| 15_N16 | 3×4 | 1510 | 1510 | 1510 | +0.000 | 2/2 | 33.81/40.30 | OK |
| 16_N17 | 3×4 | 743 | 743 | 743 | +0.000 | 2/2 | 40.42/44.08 | OK |
| 17_N18 | 3×4 | 1650 | 1695 | 1695 | +0.000 | 3/3 | 49.80/44.24 | OK |
| 18_N21 | 3×3 | 4205 | 4205 | 4205 | +0.000 | 2/2 | 43.26/44.74 | OK |
| 19_N22 | 3×4 | 12075 | 12075 | 12075 | +0.000 | 2/2 | 43.06/43.59 | OK |
| 20_N23 | 3×4 | 23 | 23 | 23 | +0.000 | 1/1 | 39.67/40.39 | OK |
| 21_N24 | 3×4 | 3460 | 3460 | 3460 | +0.000 | 2/2 | 44.46/40.44 | OK |
| 22_N25 | 3×4 | 809 | 809 | 809 | +0.000 | 2/2 | 48.73/40.53 | OK |
| 23_N26 | 4×5 | 490 | 490 | 490 | +0.000 | 4/4 | 47.64/51.32 | OK |
| 24_N27 | 5×5 | 59356 | 59356 | 59356 | +0.000 | 4/4 | 39.23/51.42 | OK |
| 25_N28 | 4×4 | 2090 | 2540 | 2540 | +0.000 | 5/5 | 37.12/41.08 | OK |
| 26_N29 | 3×4 | 3857 | 3857 | 3857 | +0.000 | 3/3 | 38.41/49.45 | OK |
| 27_N30 | 3×3 | 465 | 465 | 465 | +0.000 | 2/2 | 33.82/34.66 | OK |
| 28_N31 | 3×4 | 1480 | 1480 | 1480 | +0.000 | 1/1 | 43.37/32.51 | OK |
| 29_N32 | 4×5 | 1780 | 1820 | 1780 | -2.198 | 2/2 | 40.52/40.91 | OK |
| 30_N33 | 3×3 | 1250 | 1310 | 1310 | +0.000 | 2/2 | 35.97/31.95 | OK |
| 31_N34 | 4×5 | 510 | 510 | 510 | +0.000 | 2/2 | 35.78/40.36 | OK |
| 32_N35 | 3×4 | 280 | 280 | 280 | +0.000 | 2/2 | 32.79/33.22 | OK |
| 33_S1 | 5×5 | 18855 | 18855 | 18855 | +0.000 | 6/6 | 35.95/44.72 | OK |
| 34_S2 | 5×5 | 153500 | 153500 | 153500 | +0.000 | 6/6 | 48.14/43.23 | OK |
| 35_S3 | 11×12 | 1044180 | 1044180 | 1044180 | +0.000 | 7/7 | 67.24/82.72 | OK |
| 36_S4 | 11×12 | 92212 | 94263 | 94263 | +0.000 | 16/16 | 74.60/67.28 | OK |
| 37_S5 | 11×12 | 116020 | 116020 | 116020 | +0.000 | 7/7 | 55.73/67.30 | OK |
| 38_Real1 | 2×94 | 12928429 | 12928429 | 12928429 | +0.000 | 17/17 | 75.66/84.85 | OK |
| 39_Real2 | 2×94 | 13657053 | 13657053 | 13657053 | +0.000 | 19/19 | 81.33/89.99 | OK |
| 40_Real3 | 2×94 | 12296587 | 12296587 | 12296587 | +0.000 | 17/17 | 93.17/89.83 | OK |
| 41_Real4 | 2×94 | 14117586 | 14117586 | 14117586 | +0.000 | 19/19 | 90.07/103.98 | OK |
| 42_Real5 | 2×94 | 14017419 | 14017419 | 14017419 | +0.000 | 19/19 | 85.80/104.33 | OK |
| 43_P01 | 3×4 | 605 | 605 | 605 | +0.000 | 3/4 | 29.00/29.62 | OK |
| 44_P02 | 3×4 | 2850 | 2850 | 2850 | +0.000 | 2/2 | 39.19/40.39 | OK |
| 45_P03 | 3×4 | 149 | 149 | 149 | +0.000 | 3/3 | 43.56/47.95 | OK |
| 46_P04 | 3×4 | 450 | 450 | 450 | +0.000 | 3/3 | 42.65/43.65 | OK |
| 47_P05 | 3×5 | 290 | 290 | 290 | +0.000 | 3/3 | 47.26/40.38 | OK |
| 48_P06 | 4×4 | 49 | 49 | 49 | +0.000 | 4/4 | 39.94/41.96 | OK |
| 49_P07 | 3×3 | 291 | 291 | 291 | +0.000 | 2/2 | 39.01/38.77 | OK |
| 50_P08 | 4×6 | 10625 | 10625 | 10625 | +0.000 | 5/5 | 42.44/47.46 | OK |
| 51_P09 | 3×3 | 845 | 845 | 845 | +0.000 | 1/1 | 39.75/40.54 | OK |
| 52_P10 | 4×6 | 212 | 212 | 212 | +0.000 | 3/3 | 46.12/43.65 | OK |
| 53_P11 | 3×2 | 600 | 600 | 600 | +0.000 | 2/2 | 39.22/38.38 | OK |
| 54_P12 | 3×4 | 180 | 180 | 180 | +0.000 | 3/3 | 43.68/39.65 | OK |
| 55_P13 | 3×4 | 3210 | 3450 | 3450 | +0.000 | 3/3 | 40.69/40.71 | OK |
| 56_P14 | 3×5 | 175 | 175 | 175 | +0.000 | 2/2 | 42.05/42.82 | OK |
| 57_P15 | 3×6 | 10830 | 10830 | 10830 | +0.000 | 2/2 | 41.60/41.53 | OK |
| 58_P16 | 4×3 | 325 | 355 | 355 | +0.000 | 2/2 | 32.23/32.55 | OK |
| 59_P17 | 3×3 | 475 | 475 | 475 | +0.000 | 3/3 | 31.57/31.52 | OK |
| 60_P18 | 3×3 | 555 | 555 | 555 | +0.000 | 2/2 | 31.34/33.56 | OK |
| 61_P19 | 3×3 | 1390 | 1450 | 1450 | +0.000 | 2/2 | 37.64/38.38 | OK |
| 62_P20 | 3×4 | 3320 | 3500 | 3500 | +0.000 | 2/2 | 42.77/42.02 | OK |
| 63_S01 | 10×10 | 5067 | 5420 | 5420 | +0.000 | 11/11 | 66.53/68.75 | OK |
| 64_S02 | 15×15 | 1080 | 1194 | 1152 | -3.518 | 13/11 | 72.40/67.14 | OK |
| 65_S03 | 13×13 | 885 | 1020 | 1020 | +0.000 | 12/12 | 60.93/56.46 | OK |
| 66_S04 | 5×7 | 3125 | 3285 | 3285 | +0.000 | 5/5 | 38.52/39.12 | OK |
| 67_S05 | 22×21 | 1586 | 1799 | 1820 | +1.167 | 25/25 | 160.24/147.21 | OK |
| 68_S06 | 30×32 | 4702 | 5287 | 5389 | +1.929 | 36/37 | 309.37/322.59 | OK |
| 69_S07 | 3×4 | 305 | 326 | 326 | +0.000 | 4/4 | 31.68/28.55 | OK |

## Program SAM asal (SAM_raw)

Biaya SAM_raw tidak mengisolasi pengaruh fit score karena FI-SAM juga memperbaiki indeks SLC. Nilai SAM_raw yang kebetulan stabil tetap tidak menghilangkan undefined behavior pada source.

- Profil unlimited: SAM_raw feasible 69/69; berbeda biaya/status/transfer dari baseline terkoreksi pada 0 kasus: tidak ada.

## Reproduksi dan berkas

Jalankan `python benchmark/benchmark.py` dari folder proyek. Opsi: `--samples 7 --target-ms 20`. Angka waktu akan berubah antar-run.

- `results.json`: metadata, SHA-256 source, semua hasil fungsional, dan sampel waktu mentah.
- `results.csv`: tabel hasil per testcase/varian/profil untuk analisis lanjutan.
- `logs/unlimited/<varian>/*.log`: keluaran lengkap tiap testcase pada pengujian terbaru tanpa batas iterasi. Folder 20/1000 adalah log historis pengujian sebelumnya.
- `.build/`: source adapter, compiler log, dan executable hasil generasi.

FI-SAM adalah heuristik IBFS; skor fit yang lebih kecil tidak menjamin biaya akhir selalu lebih rendah. Perbandingan kualitas yang berlaku adalah hasil feasible pada himpunan testcase yang sama.
