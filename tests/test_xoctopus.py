import os
import sys
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
        f.write('0|/tmp/x|1|-rwxr-xr-x|0|0|10|1700000000|1700000000|1700000100|1700000000\n')
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
    assert len(row) == 11 and '.2023 ' in row[7]

    with open(triage / 'Xoctopus_all_dot_bash_history') as f:
        assert f.read().splitlines() == ['1|id', '2|ls']

    with open(triage / 'Xoctopus_proccess_masquerading.txt') as f:
        assert '/usr/bin/real\t/usr/bin/fake\t42' in f.read()

    # Сводные файлы пишутся в родительскую папку триажей
    with open(tmp_path / 'super_Xoctopus_bodyfile') as f:
        assert f.readline().rstrip('\n').endswith('|host1')


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
    assert 'parsers/lin/bodytime' in res.stdout
    # Следующие парсеры отработали
    assert (triage / 'Xoctopus_all_dot_bash_history').exists()
