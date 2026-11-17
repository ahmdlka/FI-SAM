"""Time entire testcase69/testcase640 suites. Run: python benchmark/time_datasets.py."""
import csv
import hashlib
import json
import os
import platform
import statistics
import subprocess
from datetime import datetime
from zoneinfo import ZoneInfo
import benchmark as bench
import benchmark_datasets as datasets

DRIVER=r'''
#undef main
#undef printf
#include <string.h>
typedef struct { char path[4096]; long long expected; } Case;
static double ticks(void){ LARGE_INTEGER x; QueryPerformanceCounter(&x); return (double)x.QuadPart; }
static void suite(Case *cases, int n){
    for(int i=0;i<n;i++){
        char *args[]={"algorithm",cases[i].path,NULL};
        if(algorithm_main(2,args)!=0) exit(5);
    }
}
int main(int argc,char **argv){
    if(argc!=2)return 2;
    FILE *manifest=fopen(argv[1],"r"); if(!manifest)return 3;
    int n; if(fscanf(manifest,"%d\n",&n)!=1)return 3;
    Case *cases=calloc((size_t)n,sizeof(Case)); if(!cases)return 4;
    for(int i=0;i<n;i++){
        if(fscanf(manifest,"%lld\n",&cases[i].expected)!=1)return 3;
        if(!fgets(cases[i].path,sizeof(cases[i].path),manifest))return 3;
        cases[i].path[strcspn(cases[i].path,"\r\n")]=0;
    }
    fclose(manifest);
    printf("{\"mismatches\":["); int mismatches=0;
    for(int i=0;i<n;i++){
        char *args[]={"algorithm",cases[i].path,NULL};
        long long before=benchmark_sink;
        if(algorithm_main(2,args)!=0)return 5;
        long long actual=benchmark_sink-before;
        if(actual!=cases[i].expected){
            printf("%s{\"index\":%d,\"expected\":%lld,\"actual\":%lld}",
                   mismatches++ ? "," : "",i,cases[i].expected,actual);
        }
    }
    for(int warmup=0;warmup<3;warmup++)suite(cases,n);
    LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);
    int batch=1;
    while(1){
        double start=ticks();
        for(int b=0;b<batch;b++)suite(cases,n);
        if((ticks()-start)/freq.QuadPart>=0.05)break;
        batch*=2;
    }
    printf("],\"batch\":%d,\"samples_ms\":[",batch);
    for(int sample=0;sample<11;sample++){
        double start=ticks();
        for(int b=0;b<batch;b++)suite(cases,n);
        double ms=(ticks()-start)*1000.0/freq.QuadPart/batch;
        printf("%s%.9f",sample ? "," : "",ms);
    }
    printf("]}\n");free(cases);return 0;
}
'''


