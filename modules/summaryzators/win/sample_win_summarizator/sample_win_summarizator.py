
import os

# Блок десериализации путей триажа и отбора только 'lin'
triages = os.environ['TRIAGE_PATHES']
triages = [pair.split(',') for pair in triages.split(";")]
triages = [f'{path}/' for path, os_name in triages if os_name == 'lin']

def main():
    text = []
    # for path in triages:
    #     if os.path.exists(f'{path}/Xoctopus_bodyfile_convert.txt'):
    #         filepath = f'{path}/Xoctopus_bodyfile_convert.txt'
    #     elif os.path.exists(f'{path}/bodyfile/bodyfile.txt'):
    #         filepath = f'{path}/bodyfile/bodyfile.txt'
    #     else:
    #         print(f'Module bodyfile_sum: ERROR. Невозможно открыть bodyfile по стандартному пути ') 
    #         sys.exit(0)
    #
    #     with open(filepath, 'r') as f:
    #         lines = [f'{line[:-1:]}|{path.split('/')[-2]}\n' for line in f.readlines()]
    #         text.extend(lines)
    #
    # with open(f'{path}/../super_Xoctopus_bodyfile', 'w') as f:
    #     f.writelines(text)
