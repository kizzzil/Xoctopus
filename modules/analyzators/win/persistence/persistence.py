import os
import re
import csv
import glob
import xml.etree.ElementTree as ET
import xoctopus_log as log

triage = os.environ["TRIAGE_PATH"]

'''
Проверка точек закрепления:
  - задачи планировщика: XML из <диск>/Windows/System32/Tasks (не зависят от языка системы)
  - автозапуск из Autoruns (live_responce/Persistence/Autoruns.csv), кроме задач - они уже проверены по XML
[описание, severity, регулярка по командной строке]
'''
COMMAND_RULES = [
    ['PowerShell with encoded/download/hidden command', 'high', re.compile(
        r'(powershell|pwsh).*(\s-e(nc|ncodedcommand)?\s|frombase64|downloadstring|downloadfile|\biex\b|invoke-expression|'
        r'invoke-webrequest|\biwr\b|net\.webclient|-w(indowstyle)?\s+h(idden)?|bypass)', re.I)],
    ['LOLBin execution (mshta/regsvr32/certutil/bitsadmin)', 'high', re.compile(
        r'mshta|regsvr32.*(/i:|scrobj)|certutil.*(urlcache|decode)|bitsadmin.*transfer', re.I)],
    ['rundll32 with script or non-system DLL', 'high', re.compile(
        r'rundll32.*(javascript:|\\users\\|\\programdata\\|\\temp\\|\\public\\)', re.I)],
    ['URL in command line', 'medium', re.compile(r'https?://', re.I)],
    ['script host / script file', 'medium', re.compile(r'wscript|cscript|\.(cmd|bat|ps1|vbs|vbe|js|jse|wsf|hta)\b', re.I)],
    ['activator (KMS)', 'medium', re.compile(r'kmsauto|kmspico|k-?m-?s\b|activation-renewal|\baact\b', re.I)],
]
USER_WRITABLE = re.compile(r'\\(users|programdata|windows\\temp|perflogs|\$recycle\.bin)\\', re.I)
# Каталоги ПО, которое штатно ставит неподписанные компоненты в ProgramData
TRUSTED_DIRS = re.compile(r'\\programdata\\kaspersky lab\\', re.I)
# Штатные задачи Windows, срабатывающие на правила
KNOWN_GOOD = re.compile(r'^%systemroot%\\system32\\cmd\.exe /d /c %systemroot%\\system32\\hpatchmontask\.cmd$', re.I)

NS = {'t': 'http://schemas.microsoft.com/windows/2004/02/mit/task'}

def check(command, image='', signed=None):
    '''Список (severity, причина) для командной строки и исполняемого файла'''
    hits = [(severity, reason) for reason, severity, regex in COMMAND_RULES if regex.search(command)]
    image = image or command
    if signed is False and USER_WRITABLE.search(image) and not TRUSTED_DIRS.search(image):
        hits.append(('medium', 'unsigned binary in user-writable directory'))
    return hits

def read_tasks():
    tasks = []
    for tasks_dir in glob.glob(f'{triage}/[A-Z]/Windows/System32/Tasks'):
        for root, _, files in os.walk(tasks_dir):
            for name in files:
                path = os.path.join(root, name)
                try:
                    task = ET.parse(path).getroot()
                except ET.ParseError:
                    continue
                text = lambda xpath: (task.findtext(xpath, default='', namespaces=NS) or '').strip()
                commands = [f"{(e.findtext('t:Command', '', NS) or '').strip()} {(e.findtext('t:Arguments', '', NS) or '').strip()}".strip()
                            for e in task.findall('.//t:Actions/t:Exec', NS)]
                for command in commands:
                    tasks.append({'source': 'task',
                                  'name': text('t:RegistrationInfo/t:URI') or os.path.relpath(path, tasks_dir),
                                  'command': command,
                                  # Описание и автор задачи тоже проверяются: активаторы подписываются явно
                                  'context': f"{command} {text('t:RegistrationInfo/t:Description')} {text('t:RegistrationInfo/t:Author')}",
                                  'image': command, 'signed': None,
                                  'author': text('t:RegistrationInfo/t:Author'),
                                  'run_as': text('t:Principals/t:Principal/t:UserId'),
                                  'time': text('t:RegistrationInfo/t:Date')[:19].replace('T', ' '),
                                  'evidence': path})
    return tasks

def read_autoruns():
    entries = []
    for path in glob.glob(f'{triage}/live_responce/Persistence/Autoruns.csv') + glob.glob(f'{triage}/live_response/Persistence/Autoruns.csv'):
        with open(path, 'r', encoding='utf-8-sig', errors='ignore', newline='') as f:
            for row in csv.DictReader(f):
                if row.get('Category') == 'Tasks' or not row.get('Image Path') or row['Image Path'].startswith('File not found'):
                    continue
                entries.append({'source': f"autoruns/{row['Category']}",
                                'name': f"{row['Entry Location']}\\{row['Entry']}",
                                'command': row['Launch String'],
                                'context': row['Launch String'],
                                'image': row['Image Path'],
                                'signed': row['Signer'].lower().startswith('(verified)'),
                                'author': row['Signer'] or row['Company'],
                                'run_as': row.get('Profile', ''),
                                'time': row.get('Time', ''),
                                'evidence': path})
    return entries

def main():
    entries = read_tasks() + read_autoruns()
    if not entries:
        log.warn('no scheduled task XML and no Autoruns.csv found')
        return

    order = {'high': 0, 'medium': 1, 'low': 2}
    res_path = f'{triage}/Xoctopus_persistence.csv'
    with open(res_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['time', 'severity', 'reasons', 'source', 'name', 'command', 'author_or_signer', 'run_as', 'evidence_path'])
        for e in entries:
            hits = [] if KNOWN_GOOD.search(e['command'].strip()) else check(e['context'], e['image'], e['signed'])
            if not hits:
                continue
            severity = min((h[0] for h in hits), key=order.get)
            reasons = '; '.join(sorted({h[1] for h in hits}))
            writer.writerow([e['time'], severity, reasons, e['source'], e['name'], e['command'], e['author'], e['run_as'], e['evidence']])
            log.alert(f"Suspicious persistence ({e['source']})", details=f"{e['name']}: {e['command']} [{reasons}]",
                      evidence=e['evidence'], severity=severity, time=e['time'])
    log.info(f'done, {len(entries)} autostart entries checked')

if __name__ == '__main__':
    main()
