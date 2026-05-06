import datetime
import sys
import os
import colorama
from collections import Counter

triage = os.environ["TRIAGE_PATH"]
zmpath = os.environ["ZIMMERMAN_TOOLS_PATH"] 

'''
['path_to_cd', 'exename', 'filename', 'save_dir_path']
'''
command_data = [['', 'MFTECmd.exe', '\\$Extend/\\$J" -m "\\$MFT', '../', 'J_and_MFT'], #$J and $MFT
                ['Windows/AppCompat/Programs/', 'AmcacheParser.exe', 'Amcache.hve', '../../../../', 'Amcache_csv.csv'], #Amcahce
                ['', 'MFTECmd.exe', '\\$MFT', '../', 'MFT'] #MFT if $J is not work
                ]

custom_command = [[f'Windows/System32/LogFiles/SUM', f'{zmpath}/SumECmd.exe -d "." --csv ../../../../../Sum.csv > /dev/null']]

disks = ['C', 'D', 'E', 'F']
def main():
    # Необходимо для работы триажей с несколькими дисками
    for disk in disks:
        if not os.path.exists(f'{triage}/{disk}'):
            continue
        else:
            for data in command_data:
                # По умолчанию меняет директорию на текущий диск
                if os.path.exists(f'{triage}/{disk}/{data[0]}'):
                    os.chdir(f'{triage}/{disk}/{data[0]}')
                else:
                    continue
                cmd = f'{zmpath}/{data[1]} -f "{data[2]} " --csv "{data[3]}" --csvf "{data[4]}_{disk}.csv" > /dev/null'
                os.system(cmd)

            for cmd in custom_command:
                if os.path.exists(f'{triage}/{disk}/{cmd[0]}'):
                    os.chdir(f'{triage}/{disk}/{cmd[0]}')
                else:
                    continue
                os.system(cmd[1])

if __name__ == '__main__':
    main()
