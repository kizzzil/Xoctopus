import os
import sys
import csv
import subprocess

BASE_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
XOCTOPUS = os.path.join(BASE_DIR, 'Xoctopus.py')


def run(*args, env=None):
    return subprocess.run([sys.executable, XOCTOPUS, *args], capture_output=True, text=True,
                          env={**os.environ, **(env or {})})


def make_lin_triage(path):
    '''Минимальный UAC-триаж: bodyfile, история bash, процесс и btmp/wtmp в виде готового вывода last'''
    os.makedirs(f'{path}/[root]/home/bob')
    os.makedirs(f'{path}/[root]/root')
    os.makedirs(f'{path}/bodyfile')
    os.makedirs(f'{path}/live_response/process/proc/42')
    with open(f'{path}/bodyfile/bodyfile.txt', 'w') as f:
        f.write('0|/tmp/x|1|-rwxr-xr-x|0|0|10|1700000000|1700000000|1700000000|1700000000\n')
    with open(f'{path}/[root]/home/bob/.bash_history', 'w') as f:
        f.write('ls\nls\nid\n')
    with open(f'{path}/live_response/process/proc/42/cmdline.txt', 'w') as f:
        f.write('/usr/bin/real')
    with open(f'{path}/live_response/process/proc/42/maps.txt', 'w') as f:
        f.write('0000 r-xp 0 0 0 /usr/bin/fake\n')


def test_help_lists_modules():
    res = run('--help')
    assert res.returncode == 0
    assert 'parsers/lin/bodytime' in res.stdout


def test_unknown_plugin_rejected(tmp_path):
    res = run('-m', str(tmp_path), '-p', 'parsers/lin/nope')
    assert res.returncode != 0
    assert 'not found' in res.stderr


def test_full_run(tmp_path):
    triage = tmp_path / 'host1'
    make_lin_triage(str(triage))

    res = run('-m', str(tmp_path), '-a')
    print(res.stdout, res.stderr)

    with open(triage / 'Xoctopus_bodyfile_convert.txt') as f:
        row = f.readline().rstrip('\n').split('|')
    # Время в UTC независимо от часового пояса машины
    assert row[7] == '14.11.2023 22:13:20'

    with open(triage / 'Xoctopus_all_dot_bash_history') as f:
        assert f.read().splitlines() == ['1|id', '2|ls']

    with open(triage / 'Xoctopus_proccess_masquerading.txt') as f:
        assert '/usr/bin/real\t/usr/bin/fake\t42' in f.read()

    # Сводные файлы пишутся в родительскую папку триажей
    with open(tmp_path / 'super_Xoctopus_bodyfile') as f:
        assert f.readline().rstrip('\n').endswith('|host1')

    # Находки анализаторов в едином CSV и в сводке по всем хостам
    with open(tmp_path / 'super_Xoctopus_findings.csv', newline='') as f:
        findings = list(csv.DictReader(f))
    assert [(r['host'], r['module'], r['title']) for r in findings] == \
        [('host1', 'process-masquerading', 'Process masquerading')]

    # Логи: по триажу и общий лог прогона
    with open(triage / 'Xoctopus.log') as f:
        assert '[ALERT] [host1] process-masquerading: Process masquerading' in f.read()
    with open(tmp_path / 'Xoctopus_run.log') as f:
        run_log = f.read()
    assert 'run finished: 0 failed module(s)' in run_log
    assert 'findings_sum: 1 finding(s) on 1 host(s)' in run_log


def test_rerun_does_not_duplicate_findings(tmp_path):
    triage = tmp_path / 'host1'
    make_lin_triage(str(triage))
    for _ in range(2):
        run('-m', str(tmp_path), '-a')
    with open(triage / 'Xoctopus_findings.csv', newline='') as f:
        assert len(list(csv.DictReader(f))) == 1


def test_correlate_btmp_wtmp(tmp_path):
    triage = tmp_path / 'host1'
    make_lin_triage(str(triage))
    with open(triage / 'Xoctopus_btmp', 'w') as f:
        f.writelines(['root ssh:notty 1.2.3.4 Mon Oct 1\n'] * 12 + ['\n', 'btmp begins Mon Oct 1\n'])
    with open(triage / 'Xoctopus_wtmp', 'w') as f:
        f.write('root pts/0 1.2.3.4 a\nroot pts/1 1.2.3.4 b\nbob pts/2 1.2.3.45 c\n')

    res = run('-m', str(tmp_path), '-p', 'analyzators/lin/correlate_btmp_wtmp')
    assert res.returncode == 0, res.stdout + res.stderr

    with open(triage / 'Xoctopus_correlate_btmp_wtmp') as f:
        assert f.read() == ('Successful bruteforce login from 1.2.3.4 (12 failed attempts)\n'
                            'root pts/0 1.2.3.4 a\nroot pts/1 1.2.3.4 b\n')


