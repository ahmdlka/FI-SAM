"""Test testcase69/ and testcase640/; optimal cost is the final input token.
Run: python benchmark/benchmark_datasets.py
No iteration limit or algorithm timeout. Original datasets/sources are unchanged.
"""
import csv
import hashlib
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import benchmark as bench

ROOT=bench.ROOT
DEST=ROOT/'benchmark'/'datasets'


def read_cases(folder):
    cases=[]
    input_dir=DEST/'.build'/'inputs'/folder
    input_dir.mkdir(parents=True,exist_ok=True)
    for path in sorted((ROOT/folder).glob('*.txt')):
        tokens=path.read_text().split()
        values=list(map(int,tokens))
        m,n=values[:2]
        assert len(values)==3+m*n+m+n,path
        supply=values[2+m*n:2+m*n+m]
        demand=values[2+m*n+m:-1]
        assert sum(supply)==sum(demand),path
        costs=[values[2+i*n:2+(i+1)*n] for i in range(m)]
        lower_bound=max(sum(min(costs[i])*supply[i] for i in range(m)),
                        sum(min(costs[i][j] for i in range(m))*demand[j] for j in range(n)))
        normalized=input_dir/(path.stem+'.in')
        normalized.write_text(' '.join(tokens[:-1])+'\n')
        cases.append(dict(name=path.stem,path=normalized,original=str(path.relative_to(ROOT)),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),m=m,n=n,
            costs=costs,lower_bound=lower_bound,
            supply=supply,demand=demand,reference=values[-1]))
    return cases


def table_summary(records):
    total=len(records)
    optimal=sum(r['feasible'] and r['cost']==r['reference'] for r in records)
    return dict(total=total,feasible=sum(r['feasible'] for r in records),optimal=optimal,
                not_optimal=total-optimal,optimal_pct=100*optimal/total,
                max_iterations=max(r['iteration_counter'] or 0 for r in records))


def comparison(a,b):
    common=[(x,y) for x,y in zip(a,b) if x['feasible'] and y['feasible']]
    return dict(common_feasible=len(common),better=sum(y['cost']<x['cost'] for x,y in common),
        equal=sum(y['cost']==x['cost'] for x,y in common),worse=sum(y['cost']>x['cost'] for x,y in common))


