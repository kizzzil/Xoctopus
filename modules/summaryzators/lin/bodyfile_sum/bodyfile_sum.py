import os
import xoctopus_log as log

# Блок десериализации путей триажа и отбора только 'lin'
triages = os.environ['TRIAGE_PATHES']
triages = [pair.split(',') for pair in triages.split(";")]
triages = [f'{path}/' for path, os_name in triages if os_name == 'lin']

def main():
    text = []
    for path in triages:
        if os.path.exists(f'{path}/Xoctopus_bodyfile_convert.txt'):
            filepath = f'{path}/Xoctopus_bodyfile_convert.txt'
        elif os.path.exists(f'{path}/bodyfile/bodyfile.txt'):
            filepath = f'{path}/bodyfile/bodyfile.txt'
        else:
            log.warn(f'bodyfile not found, triage skipped: {path}')
            continue

        with open(filepath, 'r') as f:
            hostname = path.split('/')[-2]
            lines = [f'{line[:-1:]}|{hostname}\n' for line in f.readlines()]
            text.extend(lines)
             
    with open(f"{os.environ['XOCTOPUS_RUN_DIR']}/super_Xoctopus_bodyfile", 'w') as f:
        f.writelines(text)
    log.info('done')
        
if __name__ == '__main__':
    main()
