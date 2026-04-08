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
command_data = [['C/', 'MFTECmd.exe', '\\$Extend/\\$J" -m "\\$MFT', '../', 'MFT.csv'], #$J and $MFT
                ['C/Windows/AppCompat/Programs/', 'AmcacheParser.exe', 'Amcache.hve', '../../../../', 'Amcache_csv.csv'], #Amcahce
                ['C/', 'MFTECmd.exe', '\\$MFT', '../', 'MFT.csv'] #MFT if $J is not work
                ]

custom_command = [[f'C/Windows/System32/LogFiles/SUM', f'{zmpath}/SumECmd.exe -d "." --csv ../../../../../Sum.csv > /dev/null']]
def main():

    for data in command_data:
        # Работа с MFT
        os.chdir(f'{triage}/{data[0]}')
        cmd = f'{zmpath}/{data[1]} -f "{data[2]} " --csv "{data[3]}" --csvf "{data[4]}" > /dev/null'
        print(cmd)
        os.system(cmd)

    for cmd in custom_command:
        print(cmd)
        os.chdir(f'{triage}/{cmd[0]}')
        os.system(cmd[1])

if __name__ == '__main__':
    main()
