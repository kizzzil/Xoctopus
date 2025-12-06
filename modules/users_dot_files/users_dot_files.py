import datetime
import sys
import os
import colorama
from collections import Counter

triage = os.environ["TRIAGE_PATH"]

def ssort_filename(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    
    # Читаем и обрабатываем
    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
        lines = [line.rstrip('\n') for line in f]
    
    counter = Counter(lines)
    with open(path, 'w', encoding='utf-8') as f:
        for line, count in reversed(counter.most_common()):
            f.write(f"{count} {line}\n")

    
def main():
    if os.path.exists(f'{triage}[root]/home/'):  
        users = [f'[root]/home/{user}/' for user in os.listdir(f'{triage}[root]/home/')]
        users.append('[root]/root/')
        print(users)

    # type 0 - sort not required
    # type 1 - sort is strictly required 
    filenames = {'.bashrc' : 0, '.zshrc' : 0, '.bash_profile' : 0, '.bash_login' : 0, '.bash_logout' : 0, '.bash_history' : 1}

    for filename in filenames.keys():
        with open(f'{triage}all_{filename[1:]}', 'w') as collector: 
            for user in users:
                path = f'{triage}{user}{filename}' 
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        collector.writelines(f.readlines())
        if filenames[filename] == 1:
            ssort_filename(f'{triage}all_{filename[1:]}')

if __name__ == '__main__':
    main()
