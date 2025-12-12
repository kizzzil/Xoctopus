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
command_data = [['Target/C/', 'MFTECmd.exe', '\\$Extend/\\$J" -m "\\$MFT', '../../', 'MFT.csv'], #$J and $MFT
                ['Target/C/Windows/AppCompat/Programs/', 'AmcacheParser.exe', 'Amcache.hve', '../../../../../', 'Amcache_csv.csv'], #Amcahce
                ['Target/C/', 'MFTECmd.exe', '\\$MFT', '../../', 'MFT.csv'] #MFT if $J is not work
                ]

def main():

    for data in command_data:
        # Работа с MFT
        os.chdir(f'{triage}/{data[0]}')
        cmd = f'{zmpath}/{data[1]} -f "{data[2]} " --csv "{data[3]}" --csvf "{data[4]}" > /dev/null'
        # print(cmd)
        os.system(cmd)

if __name__ == '__main__':
    main()
