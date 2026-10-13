import os
import sys
import subprocess
import xoctopus_log as log

triage = os.environ["TRIAGE_PATH"]
zmpath = os.environ.get("ZIMMERMAN_TOOLS_PATH", "")

'''
[рабочая директория относительно диска, обязательный входной файл, аргументы утилиты]
Пути вывода относительные: утилиты Zimmerman - Windows-программы и не понимают linux-пути (/mnt/c/...).
Результаты сохраняются в корень триажа.
'''
def commands(disk):
    return [['', '$Extend/$J', ['MFTECmd.exe', '-f', '$Extend/$J', '-m', '$MFT', '--csv', '../', '--csvf', f'J_and_MFT_{disk}.csv']],
            ['Windows/AppCompat/Programs/', 'Amcache.hve', ['AmcacheParser.exe', '-f', 'Amcache.hve', '--csv', '../../../../', '--csvf', f'Amcache_{disk}.csv']],
            ['', '$MFT', ['MFTECmd.exe', '-f', '$MFT', '--csv', '../', '--csvf', f'MFT_{disk}.csv']],  # MFT if $J is not work
            ['Windows/System32/LogFiles/SUM', '.', ['SumECmd.exe', '-d', '.', '--csv', f'../../../../../Sum_{disk}']],
            ]

disks = ['C', 'D', 'E', 'F']
def main():
    if not os.path.isdir(zmpath):
        log.warn(f'Zimmerman tools not found: "{zmpath}". Use -z or env ZIMMERMAN_TOOLS_PATH')
        sys.exit(0)

    failed = []
    # Необходимо для работы триажей с несколькими дисками
    for disk in disks:
        if not os.path.exists(f'{triage}/{disk}'):
            continue
        for workdir, required, args in commands(disk):
            # По умолчанию меняет директорию на текущий диск
            cwd = f'{triage}/{disk}/{workdir}'
            if not os.path.exists(f'{cwd}/{required}'):
                continue
            exe = os.path.join(zmpath, args[0])
            if not os.path.exists(exe):
                failed.append(f'{args[0]} not found')
                continue
            proc = subprocess.run([exe, *args[1:]], cwd=cwd, stdout=subprocess.DEVNULL)
            if proc.returncode != 0:
                failed.append(f'{args[0]} ({disk}): exit code {proc.returncode}')

    if failed:
        for message in failed:
            log.error(message)
        sys.exit(1)
    log.info('done')

if __name__ == '__main__':
    main()