def test_failed_module_does_not_stop_run(tmp_path):
    triage = tmp_path / 'host1'
    make_lin_triage(str(triage))
    # Битый bodyfile: не число вместо метки времени
    with open(triage / 'bodyfile' / 'bodyfile.txt', 'w') as f:
        f.write('0|/tmp/x|1|-rwxr-xr-x|0|0|10|abc|1|1|1\n')

    res = run('-m', str(tmp_path))
    assert res.returncode == 1
    assert 'FAILED parsers/lin/bodytime [host1]' in res.stdout
    # Следующие парсеры отработали
    assert (triage / 'Xoctopus_all_dot_bash_history').exists()


MFT_HEADER = ['EntryNumber', 'InUse', 'ParentPath', 'FileName', 'Extension', 'FileSize', 'IsDirectory', 'IsAds',
              'SI<FN', 'uSecZeros', 'Created0x10', 'Created0x30', 'LastModified0x10', 'LastModified0x30']


def mft_row(parent, name, si_created, fn_created, si_fn='True', zeros='False'):
    return [1, 'True', parent, name, os.path.splitext(name)[1], 100, 'False', 'False',
            si_fn, zeros, si_created, fn_created, si_created, fn_created]


def make_win_triage(path):
    '''Минимальный KAPE-триаж с готовым выводом утилит Zimmerman'''
    os.makedirs(f'{path}/C/Windows/appcompat/pca')
    os.makedirs(f'{path}/C/Windows/System32/Tasks/Microsoft')
    os.makedirs(f'{path}/live_responce/Persistence')
    open(f'{path}/C/$MFT', 'w').close()

    rows = [
        # Файлы образа Windows: SI = дата сборки образа
        *[mft_row('.\\Windows\\System32', f'os{i}.dll', '2024-04-01 07:22:00.0000000', '2025-11-18 09:43:13.0000000') for i in range(3)],
        mft_row('.\\ProgramData\\Microsoft\\UEV\\Scripts', 'builtin.ps1', '2024-04-01 07:22:50.0000000', '2025-11-18 09:48:22.0000000'),
        # Подмена времени: SI раньше FN, микросекунды обнулены
        mft_row('.\\Users\\bob\\AppData\\Roaming', 'evil.exe', '2019-01-01 00:00:00.0000000', '2026-09-01 10:00:00.1234567', zeros='True'),
        # Массовая установка: много файлов в одну минуту
        *[mft_row('.\\Users\\bob\\AppData\\Local\\Programs\\app', f'f{i}.dll', '2026-01-01 00:00:00.0000000', '2026-09-02 11:00:00.0000000') for i in range(25)],
        # Обычный файл
        mft_row('.\\Users\\bob\\AppData\\Roaming', 'good.exe', '2026-09-01 10:00:00.0000000', '2026-09-01 10:00:00.0000000', si_fn='False'),
    ]
    with open(f'{path}/MFT_C.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(MFT_HEADER)
        writer.writerows(rows)

    with open(f'{path}/Amcache_C_UnassociatedFileEntries.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['FileKeyLastWriteTimestamp', 'FullPath'])
        writer.writerow(['2026-09-01 10:00:00', 'c:\\users\\bob\\downloads\\mimikatz_trunk\\x64\\mimikatz.exe'])
        writer.writerow(['2026-09-01 10:00:00', 'c:\\program files\\kyocera\\kmsfx.exe'])
        writer.writerow(['2026-09-01 10:00:00', 'c:\\windows\\system32\\notepad.exe'])
    with open(f'{path}/C/Windows/appcompat/pca/PcaAppLaunchDic.txt', 'w', encoding='utf-8') as f:
        f.write('C:\\Users\\Public\\x.exe|2026-09-02 12:00:00.000\r\n')
    with open(f'{path}/C/Windows/appcompat/pca/PcaGeneralDb0.txt', 'w', encoding='utf-16') as f:
        f.write('2026-09-03 12:00:00.000|2|%programfiles%\\AnyDesk\\AnyDesk.exe|anydesk|philandro|8.0|000|0\r\n')

    task = '''<?xml version="1.0" encoding="UTF-16"?>
<Task xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo><Date>2026-09-01T10:00:00</Date><Author>{author}</Author><URI>\\{name}</URI></RegistrationInfo>
  <Principals><Principal><UserId>S-1-5-18</UserId></Principal></Principals>
  <Actions><Exec><Command>{command}</Command><Arguments>{args}</Arguments></Exec></Actions>
</Task>'''
    for name, command, args in [('Updater', 'powershell.exe', '-w hidden -enc SQBFAFgA'),
                                ('Microsoft\\Benign', 'C:\\Program Files\\App\\app.exe', '/update')]:
        with open(f'{path}/C/Windows/System32/Tasks/{name}', 'w', encoding='utf-16') as f:
            f.write(task.format(author='x', name=name, command=command, args=args))

    with open(f'{path}/live_responce/Persistence/Autoruns.csv', 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Time', 'Entry Location', 'Entry', 'Enabled', 'Category', 'Profile', 'Description', 'Signer',
                         'Company', 'Image Path', 'Version', 'Launch String'])
        writer.writerow(['', 'HKCU\\...\\Run', 'upd', 'enabled', 'Logon', 'bob', '', '(Not verified) ', '',
                         'c:\\users\\bob\\appdata\\roaming\\upd.exe', '', 'C:\\Users\\bob\\AppData\\Roaming\\upd.exe'])
        writer.writerow(['', 'HKLM\\...\\Run', 'ok', 'enabled', 'Logon', 'System-wide', '', '(Verified) Microsoft Windows', '',
                         'c:\\windows\\system32\\ok.exe', '', 'C:\\Windows\\System32\\ok.exe'])


def win_findings(tmp_path, module):
    triage = tmp_path / 'win1'
    make_win_triage(str(triage))
    res = run('-m', str(tmp_path), '-p', f'analyzators/win/{module}')
    assert res.returncode == 0, res.stdout + res.stderr
    with open(triage / 'Xoctopus_findings.csv', newline='') as f:
        return list(csv.DictReader(f))


def test_mft_timestomping(tmp_path):
    findings = win_findings(tmp_path, 'mft_timestomping')
    # Только evil.exe: файлы образа ОС и массовая установка отфильтрованы
    assert len(findings) == 1
    assert findings[0]['severity'] == 'high'
    assert findings[0]['details'].startswith('C:\\Users\\bob\\AppData\\Roaming\\evil.exe: SI 2019-01-01 00:00:00')


def test_suspicious_exec(tmp_path):
    findings = win_findings(tmp_path, 'suspicious_exec')
    got = {(r['severity'], r['title']) for r in findings}
    assert got == {('high', 'Suspicious execution (attacker tool: mimikatz.exe)'),
                   ('high', 'Suspicious execution (run from Users\\Public / PerfLogs / Recycle Bin)'),
                   ('medium', 'Suspicious execution (remote access tool: AnyDesk.exe)')}


def test_persistence(tmp_path):
    findings = win_findings(tmp_path, 'persistence')
    got = {(r['severity'], r['details'].split(':')[0]) for r in findings}
    assert got == {('high', '\\Updater'), ('medium', 'HKCU\\...\\Run\\upd')}


def test_low_severity_only_in_csv(tmp_path):
    triage = tmp_path / 'win1'
    make_win_triage(str(triage))
    with open(triage / 'C/Windows/appcompat/pca/PcaAppLaunchDic.txt', 'a', encoding='utf-8') as f:
        f.write('E:\\setup.exe|2026-09-04 12:00:00.000\r\n')
    res = run('-m', str(tmp_path), '-p', 'analyzators/win/suspicious_exec')
    assert 'E:\\setup.exe' not in res.stdout
    assert '1 low severity finding(s) written only to Xoctopus_findings.csv' in res.stdout
    with open(triage / 'Xoctopus.log') as f:
        assert 'E:\\setup.exe' not in f.read()
    with open(triage / 'Xoctopus_findings.csv', newline='') as f:
        assert [r['severity'] for r in csv.DictReader(f) if 'E:\\setup.exe' in r['details']] == ['low']
