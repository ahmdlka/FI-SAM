# Pengujian testcase69 dan testcase640

Tanggal: 2026-11-18T01:49:25.645276+07:00

Acuan optimal adalah angka terakhir pada setiap file `.txt`. Angka itu dipisahkan dari input algoritma. Semua run tanpa batas iterasi dan tanpa timeout eksekusi. Tidak ada optimasi lanjutan. Source program dan dataset tidak diubah oleh skrip ini.

Kedua source sekarang memakai indeks pembanding SLC `slc[q]` yang benar. Adapter SAM hanya menyesuaikan I/O, EOF, dan inisialisasi indeks diagnostik. Label SAM_raw dipertahankan dalam data untuk kompatibilitas skrip; pada versi ini source-nya identik dengan SAM.

Keluaran diagnostik sebelum tabel akhir dinonaktifkan pada salinan uji. Alokasi akhir, biaya, dan counter iterasi tetap diperiksa. Valid berarti alokasi nonnegatif, semua supply dan demand terpenuhi, serta biaya hasil hitung ulang sama dengan biaya yang dicetak. Optimal dihitung hanya dari hasil valid yang tepat sama dengan acuan; denominator persentase adalah seluruh testcase dalam folder.

| Dataset | Metode | Valid | Mencapai optimal | Belum optimal | Persentase optimal | Iterasi maksimum |
|---|---|---:|---:|---:|---:|---:|
| testcase69 | SAM_raw | 69/69 | 47 | 22 | 68.1159% | 36 |
| testcase69 | SAM | 69/69 | 47 | 22 | 68.1159% | 36 |
| testcase69 | FI-SAM | 69/69 | 49 | 20 | 71.0145% | 37 |
| testcase640 | SAM_raw | 640/640 | 566 | 74 | 88.4375% | 34 |
| testcase640 | SAM | 640/640 | 566 | 74 | 88.4375% | 34 |
| testcase640 | FI-SAM | 640/640 | 566 | 74 | 88.4375% | 34 |

**Acuan tidak valid pada testcase69:** G6_N04: acuan 555 lebih rendah dari batas bawah biaya 1435. Persentase tetap memakai angka terakhir sesuai instruksi; ini adalah persentase menyamai acuan, bukan validasi optimalitas acuan.

## testcase69: FI-SAM dibanding SAM baseline terkoreksi

Dari 69 kasus valid pada keduanya: lebih murah 3, sama 64, lebih mahal 2.

| Testcase | Optimal | SAM | FI-SAM | Hasil FI-SAM |
|---|---:|---:|---:|---|
| G6_N32 | 1780 | 1820 | 1780 | Lebih baik |
| G7_N05 | 410 | 430 | 410 | Lebih baik |
| G8_S02 | 1080 | 1194 | 1152 | Lebih baik |
| G8_S05 | 1586 | 1799 | 1820 | Lebih buruk |
| G8_S06 | 4702 | 5287 | 5389 | Lebih buruk |

SAM_raw berbeda biaya/status dari baseline terkoreksi pada 0 kasus: tidak ada.
Perbandingan FI-SAM terhadap SAM_raw: {'common_feasible': 69, 'better': 3, 'equal': 64, 'worse': 2}.

### testcase69: FI-SAM dibanding program SAM asal (SAM_raw)

| Testcase | Acuan | SAM_raw | FI-SAM | Hasil FI-SAM |
|---|---:|---:|---:|---|
| G6_N32 | 1780 | 1820 | 1780 | Lebih baik |
| G7_N05 | 410 | 430 | 410 | Lebih baik |
| G8_S02 | 1080 | 1194 | 1152 | Lebih baik |
| G8_S05 | 1586 | 1799 | 1820 | Lebih buruk |
| G8_S06 | 4702 | 5287 | 5389 | Lebih buruk |
SAM_raw: hasil tidak valid: tidak ada; biaya di bawah acuan: tidak ada.
SAM: hasil tidak valid: tidak ada; biaya di bawah acuan: tidak ada.
FI-SAM: hasil tidak valid: tidak ada; biaya di bawah acuan: tidak ada.

