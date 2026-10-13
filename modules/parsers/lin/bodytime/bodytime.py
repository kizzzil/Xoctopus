import sys
import os
import xoctopus_log as log

triage = os.environ["TRIAGE_PATH"]

if __name__ == '__main__':
    body_path = f"{triage}/bodyfile/bodyfile.txt"
    if not os.path.exists(body_path):
        log.warn(f'body file does not exist: {body_path}')
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
                # Время в UTC, чтобы не зависеть от часового пояса машины аналитика
                row[i] = log.format_time(row[i])
            output_file.write("|".join(row) + '\n')

    log.info('done')



