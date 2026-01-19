import csv
import sys
import os
import colorama
from collections import defaultdict
from datetime import datetime

triage = os.environ["TRIAGE_PATH"]
bodyfile_path = f'{triage}/Xoctopus_bodyfile_convert.txt'

def parse_datetime(dt_str):
    return datetime.strptime(dt_str, "%d.%m.%Y %H:%M:%S")

def main():
    files_by_dir = defaultdict(list) 

    with open(bodyfile_path, 'r') as f:
        reader = csv.reader(f, delimiter='|')
        for row in reader:
            if len(row) < 10:
                continue  # пропустить некорректные строки
            # Проверяем, что это файл, а не каталог
            if not row[3].startswith('-'):
                continue
            if not (row[3][3] == 'x' or row[3][6] == 'x' or row[3][9] == 'x'):
                continue
            path = row[1]
            try:
                mtime = parse_datetime(row[8])
                ctime = parse_datetime(row[9])
            except Exception:
                continue  # пропустить строки с некорректными датами
            directory = '/'.join(path.split('/')[:-1])
            files_by_dir[directory].append({'path': path, 'mtime': mtime, 'ctime': ctime})

        
    result_paths = []

    # Фильтрация по условиям таймстомпинга
    for directory, files in files_by_dir.items():
        if not files:
            continue
        min_mtime = min(file['mtime'] for file in files)
        for file in files:
            if file['mtime'] == min_mtime and \
                file['ctime'] > file['mtime']:
                result_paths.append(file['path'])

    # with open('Xoctopus_gsocket_finder', 'w') as f:
    #     f.writeline('Предполагаемые пути:')
    #     f.writelines(result_paths)
        
    pids = defaultdict(list)

    # Поиск таких файлов, которые запущены в процессах
    with open(f'{triage}/live_response/process/running_processes_full_paths.txt', 'r') as f:
        proc_full_paths = f.readlines()

    for path in result_paths:
        for full_path_str in proc_full_paths:
        # Поскольку gsocket использует маскардинг имени исполняемого файла процесса, 
        # то в процессах он вероятно будет показан как deleted.
            if path in full_path_str and 'deleted' in full_path_str:
                proc_index = full_path_str.index('proc')
                # Выделяем PID по найденным исполняемым файлам.
                pid = full_path_str[proc_index + 5:full_path_str.index('->') - 5:] 
                pids[pid] = path
   
    # Проверка активных подключений
    current_connection = defaultdict(list)

    with open(f'{triage}/live_response/process/lsof_-nPl.txt', 'r') as f:
        connections = [x for x in f.readlines() if 'TCP' in x ]

    for pid in pids.keys():
        for connect in connections:
            if pid in connect:
                current_connection[pid] = connect[connect.index('TCP')::]
    
    print(current_connection)
    # Анализируем новые подключения от gsocket
    with open(f'{triage}/Xoctopus_gsocket_finder_res.txt', 'w') as f:
        if pids is not None:
            f.writelines([f'PID\tPATH\t\tCONNECT(FROM->TO)\n'])
            for pid in pids.keys():
                row = f'{pid}\t{pids[pid]}\t'
                if current_connection is not None:
                    if pid in current_connection.keys():
                        row += f'{current_connection[pid][:-1]}'
                    else:
                        row += f'NO CURRENT CONNECTION'
                f.writelines([f'{row}\n'])

        elif result_paths is not None:
            f.writelines(['Подозрительные имена файлов'])
            f.writelines(result_paths)

if __name__ == '__main__':
    main()

    
