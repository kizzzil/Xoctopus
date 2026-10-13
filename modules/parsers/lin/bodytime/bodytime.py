import datetime
import sys
import os
import colorama

triage = os.environ["TRIAGE_PATH"]

if __name__ == '__main__':
    body_path = f"{triage}/bodyfile/bodyfile.txt"
    if not os.path.exists(body_path):
        print(f"Module bodytime: " + colorama.Fore.YELLOW + f"Warning! body file does not exist: {body_path}")
        sys.exit(0)

    text = []
    with open(body_path, 'rb') as f:
        for line in f:
            try:
                decoded = line.decode('utf-8')
            # нужно для обработки ошибок
            except UnicodeDecodeError:
                decoded = line.decode('latin-1')
            text.append(decoded)
    with open(f'{triage}/Xoctopus_bodyfile_convert.txt', 'w') as output_file:
        for line in text:
            row = line.rstrip('\r\n').split('|')
            if len(row) < 11:
                continue  # пропустить некорректные строки
            for i in range(7,11):
                if row[i] == '':
                    continue
                row[i] = datetime.datetime.fromtimestamp(int(row[i])).strftime('%d.%m.%Y %H:%M:%S')
            output_file.write("|".join(row) + '\n')

    print('Module bodytime: ' + colorama.Fore.GREEN + 'Success')



