import os
import re
import csv
import glob
import sys
import xoctopus_log as log

triage = os.environ["TRIAGE_PATH"]

'''
Следы запуска программ из Amcache (вывод AmcacheParser) и PCA (Program Compatibility Assistant, Windows 11 22H2+)
проверяются по именам известных инструментов и по подозрительным путям.
[категория, severity, регулярка по имени файла]
'''
TOOL_RULES = [
    ['attacker tool', 'high', re.compile(
        r'mimikatz|mimilib|\bmimi(32|64)?\.exe|psexe(c|svc)|paexec|procdump|nanodump|pwdump|gsecdump|wce(32|64)?\.exe|lazagne|'
        r'rubeus|sharphound|bloodhound|adfind|secretsdump|crackmapexec|\bnxc\.exe|impacket|kerbrute|'
        r'rclone|\bngrok|plink|chisel|\bfrpc?\.exe|\bnc(at|64)?\.exe|socat|'
        r'advanced_ip_scanner|advanced ip scanner|netscan|\bnmap|masscan|ipscan|softperfect|'
        r'megasync|megacmd|cobaltstrike|\bbeacon\.exe|sliver|meterpreter', re.I)],
    ['remote access tool', 'medium', re.compile(
        r'anydesk|teamviewer|rustdesk|ammyy|aeroadmin|litemanager|radmin|screenconnect|splashtop|'
        r'rutserv|rfusclient|remote ?utilities|supremo|\bdwagent|tightvnc|ultravnc|\bvncviewer', re.I)],
    ['activator / crack', 'medium', re.compile(
        r'kmsauto|kmspico|kms[ _-]?(vl|tools|activator|cleaner|matrix)|\bkms\.(exe|cmd)|activator|\baact|'
        r'\bmas(_aio)?\.(exe|cmd)|keygen|\bcrack|\bpatch(er)?\.exe|kpojiuk', re.I)],
]
# [описание, severity, регулярка по полному пути]
PATH_RULES = [
    ['run from Users\\Public / PerfLogs / Recycle Bin', 'high', re.compile(r'^[a-z]:\\(users\\public|perflogs|\$recycle\.bin)\\', re.I)],
    ['run from ProgramData or AppData\\Roaming root', 'medium', re.compile(r'^[a-z]:\\(programdata|users\\[^\\]+\\appdata\\roaming)\\[^\\]+$', re.I)],
    ['run from Windows\\Temp', 'medium', re.compile(r'^[a-z]:\\windows\\temp\\', re.I)],
    ['run from user Temp', 'low', re.compile(r'^[a-z]:\\users\\[^\\]+\\appdata\\local\\temp\\', re.I)],
    ['run from removable / non-system drive', 'low', re.compile(r'^[d-z]:\\', re.I)],
]

ENV_VARS = {'%programfiles%': 'C:\\Program Files', '%programfiles(x86)%': 'C:\\Program Files (x86)',
            '%windir%': 'C:\\Windows', '%systemroot%': 'C:\\Windows', '%programdata%': 'C:\\ProgramData'}

def expand(path):
    for var, value in ENV_VARS.items():
        if path.lower().startswith(var):
            return value + path[len(var):]
    return path

def read_text(path):
    '''PCA-файлы бывают в UTF-8 и UTF-16'''
    with open(path, 'rb') as f:
        data = f.read()
    encoding = 'utf-16' if data[:2] in (b'\xff\xfe', b'\xfe\xff') or data[1:2] == b'\x00' else 'utf-8-sig'
    return data.decode(encoding, errors='ignore').splitlines()

def collect():
    '''{путь в нижнем регистре: {'path', 'time', 'sources'}}, time - самое раннее известное время'''
    entries = {}

    def add(path, time, source):
        path = expand(path.strip())
        if not path:
            return
        entry = entries.setdefault(path.lower(), {'path': path, 'time': time, 'sources': set()})
        entry['sources'].add(source)
        if time and (not entry['time'] or time < entry['time']):
            entry['time'] = time

    for amcache in glob.glob(f'{triage}/Amcache_*FileEntries.csv'):
        with open(amcache, 'r', encoding='utf-8-sig', newline='') as f:
            for row in csv.DictReader(f):
                add(row.get('FullPath', ''), row.get('FileKeyLastWriteTimestamp', '')[:19], 'Amcache')

    for pca_dir in glob.glob(f'{triage}/[A-Z]/Windows/appcompat/pca'):
        launch_dic = f'{pca_dir}/PcaAppLaunchDic.txt'
        if os.path.exists(launch_dic):
            for line in read_text(launch_dic):
                path, _, time = line.partition('|')
                add(path, time[:19], 'PcaAppLaunchDic')
        for general_db in glob.glob(f'{pca_dir}/PcaGeneralDb*.txt'):
            for line in read_text(general_db):
                fields = line.split('|')
                if len(fields) >= 3:
                    add(fields[2], fields[0][:19], 'PcaGeneralDb')
    return entries

def match(path):
    '''Самое серьезное из сработавших правил: (severity, причина) или None'''
    order = {'high': 0, 'medium': 1, 'low': 2}
    hits = []
    name = path.replace('/', '\\').split('\\')[-1]
    for category, severity, regex in TOOL_RULES:
        if regex.search(name) or (category == 'activator / crack' and regex.search(path)):
            hits.append((severity, f'{category}: {name}'))
    for reason, severity, regex in PATH_RULES:
        if regex.search(path):
            hits.append((severity, reason))
    return min(hits, key=lambda hit: order[hit[0]]) if hits else None

def main():
    entries = collect()
    if not entries:
        log.warn('no Amcache CSV (run zimmerman_extractor first) and no PCA files found')
        sys.exit(0)

    res_path = f'{triage}/Xoctopus_suspicious_exec.csv'
    with open(res_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'severity', 'reason', 'path', 'sources'])
        for entry in sorted(entries.values(), key=lambda e: e['time']):
            hit = match(entry['path'])
            if not hit:
                continue
            severity, reason = hit
            sources = ', '.join(sorted(entry['sources']))
            writer.writerow([entry['time'], severity, reason, entry['path'], sources])
            log.alert(f'Suspicious execution ({reason})', details=f"{entry['path']} [{sources}]",
                      evidence=res_path, severity=severity, time=entry['time'])
    log.info(f'done, {len(entries)} executed file(s) checked')

if __name__ == '__main__':
    main()
