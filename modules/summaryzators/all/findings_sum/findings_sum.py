import os
import csv
import xoctopus_log as log

# Блок десериализации путей триажа (все ОС)
triages = os.environ['TRIAGE_PATHES']
triages = [pair.split(',') for pair in triages.split(";")]
triages = [path for path, os_name in triages]

def main():
    ## Сбор Xoctopus_findings.csv всех триажей в один файл
    rows = []
    for path in triages:
        findings_path = os.path.join(path, log.FINDINGS_FILE)
        if not os.path.exists(findings_path):
            continue
        with open(findings_path, 'r', encoding='utf-8', newline='') as f:
            rows.extend(csv.DictReader(f))

    with open(f"{os.environ['XOCTOPUS_RUN_DIR']}/super_{log.FINDINGS_FILE}", 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=log.FINDINGS_HEADER)
        writer.writeheader()
        writer.writerows(rows)

    hosts = len({row['host'] for row in rows})
    log.info(f'{len(rows)} finding(s) on {hosts} host(s)')

if __name__ == '__main__':
    main()
