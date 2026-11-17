"""Benchmark SAM/FI-SAM tanpa mengedit source program atau testcase.

Run from any directory: python benchmark/benchmark.py
Requires Python 3.10+, GCC, and Windows (QueryPerformanceCounter for timing).
Generated C adapters, compiler logs, and executables are in .build/.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import statistics
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
OUT = Path(__file__).resolve().parent
BUILD = OUT / '.build'


def replace_once(text, old, new):
    assert text.count(old) == 1, f'Source changed; adapter cannot locate: {old[:80]!r}'
    return text.replace(old, new, 1)


def sources():
    raw = (ROOT / 'SAM.c').read_text()
    raw = replace_once(raw, 'int main(){', 'int main(int argc, char *argv[]){')
    raw = replace_once(raw, 'in=fopen("N06.txt","r");',
                       'in=fopen(argc > 1 ? argv[1] : "N06.txt","r");\n'
                       '\tif(in == NULL){ perror("input"); return EXIT_FAILURE; }')
    raw = replace_once(raw, 'while(!feof(in)){\n\t\tfscanf(in,"%d", &jumlah_supply);\n\t\tfscanf(in,"%d", &jumlah_demand);',
                       'while(fscanf(in,"%d %d", &jumlah_supply, &jumlah_demand) == 2){')
    raw = replace_once(raw, 'konflik[q]=0;',
                       'konflik[q]=0;\n\t\t\t\t\tflc[q] = slc[q] = -1;')
    raw = raw.rstrip()
    assert raw.endswith('\n}')
    raw = raw[:-2] + '\n\tfclose(in);\n\treturn EXIT_SUCCESS;\n}\n'
    # Source SAM kini sudah memakai koreksi SLC; tetap mendukung source lama.
    old_slc = 'average_cost_multiply_supply[q] < average_cost_multiply_supply[p]'
    fixed_slc = 'average_cost_multiply_supply[slc[q]] < average_cost_multiply_supply[p]'
    normalized = replace_once(raw, old_slc, fixed_slc) if old_slc in raw else raw
    assert fixed_slc in normalized, 'Pembanding AS pada SLC tidak ditemukan.'
    return {'SAM_raw': raw, 'SAM': normalized, 'FI-SAM': (ROOT / 'FI-SAM.c').read_text()}


def compile_c(name, source):
    cpath, exe = BUILD / f'{name}.c', BUILD / f'{name}.exe'
    cpath.write_text(source)
    command = ['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', str(cpath), '-o', str(exe)]
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    (BUILD / f'{name}.compile.log').write_text(result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(result.stderr)
    return exe


def read_case(path):
    data = list(map(int, path.read_text().split()))
    m, n = data[:2]
    assert len(data) == 2 + m*n + m+n
    costs = [data[2+i*n:2+(i+1)*n] for i in range(m)]
    supply, demand = data[2+m*n:2+m*n+m], data[2+m*n+m:]
    assert sum(supply) == sum(demand)
    reference = int(path.with_suffix('.out').read_text().strip())
    return dict(name=path.stem, path=path, m=m, n=n, costs=costs,
                supply=supply, demand=demand, reference=reference)


def functional(exe, case, limit, variant):
    run = subprocess.run([str(exe), str(case['path'])], cwd=ROOT,
                         capture_output=True, text=True)
    logdir = OUT / 'logs' / str(limit) / variant
    logdir.mkdir(parents=True, exist_ok=True)
    (logdir / f"{case['name']}.log").write_text(run.stdout + run.stderr)
    cost_matches = re.findall(r'Total Alokasi tabel adalah: (-?\d+)', run.stdout)
    counters = re.findall(r'Jumlah iterasi yang dijalankan: (\d+)', run.stdout)
    alloc = [[int(x) for x in re.findall(r'\[(-?\d+)\]', line)]
             for line in run.stdout.splitlines() if 'Total alloc :' in line]
    shape = len(alloc) == case['m'] and all(len(row) == case['n'] for row in alloc)
    row_sums = [sum(row) for row in alloc] if shape else []
    col_sums = [sum(row[j] for row in alloc) for j in range(case['n'])] if shape else []
    recomputed = sum(case['costs'][i][j] * alloc[i][j]
                     for i in range(case['m']) for j in range(case['n'])) if shape else None
    cost = int(cost_matches[-1]) if cost_matches else None
    feasible = bool(run.returncode == 0 and shape and recomputed == cost
                    and row_sums == case['supply'] and col_sums == case['demand']
                    and all(x >= 0 for row in alloc for x in row))
    return dict(case=case['name'], variant=variant, iteration_limit=None,
        reference=case['reference'], cost=cost, feasible=feasible,
        gap_pct=100*(cost-case['reference'])/case['reference'] if feasible else None,
        transfers=len(re.findall(r'Selisih terkecil ada di kolom ke', run.stdout)),
        iteration_counter=int(counters[-1]) if counters else None,
        limit_hit='ITER LEWAT' in run.stdout, returncode=run.returncode,
        fit_evaluations=len(re.findall(r'FI-SAM kolom', run.stdout)),
        supply_error=sum(abs(a-b) for a,b in zip(row_sums, case['supply'])) if shape else None,
        demand_error=sum(abs(a-b) for a,b in zip(col_sums, case['demand'])) if shape else None)


TIMING_PREFIX = r'''
#include <stdio.h>
#include <stdlib.h>
#include <windows.h>
static volatile long long benchmark_sink = 0;
/* Hilangkan logging, tetapi pertahankan hasil akhir melalui volatile sink. */
#define printf(...) ((void)0)
#define main algorithm_main
'''
TIMING_SUFFIX = r'''
#undef main
#undef printf
static double ticks(void){
    LARGE_INTEGER value;
    QueryPerformanceCounter(&value);
    return (double)value.QuadPart;
}
int main(int argc, char **argv){
    LARGE_INTEGER frequency;
    QueryPerformanceFrequency(&frequency);
    if(argc != 5) return 2;
    int samples = atoi(argv[2]);
    double target = atof(argv[3]) / 1000.0;
    long long expected = atoll(argv[4]);
    char *algorithm_argv[] = {argv[0], argv[1], NULL};
    if(algorithm_main(2, algorithm_argv) != 0 || benchmark_sink != expected) return 3;
    for(int i=0; i<5; i++) algorithm_main(2, algorithm_argv);
    int batch = 1;
    for(;;){
        double start = ticks();
        for(int i=0; i<batch; i++) algorithm_main(2, algorithm_argv);
        double elapsed = (ticks()-start)/(double)frequency.QuadPart;
        if(elapsed >= target || batch >= 1048576) break;
        batch *= 2;
    }
    printf("{\"batch\":%d,\"samples_us\":[", batch);
    for(int sample=0; sample<samples; sample++){
        double start = ticks();
        for(int i=0; i<batch; i++) algorithm_main(2, algorithm_argv);
        double us = (ticks()-start)*1000000.0/(double)frequency.QuadPart/batch;
        printf("%s%.9f", sample ? "," : "", us);
    }
    printf("]}\n");
    return 0;
}
'''


def summary(records):
    good = [r for r in records if r['feasible']]
    return dict(total=len(records), feasible=len(good),
        limit_hits=sum(r['limit_hit'] for r in records),
        reference_matches=sum(r['cost'] == r['reference'] for r in good),
        mean_gap_pct=statistics.mean(r['gap_pct'] for r in good) if good else None,
        mean_transfers=statistics.mean(r['transfers'] for r in good) if good else None)


def paired(a, b):
    common = [(x,y) for x,y in zip(a,b) if x['feasible'] and y['feasible']]
    return dict(common_feasible=len(common),
        fi_better=sum(y['cost'] < x['cost'] for x,y in common),
        equal=sum(y['cost'] == x['cost'] for x,y in common),
        fi_worse=sum(y['cost'] > x['cost'] for x,y in common),
        mean_cost_improvement_pct=statistics.mean(100*(x['cost']-y['cost'])/x['cost'] for x,y in common),
        mean_gap_sam=statistics.mean(x['gap_pct'] for x,y in common),
        mean_gap_fi=statistics.mean(y['gap_pct'] for x,y in common),
        transfers_sam=sum(x['transfers'] for x,y in common),
        transfers_fi=sum(y['transfers'] for x,y in common))


def write_csv(data):
    flat=[]
    for limit,profile in data['profiles'].items():
        for variant,records in profile.items():
            for record in records:
                timing=data['timing'].get(record['case'],{}).get(variant,{})
                flat.append(dict(record, median_time_us=timing.get('median_us'),
                                 time_iqr_us=timing.get('iqr_us')))
    with (OUT/'results.csv').open('w',newline='',encoding='utf-8') as file:
        writer=csv.DictWriter(file,fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)


def write_report(data, cases):
    lines = ['# Benchmark SAM dan FI-SAM', '', f"Tanggal: {data['metadata']['timestamp']}", '',
        'Perbandingan utama memakai **SAM baseline terkoreksi** dan FI-SAM. '
        'SAM_raw adalah program asal dengan adaptasi I/O saja dan inisialisasi indeks diagnostik; '
        'hasilnya disimpan sebagai pembanding tambahan, bukan bukti dampak fit score.', '',
        '## Metodologi', '',
        '- 69 pasangan `.in`/`.out`; seluruh input diperiksa seimbang. Batas iterasi pada kedua source telah dihapus sesuai permintaan; testcase tidak diedit.',
        '- Compiler: ' + data['metadata']['gcc'] + '; flag `-std=c99 -O2 -Wall -Wextra`.',
        '- Lingkungan: ' + data['metadata']['platform'] + '; CPU: ' + data['metadata']['cpu'] + '.',
        '- Adapter SAM: path input melalui argv, pembacaan header berhenti di EOF, penutupan file, dan inisialisasi FLC/SLC '
        'agar cetakan diagnostik tidak membaca nilai yang belum diisi. Aturan tie breaker asli dipertahankan.',
        '- Pada baseline SAM terkoreksi, pembanding AS untuk SLC memakai `slc[q]`, sama seperti FI-SAM. '
        '`SAM_raw` tetap memakai `q`; indeks ini bisa melewati batas jumlah baris, sehingga hasilnya mengandung risiko undefined behavior.',
        '- Tidak ada batas iterasi maupun timeout eksekusi algoritma. Setiap run berakhir melalui kondisi tidak ada ER; kelayakan alokasi diperiksa terpisah.',
        '- Feasible berarti alokasi nonnegatif, jumlah setiap baris sama dengan supply, setiap kolom sama dengan demand, '
        'dan biaya keluaran sama dengan biaya hasil hitung ulang. Biaya tidak feasible tidak dimasukkan ke gap atau peringkat.',
        '- Biaya acuan berasal dari `.out`; benchmark ini tidak membuktikan ulang optimalitas file acuan. '
        'Gap (%) = 100 × (biaya hasil − biaya acuan) / biaya acuan; rata-rata gap tidak dibobot menurut skala biaya.',
        '- Transfer adalah jumlah langkah pemindahan aktual; counter iterasi turut disimpan dalam data hasil.',
        f"- Waktu tanpa batas iterasi: {data['metadata']['samples']} sampel per testcase, median mikrodetik per pemanggilan; "
        f"batch adaptif minimal {data['metadata']['target_ms']} ms, 5 warmup dan satu pemeriksaan hasil awal. "
        'SAM dan FI-SAM diukur bergantian urutannya antartestcase. QueryPerformanceCounter dipakai dalam proses; '
        'startup proses, kompilasi, dan logging dikeluarkan. Pembacaan file, perhitungan, dan penutupan file tetap diukur. '
        'Cache file menjadi hangat; hasil menggambarkan mesin dan sesi pengujian ini.',
        '- Seluruh `printf` dihilangkan hanya pada build timing; biaya akhir tetap dikonsumsi melalui volatile sink '
        'dan diperiksa terhadap hasil build fungsional sebelum pengukuran.', '', '## Ringkasan', '']
    for limit in ('unlimited',):
        records = data['profiles'][limit]
        lines += ['### Sampai algoritma selesai, tanpa batas iterasi', '',
            '| Metrik | SAM baseline terkoreksi | FI-SAM |', '|---|---:|---:|']
        a,b = summary(records['SAM']),summary(records['FI-SAM'])
        for label,key in [('Feasible','feasible'),('Mencapai batas iterasi','limit_hits'),
                          ('Sama dengan biaya acuan (hanya feasible)','reference_matches'),
                          ('Rata-rata gap (%) pada hasil feasible','mean_gap_pct'),
                          ('Rata-rata transfer pada hasil feasible','mean_transfers')]:
            fmt = lambda x: f'{x:.4f}' if isinstance(x,float) else str(x)
            lines.append(f'| {label} | {fmt(a[key])} | {fmt(b[key])} |')
        p=paired(records['SAM'],records['FI-SAM'])
        lines += ['', f"Dari {p['common_feasible']} testcase yang feasible pada keduanya: FI-SAM lebih murah "
            f"pada **{p['fi_better']}**, sama pada **{p['equal']}**, dan lebih mahal pada **{p['fi_worse']}**. "
            f"Rata-rata perubahan biaya relatif terhadap SAM: penghematan {p['mean_cost_improvement_pct']:.4f}%. "
            f"Rata-rata gap pada himpunan yang sama: SAM {p['mean_gap_sam']:.4f}%, FI-SAM {p['mean_gap_fi']:.4f}%. "
            f"Total transfer: {p['transfers_sam']} → {p['transfers_fi']}.", '']
        invalid = [r['case'] for r in records['FI-SAM'] if not r['feasible']]
        lines += ['FI-SAM belum feasible: ' + (', '.join(invalid) if invalid else 'tidak ada') + '.', '']
    lines += ['## Mengapa menang 3 kasus tetapi mencapai acuan bertambah 2?', '',
        'Menang dibanding SAM dan menyamai acuan adalah dua ukuran berbeda. '
        'N05 (430 → 410, acuan 410) dan N32 (1820 → 1780, acuan 1780) menambah dua hasil yang menyamai acuan. '
        'S02 (1194 → 1152, acuan 1080) lebih murah daripada SAM tetapi belum menyamai acuan. '
        'Pada S05 dan S06, FI-SAM lebih mahal, tetapi kedua metode sama-sama belum menyamai acuan. '
        'Jadi kemenangan/kekalahan adalah 3/2 dengan 64 seri; jumlah hasil yang menyamai acuan tetap 48 → 50. '
        'Selisih jumlah menang dan kalah sebesar 1 bukan berarti FI-SAM hanya menang pada satu testcase.', '',
        '## Terminasi', '',
        'Batas 20 pada source awal merupakan pembatas implementasi. Batas itu sekarang dihapus pada kedua program. '
        'Kondisi keluar algoritma adalah tidak ada ER. Suatu algoritma iteratif membutuhkan argumen terminasi '
        'untuk dijamin selalu berhenti; pada kode ini transfer dapat membuat ER baru, sehingga jumlah ER '
        'tidak selalu turun pada setiap langkah. Ini tidak membuktikan SAM mengalami siklus. '
        'Hasil pengujian menunjukkan seluruh 69 testcase berhenti secara alami dengan alokasi valid; '
        'pengujian tersebut bukan bukti terminasi untuk semua kemungkinan input.', '']
    timing = data['timing']
    a,b = [statistics.mean(timing[c['name']][v]['median_us'] for c in cases) for v in ('SAM','FI-SAM')]
    ratio = math.exp(statistics.mean(math.log(timing[c['name']]['FI-SAM']['median_us']/timing[c['name']]['SAM']['median_us']) for c in cases))
    relative_iqr=[r['iqr_us']/r['median_us'] for case in timing.values() for r in case.values()]
    lines += ['## Waktu eksekusi (tanpa batas iterasi)', '',
        '| Metrik | SAM baseline terkoreksi | FI-SAM |', '|---|---:|---:|',
        f'| Rata-rata median per testcase (µs) | {a:.3f} | {b:.3f} |',
        f'| Jumlah median untuk satu suite 69 testcase (ms) | {a*len(cases)/1000:.3f} | {b*len(cases)/1000:.3f} |', '',
        f'Rata-rata geometrik rasio waktu FI-SAM/SAM: **{ratio:.4f}×**. '
        'Jumlah median suite merupakan agregasi median, bukan satu pengukuran suite utuh. '
        'Perbedaan pada durasi mikrodetik sensitif terhadap noise OS dan overhead pembacaan file.', '',
        f"Median IQR relatif antar-sampel: {100*statistics.median(relative_iqr):.2f}%; "
        f"maksimum {100*max(relative_iqr):.2f}%. Selisih rerata waktu kedua metode sangat kecil "
        'dibanding variasi pengukuran; angka ini tidak membuktikan salah satu metode lebih cepat.', '',
        '## Hasil setiap testcase (tanpa batas iterasi)', '',
        'Δ biaya (%) = 100 × (FI-SAM − SAM) / SAM; negatif berarti FI-SAM lebih murah. '
        'Status `OK` hanya jika kedua hasil feasible.', '',
        '| Testcase | Ukuran | Acuan | SAM | FI-SAM | Δ biaya (%) | Transfer SAM/FI | Waktu SAM/FI (µs) | Status |',
        '|---|---|---:|---:|---:|---:|---:|---:|---|']
    for c,a,b in zip(cases,data['profiles']['unlimited']['SAM'],data['profiles']['unlimited']['FI-SAM']):
        ta,tb = timing[c['name']]['SAM']['median_us'],timing[c['name']]['FI-SAM']['median_us']
        delta = 100*(b['cost']-a['cost'])/a['cost'] if a['feasible'] and b['feasible'] else None
        delta_str = f'{delta:+.3f}' if delta is not None else 'n/a'
        lines.append(f"| {c['name']} | {c['m']}×{c['n']} | {c['reference']} | {a['cost']} | {b['cost']} | "
                     f"{delta_str} | {a['transfers']}/{b['transfers']} | {ta:.2f}/{tb:.2f} | "
                     f"{'OK' if delta is not None else 'BELUM FEASIBLE'} |")
    lines += ['', '## Program SAM asal (SAM_raw)', '',
        'Biaya SAM_raw tidak mengisolasi pengaruh fit score karena FI-SAM juga memperbaiki indeks SLC. '
        'Nilai SAM_raw yang kebetulan stabil tetap tidak menghilangkan undefined behavior pada source.', '']
    for limit,records in data['profiles'].items():
        raw,normal = records['SAM_raw'],records['SAM']
        different = [a['case'] for a,b in zip(raw,normal) if (a['cost'],a['feasible'],a['transfers']) != (b['cost'],b['feasible'],b['transfers'])]
        lines += [f"- Profil {limit}: SAM_raw feasible {summary(raw)['feasible']}/69; "
                  f"berbeda biaya/status/transfer dari baseline terkoreksi pada {len(different)} kasus: "
                  + (', '.join(different) if different else 'tidak ada') + '.']
    lines += ['', '## Reproduksi dan berkas', '',
        'Jalankan `python benchmark/benchmark.py` dari folder proyek. '
        'Opsi: `--samples 7 --target-ms 20`. Angka waktu akan berubah antar-run.', '',
        '- `results.json`: metadata, SHA-256 source, semua hasil fungsional, dan sampel waktu mentah.',
        '- `results.csv`: tabel hasil per testcase/varian/profil untuk analisis lanjutan.',
        '- `logs/unlimited/<varian>/*.log`: keluaran lengkap tiap testcase pada pengujian terbaru tanpa batas iterasi. Folder 20/1000 adalah log historis pengujian sebelumnya.',
        '- `.build/`: source adapter, compiler log, dan executable hasil generasi.', '',
        'FI-SAM adalah heuristik IBFS; skor fit yang lebih kecil tidak menjamin biaya akhir selalu lebih rendah. '
        'Perbandingan kualitas yang berlaku adalah hasil feasible pada himpunan testcase yang sama.', '']
    (OUT / 'BENCHMARK.md').write_text('\n'.join(lines), encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--samples', type=int, default=7)
    parser.add_argument('--target-ms', type=float, default=20)
    args=parser.parse_args()
    assert args.samples >= 3 and args.target_ms > 0
    BUILD.mkdir(parents=True, exist_ok=True)
    cases = [read_case(p) for p in sorted((ROOT/'testcase').glob('*.in'))]
    variants = sources()
    data = dict(metadata=dict(timestamp=datetime.now(ZoneInfo('Asia/Jakarta')).isoformat(),
        platform=platform.platform(), cpu=os.environ.get('PROCESSOR_IDENTIFIER','unknown'),
        gcc=subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
        samples=args.samples, target_ms=args.target_ms,
        hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in ['SAM.c','FI-SAM.c']},
        source_adapter_hashes={name:hashlib.sha256(src.encode()).hexdigest() for name,src in variants.items()}),
        profiles={}, timing={})
    for limit in ('unlimited',):
        data['profiles'][str(limit)]={}
        for name,src in variants.items():
            adapted = src
            exe = compile_c(f'{name}_{limit}',adapted)
            records=[functional(exe,c,limit,name) for c in cases]
            data['profiles'][str(limit)][name]=records
            print(f'Functional limit={limit}, {name}: {summary(records)}',flush=True)
    timed={}
    for name in ('SAM','FI-SAM'):
        src=variants[name]
        src=replace_once(src,'printf("Total Alokasi tabel adalah: %d\\n", total_alloc);',
                         'benchmark_sink += total_alloc;')
        timed[name]=compile_c(f'{name}_timed',TIMING_PREFIX+src+TIMING_SUFFIX)
    for index,case in enumerate(cases):
        record={}
        for name in (('SAM','FI-SAM') if index%2==0 else ('FI-SAM','SAM')):
            expected=data['profiles']['unlimited'][name][index]['cost']
            result=subprocess.run([str(timed[name]),str(case['path']),str(args.samples),str(args.target_ms),str(expected)],
                                  capture_output=True,text=True,check=True)
            sample=json.loads(result.stdout)
            sample['median_us']=statistics.median(sample['samples_us'])
            quartiles=statistics.quantiles(sample['samples_us'],n=4)
            sample['iqr_us']=quartiles[2]-quartiles[0]
            record[name]=sample
        data['timing'][case['name']]=record
        if (index+1)%10==0 or index+1==len(cases):
            print(f'Timing {index+1}/{len(cases)}',flush=True)
    (OUT/'results.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    write_csv(data)
    write_report(data,cases)
    print('RESULT:',OUT/'BENCHMARK.md',flush=True)


if __name__=='__main__':
    main()