## testcase640: FI-SAM dibanding SAM baseline terkoreksi

Dari 640 kasus valid pada keduanya: lebih murah 6, sama 627, lebih mahal 7.

| Testcase | Optimal | SAM | FI-SAM | Hasil FI-SAM |
|---|---:|---:|---:|---|
| G29_REP04 | 2246839 | 2248245 | 2247997 | Lebih baik |
| G44_REP05 | 2808503 | 2808829 | 2808917 | Lebih buruk |
| G45_REP03 | 2905168 | 2906316 | 2906064 | Lebih baik |
| G53_REP05 | 1639235 | 1675229 | 1680590 | Lebih buruk |
| G60_REP08 | 4970660 | 4970812 | 4970902 | Lebih buruk |
| G61_REP03 | 5090916 | 5092565 | 5092628 | Lebih buruk |
| G63_REP04 | 4566846 | 4570792 | 4570842 | Lebih buruk |
| G65_REP03 | 4143566 | 4145483 | 4145674 | Lebih buruk |
| G65_REP05 | 4683455 | 4685804 | 4686626 | Lebih buruk |
| G67_REP03 | 2928793 | 2944758 | 2942433 | Lebih baik |
| G70_REP01 | 834967 | 895980 | 894560 | Lebih baik |
| G72_REP08 | 1028304 | 1043092 | 1041955 | Lebih baik |
| G73_REP10 | 920804 | 941738 | 929970 | Lebih baik |

SAM_raw berbeda biaya/status dari baseline terkoreksi pada 0 kasus: tidak ada.
Perbandingan FI-SAM terhadap SAM_raw: {'common_feasible': 640, 'better': 6, 'equal': 627, 'worse': 7}.

### testcase640: FI-SAM dibanding program SAM asal (SAM_raw)

| Testcase | Acuan | SAM_raw | FI-SAM | Hasil FI-SAM |
|---|---:|---:|---:|---|
| G29_REP04 | 2246839 | 2248245 | 2247997 | Lebih baik |
| G44_REP05 | 2808503 | 2808829 | 2808917 | Lebih buruk |
| G45_REP03 | 2905168 | 2906316 | 2906064 | Lebih baik |
| G53_REP05 | 1639235 | 1675229 | 1680590 | Lebih buruk |
| G60_REP08 | 4970660 | 4970812 | 4970902 | Lebih buruk |
| G61_REP03 | 5090916 | 5092565 | 5092628 | Lebih buruk |
| G63_REP04 | 4566846 | 4570792 | 4570842 | Lebih buruk |
| G65_REP03 | 4143566 | 4145483 | 4145674 | Lebih buruk |
| G65_REP05 | 4683455 | 4685804 | 4686626 | Lebih buruk |
| G67_REP03 | 2928793 | 2944758 | 2942433 | Lebih baik |
| G70_REP01 | 834967 | 895980 | 894560 | Lebih baik |
| G72_REP08 | 1028304 | 1043092 | 1041955 | Lebih baik |
| G73_REP10 | 920804 | 941738 | 929970 | Lebih baik |
SAM_raw: hasil tidak valid: tidak ada; biaya di bawah acuan: tidak ada.
SAM: hasil tidak valid: tidak ada; biaya di bawah acuan: tidak ada.
FI-SAM: hasil tidak valid: tidak ada; biaya di bawah acuan: tidak ada.

## Berkas dan reproduksi

`python benchmark/benchmark_datasets.py`

`results.csv` memuat seluruh kasus termasuk yang biayanya sama. `results.json` memuat metadata, hash source/dataset, dan ringkasan. `logs/<dataset>/unlimited/<metode>/` memuat tabel akhir setiap run. Pengujian ini berfokus pada ketepatan biaya dan kelayakan, bukan pengukuran waktu.
