# Kecepatan SAM dan FI-SAM

Tanggal: 2026-11-18T01:50:12.112054+07:00

Tanpa batas iterasi. GCC gcc (Rev8, Built by MSYS2 project) 15.2.0; -std=c99 -O2 -Wall -Wextra. Windows-11-10.0.26300-SP0. CPU: Intel64 Family 6 Model 170 Stepping 4, GenuineIntel.

Pengukuran memakai QueryPerformanceCounter dalam proses. Satu suite menjalankan seluruh testcase dalam folder. Setiap pemanggilan tetap membaca dan menutup file input; angka optimal terakhir dipisahkan sebelumnya. Startup proses, kompilasi, dan semua printf dikeluarkan. Biaya akhir dikonsumsi oleh volatile sink agar perhitungan tidak dibuang compiler. Cache file hangat.

Tiga sesi independen dengan urutan program dirotasi, masing-masing 3 warmup suite dan 11 sampel; batch adaptif minimal 50 ms. Angka tabel adalah median dari 33 sampel waktu suite. Rata-rata per kasus = median suite / jumlah kasus, bukan median dari waktu masing-masing kasus.

Kedua source telah memakai koreksi indeks SLC yang sama. SAM diuji dengan adapter I/O/EOF dan inisialisasi indeks diagnostik. Tidak ada varian SAM dengan indeks SLC lama dalam pengukuran ini.

| Dataset | Program | Median suite (ms) | Rata-rata per kasus (µs) | IQR suite (ms) | Biaya preflight berbeda |
|---|---|---:|---:|---:|---:|
| testcase69 | SAM | 7.1236 | 103.241 | 0.9892 | 0 |
| testcase69 | FI-SAM | 7.2251 | 104.711 | 1.1800 | 0 |

testcase69: FI-SAM +1.425% waktu dibanding SAM; rasio FI/SAM 1.01425×. Median sesi SAM: [6.8021625, 7.05145, 7.6903125]; FI-SAM: [7.96095, 6.2163, 7.48535].

| Dataset | Program | Median suite (ms) | Rata-rata per kasus (µs) | IQR suite (ms) | Biaya preflight berbeda |
|---|---|---:|---:|---:|---:|
| testcase640 | SAM | 117.1640 | 183.069 | 12.4800 | 0 |
| testcase640 | FI-SAM | 112.5432 | 175.849 | 12.6553 | 0 |

testcase640: FI-SAM -3.944% waktu dibanding SAM; rasio FI/SAM 0.96056×. Median sesi SAM: [121.2648, 113.8383, 117.164]; FI-SAM: [114.628, 114.881, 106.4466].

Durasi bergantung pada mesin, cache, dan beban OS. Selisih kecil dibanding variasi sampel tidak membuktikan metode lebih cepat. Semua pemeriksaan biaya preflight dilaporkan.

Reproduksi: `python benchmark/time_datasets.py`. Sampel mentah: `timing.json`. Ringkasan: `timing.csv`.
