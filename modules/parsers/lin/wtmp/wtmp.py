import datetime
import sys
import os
import colorama
import subprocess

triage = os.environ["TRIAGE_PATH"]
files = {'wtmp' : ['wtmp', 'wtmp.1'], 'btmp' : ['btmp', 'btmp.1'], 'utmp' : ['utmp', 'utmp.1']}

def main():
    for category in files.keys():
        res = ""
        for file in files[category]:
            path = f'{triage}/[root]/var/log/{file}'
            if not os.path.exists(path):
                continue
            proc = subprocess.run(['last', '-f', path, '-F'], capture_output=True, text=True, check=True)
            res += proc.stdout
        with open(f'{triage}/Xoctopus_{category}', 'w') as f:
            f.write(res)

if __name__ == '__main__':
    main()
