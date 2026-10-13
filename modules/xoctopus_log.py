'''
Общий модуль логирования и записи находок для Xoctopus.
Лаунчер добавляет папку modules в PYTHONPATH, поэтому в модулях достаточно:

    import xoctopus_log as log
    log.info('message')
    log.alert('Title', details='...', evidence='/path/to/file')

Строка лога:   [дд.мм.гггг ЧЧ:ММ:СС] [LEVEL] [host] module: message   (время в UTC)
Куда пишется:  консоль, <триаж>/Xoctopus.log, общий лог прогона Xoctopus_run.log
Находки:       <триаж>/Xoctopus_findings.csv
'''
import os
import sys
import csv
import atexit
import datetime
import colorama

TIME_FORMAT = '%d.%m.%Y %H:%M:%S'
FINDINGS_FILE = 'Xoctopus_findings.csv'
FINDINGS_HEADER = ['time', 'host', 'module', 'severity', 'title', 'details', 'evidence_path']

COLORS = {'INFO': '', 'WARN': colorama.Fore.YELLOW, 'ERROR': colorama.Fore.RED, 'ALERT': colorama.Fore.MAGENTA}

# Имя модуля = имя запущенного скрипта
MODULE = os.path.splitext(os.path.basename(sys.argv[0]))[0]
TRIAGE = os.environ.get('TRIAGE_PATH')
HOST = os.environ.get('TRIAGE_NAME', '-')

def format_time(timestamp):
    '''Unix timestamp -> строка в UTC'''
    return datetime.datetime.fromtimestamp(int(timestamp), tz=datetime.timezone.utc).strftime(TIME_FORMAT)

def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime(TIME_FORMAT)

def _append(path, line):
    try:
        with open(path, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except OSError:
        pass  # невозможность записать лог не должна ломать модуль

def log(level, message, host=None, module=None, triage=None):
    host = host or HOST
    module = module or MODULE
    triage = triage if triage is not None else TRIAGE
    line = f'[{now()}] [{level:<5}] [{host}] {module}: {message}'

    if sys.stdout.isatty() and COLORS[level]:
        print(COLORS[level] + line + colorama.Style.RESET_ALL, flush=True)
    else:
        print(line, flush=True)

    if triage:
        _append(os.path.join(triage, 'Xoctopus.log'), line)
    # Читается при каждом вызове: лаунчер задает путь уже после импорта модуля
    run_log = os.environ.get('XOCTOPUS_RUN_LOG')
    if run_log:
        _append(run_log, line)

def info(message, **kwargs):
    log('INFO', message, **kwargs)

def warn(message, **kwargs):
    log('WARN', message, **kwargs)

def error(message, **kwargs):
    log('ERROR', message, **kwargs)

def _findings_path():
    return os.path.join(TRIAGE, FINDINGS_FILE) if TRIAGE else None

def _drop_previous_findings():
    '''При повторном запуске модуля его старые находки удаляются, находки других модулей остаются'''
    path = _findings_path()
    if not path or not os.path.exists(path):
        return
    with open(path, 'r', encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    kept = [row for row in rows if row.get('module') != MODULE]
    if len(kept) == len(rows):
        return
    with open(path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FINDINGS_HEADER)
        writer.writeheader()
        writer.writerows(kept)

_low_count = 0

def _report_low():
    if _low_count:
        info(f'{_low_count} low severity finding(s) written only to {FINDINGS_FILE}')

def alert(title, details='', evidence='', severity='high', time=''):
    '''
    Находка: пишется в лог с уровнем ALERT и в Xoctopus_findings.csv.
    Находки с severity low пишутся только в CSV, в конце выводится их количество.
    time - время события (если известно), evidence - путь к файлу с подробностями.
    '''
    global _low_count
    if severity == 'low':
        if _low_count == 0:
            atexit.register(_report_low)
        _low_count += 1
    else:
        log('ALERT', f'{title}: {details}' if details else title)
    path = _findings_path()
    if not path:
        return
    new_file = not os.path.exists(path)
    with open(path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(FINDINGS_HEADER)
        writer.writerow([time, HOST, MODULE, severity, title, details, evidence])

if TRIAGE and MODULE:
    _drop_previous_findings()
