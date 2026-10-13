import os
import sys
import xoctopus_log as log

triage = os.environ["TRIAGE_PATH"]

if __name__ == "__main__":
    
    path_to_proc = f'{triage}/live_response/process/proc/'
    if os.path.exists(path_to_proc):
        os.chdir(path_to_proc)
        pid_list = os.listdir()
    
        # Проверяем существует ли вообще путь до папки (иногда его не бывает)
        if os.path.exists(path_to_proc):
            res_path = f'{triage}/Xoctopus_proccess_masquerading.txt'
            with open(res_path, 'w') as of:
                of.write('CMDLINE\tEXE(maps)\tPID\n')
                for pid in pid_list:
                    cmdline_path = f'{path_to_proc}/{pid}/cmdline.txt'
                    maps_path = f'{path_to_proc}/{pid}/maps.txt'
                    if os.path.exists(cmdline_path) and os.path.exists(maps_path):
                        with open(cmdline_path, 'r') as f:
                            cmdline = f.readline()
                        with open(maps_path, 'r') as f:
                            maps = f.readlines()

                        if not maps or not maps[0].split() or not cmdline:
                            continue
                        maps_exec_path = maps[0].split()[-1]
                        if cmdline[0] != '/':
                            continue
                        stop_str = cmdline.find(':')
                        if stop_str != -1:
                            cmdline = cmdline[:stop_str]
                        if cmdline != maps_exec_path:
                            of.write(cmdline + '\t' + maps_exec_path + '\t' + pid + '\n')
                            log.alert('Process masquerading', details=f'pid {pid}: cmdline {cmdline}, exe {maps_exec_path}',
                                      evidence=res_path)
                    else:
                        continue
        log.info('done')
    else:
        log.warn(f'path does not exist: {path_to_proc}')
        sys.exit(0)