def report(data):
    lines=['# Pengujian testcase69 dan testcase640', '',
        'Tanggal: '+data['timestamp'], '',
        'Acuan optimal adalah angka terakhir pada setiap file `.txt`. Angka itu dipisahkan dari input algoritma. '
        'Semua run tanpa batas iterasi dan tanpa timeout eksekusi. Tidak ada optimasi lanjutan. '
        'Source program dan dataset tidak diubah oleh skrip ini.', '',
        'Kedua source sekarang memakai indeks pembanding SLC `slc[q]` yang benar. '
        'Adapter SAM hanya menyesuaikan I/O, EOF, dan inisialisasi indeks diagnostik. '
        'Label SAM_raw dipertahankan dalam data untuk kompatibilitas skrip; pada versi ini source-nya identik dengan SAM.', '',
        'Keluaran diagnostik sebelum tabel akhir dinonaktifkan pada salinan uji. Alokasi akhir, biaya, '
        'dan counter iterasi tetap diperiksa. Valid berarti alokasi nonnegatif, semua supply dan demand terpenuhi, '
        'serta biaya hasil hitung ulang sama dengan biaya yang dicetak. Optimal dihitung hanya dari hasil valid '
        'yang tepat sama dengan acuan; denominator persentase adalah seluruh testcase dalam folder.', '',
        '| Dataset | Metode | Valid | Mencapai optimal | Belum optimal | Persentase optimal | Iterasi maksimum |',
        '|---|---|---:|---:|---:|---:|---:|']
    allrows=[]
    for folder,d in data['datasets'].items():
        for method,rows in d['results'].items():
            s=table_summary(rows)
            lines.append(f"| {folder} | {method} | {s['feasible']}/{s['total']} | {s['optimal']} | {s['not_optimal']} | {s['optimal_pct']:.4f}% | {s['max_iterations']} |")
            allrows.extend(dict(dataset=folder,**r) for r in rows)
    for folder,d in data['datasets'].items():
        invalid_refs=[c for c in d['cases'] if c['reference']<c.get('lower_bound',0)]
        if invalid_refs:
            lines+=['',f'**Acuan tidak valid pada {folder}:** '+ '; '.join(
                f"{c['name']}: acuan {c['reference']} lebih rendah dari batas bawah biaya {c['lower_bound']}"
                for c in invalid_refs)+'. Persentase tetap memakai angka terakhir sesuai instruksi; ini adalah persentase menyamai acuan, bukan validasi optimalitas acuan.']
        a,b=d['results']['SAM'],d['results']['FI-SAM']
        p=comparison(a,b)
        lines+=['',f'## {folder}: FI-SAM dibanding SAM baseline terkoreksi','',
            f"Dari {p['common_feasible']} kasus valid pada keduanya: lebih murah {p['better']}, sama {p['equal']}, lebih mahal {p['worse']}.",'',
            '| Testcase | Optimal | SAM | FI-SAM | Hasil FI-SAM |', '|---|---:|---:|---:|---|']
        for x,y in zip(a,b):
            if x['cost']!=y['cost'] and x['feasible'] and y['feasible']:
                lines.append(f"| {x['case']} | {x['reference']} | {x['cost']} | {y['cost']} | {'Lebih baik' if y['cost']<x['cost'] else 'Lebih buruk'} |")
        raw=d['results']['SAM_raw']
        different=[x['case'] for x,y in zip(raw,a) if (x['cost'],x['feasible'])!=(y['cost'],y['feasible'])]
        lines+=['',f"SAM_raw berbeda biaya/status dari baseline terkoreksi pada {len(different)} kasus: "+(', '.join(different) or 'tidak ada')+'.',
                'Perbandingan FI-SAM terhadap SAM_raw: '+str(comparison(raw,b))+'.']
        lines+=['',f'### {folder}: FI-SAM dibanding program SAM asal (SAM_raw)','',
                '| Testcase | Acuan | SAM_raw | FI-SAM | Hasil FI-SAM |', '|---|---:|---:|---:|---|']
        for x,y in zip(raw,b):
            if x['cost']!=y['cost'] and x['feasible'] and y['feasible']:
                lines.append(f"| {x['case']} | {x['reference']} | {x['cost']} | {y['cost']} | {'Lebih baik' if y['cost']<x['cost'] else 'Lebih buruk'} |")
        for method,rows in d['results'].items():
            invalid=[r['case'] for r in rows if not r['feasible']]
            below=[r['case'] for r in rows if r['feasible'] and r['cost']<r['reference']]
            lines += [f'{method}: hasil tidak valid: '+(', '.join(invalid) or 'tidak ada')+
                      '; biaya di bawah acuan: '+(', '.join(below) or 'tidak ada')+'.']
    lines+=['','## Berkas dan reproduksi','',
        '`python benchmark/benchmark_datasets.py`', '',
        '`results.csv` memuat seluruh kasus termasuk yang biayanya sama. `results.json` memuat metadata, '
        'hash source/dataset, dan ringkasan. `logs/<dataset>/unlimited/<metode>/` memuat tabel akhir setiap run. '
        'Pengujian ini berfokus pada ketepatan biaya dan kelayakan, bukan pengukuran waktu.', '']
    (DEST/'BENCHMARK.md').write_text('\n'.join(lines),encoding='utf-8')
    with (DEST/'results.csv').open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(allrows[0]))
        writer.writeheader();writer.writerows(allrows)


def main():
    DEST.mkdir(exist_ok=True)
    bench.BUILD=DEST/'.build'
    bench.BUILD.mkdir(exist_ok=True)
    data=dict(timestamp=datetime.now(ZoneInfo('Asia/Jakarta')).isoformat(),
        source_hashes={p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['SAM.c','FI-SAM.c']},
        compiler='gcc -std=c99 -O2 -Wall -Wextra',datasets={})
    executables={}
    for method,source in bench.sources().items():
        marker='\t\tjumlah_ER = 0;\n\n\t\tprintf("\\n\\n");'
        source=bench.replace_once(source,marker,'\t\tbenchmark_emit = 1;\n'+marker)
        # Macro only suppresses output; allocation and termination logic are unchanged.
        prefix='#include <stdio.h>\nstatic int benchmark_emit = 0;\n#define printf(...) (benchmark_emit ? printf(__VA_ARGS__) : 0)\n'
        executables[method]=bench.compile_c(method,prefix+source)
    for folder in ['testcase69','testcase640']:
        cases=read_cases(folder)
        expected=69 if folder=='testcase69' else 640
        assert len(cases)==expected
        bench.OUT=DEST/'logs'/folder
        d=dict(cases=[{k:v for k,v in c.items() if k not in ['path','costs','supply','demand']} for c in cases],results={})
        for method,exe in executables.items():
            records=[]
            for i,case in enumerate(cases):
                row=bench.functional(exe,case,'unlimited',method)
                # Each completed iteration performs one transfer; its diagnostic
                # print is suppressed. Fit evaluations cannot be read from this log.
                row['transfers']=row['iteration_counter']
                row['fit_evaluations']=None
                records.append(row)
                if (i+1)%100==0:print(folder,method,i+1,'/',len(cases),flush=True)
            d['results'][method]=records
            print(folder,method,table_summary(records),flush=True)
        data['datasets'][folder]=d
        (DEST/'results.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    report(data)
    print('REPORT',DEST/'BENCHMARK.md',flush=True)


if __name__=='__main__':main()