def main():
    out=datasets.DEST
    previous=json.loads((out/'results.json').read_text())
    for name,digest in previous['source_hashes'].items():
        assert hashlib.sha256((bench.ROOT/name).read_bytes()).hexdigest()==digest
    bench.BUILD=out/'.build'
    executables={}
    for name,src in bench.sources().items():
        if name=='SAM_raw':
            continue  # SAM_raw is now an alias of corrected SAM; time each program once.
        src=bench.replace_once(src,'printf("Total Alokasi tabel adalah: %d\\n", total_alloc);',
                               'benchmark_sink += total_alloc;')
        executables[name]=bench.compile_c(name+'_suite_timed',bench.TIMING_PREFIX+src+DRIVER)
    data=dict(timestamp=datetime.now(ZoneInfo('Asia/Jakarta')).isoformat(),
        platform=platform.platform(),cpu=os.environ.get('PROCESSOR_IDENTIFIER','unknown'),
        compiler=subprocess.check_output(['gcc','--version'],text=True).splitlines()[0],
        flags='-std=c99 -O2 -Wall -Wextra',samples_per_session=11,sessions=3,
        source_hashes=previous['source_hashes'],datasets={})
    for folder in ['testcase69','testcase640']:
        cases=datasets.read_cases(folder)
        results={name:[] for name in executables}
        for name in executables:
            expected=previous['datasets'][folder]['results'][name]
            manifest=bench.BUILD/(folder+'_'+name+'.manifest')
            lines=[str(len(cases))]
            for case,row in zip(cases,expected):
                assert case['name']==row['case']
                assert case['sha256']==next(c['sha256'] for c in previous['datasets'][folder]['cases'] if c['name']==case['name'])
                lines += [str(row['cost']),str(case['path'])]
            manifest.write_text('\n'.join(lines)+'\n')
        # Rotate process order over three independent sessions per dataset.
        for session in range(3):
            names=list(executables)
            names=names[session:]+names[:session]
            for name in names:
                result=subprocess.run([str(executables[name]),str(bench.BUILD/(folder+'_'+name+'.manifest'))],
                    capture_output=True,text=True,check=True)
                sample=json.loads(result.stdout)
                sample['session']=session+1
                results[name].append(sample)
                print(folder,name,'session',session+1,'median suite ms',statistics.median(sample['samples_ms']),
                      'cost mismatches',len(sample['mismatches']),flush=True)
        d=dict(count=len(cases),results=results,summary={})
        for name,sessions in results.items():
            samples=[t for s in sessions for t in s['samples_ms']]
            median=statistics.median(samples)
            q=statistics.quantiles(samples,n=4)
            d['summary'][name]=dict(median_suite_ms=median,mean_per_case_us=median*1000/len(cases),
                iqr_suite_ms=q[2]-q[0],sessions_median_ms=[statistics.median(s['samples_ms']) for s in sessions],
                cost_mismatches=sum(len(s['mismatches']) for s in sessions))
        data['datasets'][folder]=d
        (out/'timing.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    lines=['# Kecepatan SAM dan FI-SAM', '', 'Tanggal: '+data['timestamp'], '',
        'Tanpa batas iterasi. GCC '+data['compiler']+'; '+data['flags']+'. '+data['platform']+'. CPU: '+data['cpu']+'.', '',
        'Pengukuran memakai QueryPerformanceCounter dalam proses. Satu suite menjalankan seluruh testcase dalam folder. '
        'Setiap pemanggilan tetap membaca dan menutup file input; angka optimal terakhir dipisahkan sebelumnya. '
        'Startup proses, kompilasi, dan semua printf dikeluarkan. Biaya akhir dikonsumsi oleh volatile sink '
        'agar perhitungan tidak dibuang compiler. Cache file hangat.', '',
        'Tiga sesi independen dengan urutan program dirotasi, masing-masing 3 warmup suite dan 11 sampel; '
        'batch adaptif minimal 50 ms. Angka tabel adalah median dari 33 sampel waktu suite. '
        'Rata-rata per kasus = median suite / jumlah kasus, bukan median dari waktu masing-masing kasus.', '',
        'Kedua source telah memakai koreksi indeks SLC yang sama. SAM diuji dengan adapter I/O/EOF '
        'dan inisialisasi indeks diagnostik. Tidak ada varian SAM dengan indeks SLC lama dalam pengukuran ini.', '',
        '| Dataset | Program | Median suite (ms) | Rata-rata per kasus (µs) | IQR suite (ms) | Biaya preflight berbeda |',
        '|---|---|---:|---:|---:|---:|']
    rows=[]
    for folder,d in data['datasets'].items():
        if rows:
            lines+=['', '| Dataset | Program | Median suite (ms) | Rata-rata per kasus (µs) | IQR suite (ms) | Biaya preflight berbeda |',
                    '|---|---|---:|---:|---:|---:|']
        for name,s in d['summary'].items():
            lines.append(f"| {folder} | {name} | {s['median_suite_ms']:.4f} | {s['mean_per_case_us']:.3f} | {s['iqr_suite_ms']:.4f} | {s['cost_mismatches']} |")
            rows.append(dict(dataset=folder,method=name,**{k:v for k,v in s.items() if k!='sessions_median_ms'}))
        fi=d['summary']['FI-SAM']['median_suite_ms']
        for name in ['SAM']:
            a=d['summary'][name]['median_suite_ms']
            lines+=['',f"{folder}: FI-SAM {(fi/a-1)*100:+.3f}% waktu dibanding {name}; "
                    f"rasio FI/SAM {fi/a:.5f}×. Median sesi {name}: {d['summary'][name]['sessions_median_ms']}; "
                    f"FI-SAM: {d['summary']['FI-SAM']['sessions_median_ms']}."]
    lines+=['','Durasi bergantung pada mesin, cache, dan beban OS. Selisih kecil dibanding variasi sampel '
            'tidak membuktikan metode lebih cepat. Semua pemeriksaan biaya preflight dilaporkan.', '',
            'Reproduksi: `python benchmark/time_datasets.py`. Sampel mentah: `timing.json`. Ringkasan: `timing.csv`.', '']
    (out/'TIMING.md').write_text('\n'.join(lines),encoding='utf-8')
    with (out/'timing.csv').open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    print('REPORT',out/'TIMING.md',flush=True)


if __name__=='__main__':main()
