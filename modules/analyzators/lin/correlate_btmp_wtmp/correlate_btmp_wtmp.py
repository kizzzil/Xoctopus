import os
import sys
from collections import Counter

triage = os.environ["TRIAGE_PATH"]
wtmp_path = f'{triage}/Xoctopus_wtmp'
btmp_path = f'{triage}/Xoctopus_btmp'

boundary = 10

def main():
    if not os.path.exists(btmp_path) or not os.path.exists(wtmp_path):
        print('Module correlate_btmp_wtmp: Warning! run parser wtmp first')
        sys.exit(0)

    # Подсчет неудачных попыток входа по IP (3-я колонка вывода last)
    with open(btmp_path, 'r', encoding='utf-8', errors='ignore') as f:
        counter = Counter(line.split()[2] for line in f
                          if len(line.split()) >= 3 and not line.startswith(('btmp begins', 'wtmp begins')))

    out = [f'{count} {ip}' for ip, count in counter.most_common()]
    with open(f'{btmp_path}_most_IPs', 'w') as f:
        f.writelines([f'{x}\n' for x in out])

    # Отсортируем только те, которые больше границы
    ips = {ip: count for ip, count in counter.items() if count > boundary}

    with open(wtmp_path, 'r', encoding='utf-8', errors='ignore') as f:
        wtmp = f.readlines()

    result = {}
    for ip in ips.keys():
        for row in wtmp:
            if ip in row.split():
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
