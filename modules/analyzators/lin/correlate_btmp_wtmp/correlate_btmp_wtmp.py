import os
import subprocess

triage = os.environ["TRIAGE_PATH"]
wtmp_path = f'{triage}/Xoctopus_wtmp'
btmp_path = f'{triage}/Xoctopus_btmp'

boundary = 10

def main():
    cmd = f'cat {btmp_path}' + "| awk '{print $3}' | sort | uniq -c | sort -nr"
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
     
    out = [f'{x.lstrip()}' for x in proc.stdout.split('\n')]
    out = out[:-1:]
    out = [x for x in out if len(x.split()) == 2]
    with open(f'{btmp_path}_most_IPs', 'w') as f:
        f.writelines([f'{x}\n' for x in out])

    ips = {}
    splited_out = [x.split() for x in out] 

    for pair in splited_out:
        # Отсортируем только те, которые больше границы 
        if int(pair[0]) > boundary:
            ips[pair[1]] = pair[0]

    with open(wtmp_path, 'r') as f:
        wtmp = f.readlines()

    result = {}
    for ip in ips.keys():
        for row in wtmp:
            if ip in row:
                if ip in result.keys():
                    result[ip].append(row)
                else:
                    result[ip] = [row]

    with open(f'{triage}/Xoctopus_correlate_btmp_wtmp', 'w') as f:
        for ip in result.keys():
            f.writelines([f'Successful bruteforce login from {ip} ({ips[ip]} failed attempts)\n'])
            f.writelines(result[ip])
     

if __name__ == '__main__':
    main()
