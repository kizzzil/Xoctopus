import os

# Блок десериализации путей триажа и отбора только 'lin'
triages = os.environ['TRIAGE_PATHES']
triages = [ pair.split(',') for pair in triages.split(";")]
triages = [path for path, os_name in triages if os_name == 'lin']

def main():
    ## Выявления файлов созданных парсером users_dot_files
    ## и классификации их по соответствующим триажам 
    files = {}
    for path in triages:
        dot_files = [filename for filename in os.listdir(path) if 'Xoctopus_all_dot' in filename]
        for filename in dot_files:
            if filename in files.keys():
                files[filename].append(f'{path}/')             
            else:
                files[filename] = [f'{path}/']             
    
    ## Определяет файлы где необходимо делать сортировку или 
    sort_them = []#'Xoctopus_all_dot_bash_history'] 
    
    for filename in files.keys():
        if filename in sort_them:
            print('aboba') 
        else:
            text = []
            for path in files[filename]:
                text.append(f"###XOCOCTOPUS: hostname {path.split('/')[-2]}###\n")
                with open(f'{path}/{filename}', 'r') as f:
                    text.extend(f.readlines())
            with open(f'{path}/../super_{filename}', 'w') as f:
                f.writelines(text)


        
if __name__ == '__main__':
    main()
