import os
import argparse

triage = os.environ["TRIAGE_PATH"]

if __name__ == "__main__":
     
    path_to_proc = f'{triage}/live_response/process/proc/'
    os.chdir(path_to_proc)
    pid_list = os.listdir()
   
    # Проверяем существует ли вообще путь до папки (иногда его не бывает)
    if os.path.exists(path_to_proc):
        with open(f'{triage}/proccess_masquerading.txt', 'w') as of:
        
            for pid in pid_list:
                cmdline_path = f'{path_to_proc}/{pid}/cmdline.txt'
                maps_path = f'{path_to_proc}/{pid}/maps.txt'
                if os.path.exists(cmdline_path) and os.path.exists(maps_path):
                    with open(cmdline_path, 'r') as f:
                        cmdline = f.readline()
                    with open(maps_path, 'r') as f:
                        maps = f.readlines()

                    maps_exec_path = maps[0].split()[-1]
                    if cmdline[0] != '/':
                        continue
                    stop_str = cmdline.find(':')
                    if stop_str:
                        cmdline = cmdline[:stop_str]
                    if cmdline != maps_exec_path:
                        of.write(cmdline + '\t' + maps_exec_path + '\t' + pid + '\n')
                else:
                    continue
