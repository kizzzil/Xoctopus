import datetime
import sys
import os

triage = os.environ["TRIAGE"]

if __name__ == '__main__':
    body_path = f"{triage}/bodyfile/bodyfile.txt"
    if not os.path.exists(body_path):
        print(f"ERROR\nbody file path is not specified\nPlease check file path: {body_path}")
    
    try:
        f = open(body_path, 'r+')
    except:
        print(f'ERROR: File path does not exist\nPlease check file path {body_path}')
    
    text = []
    with open(body_path, 'rb') as f:
        for line in f:
            try:
                decoded = line.decode('utf-8')
            except UnicodeDecodeError:
                decoded = line.decode('latin-1')  # или другой подходящей кодировки
            text.append(decoded)
    output_file = open(f'{body_path[:-4]}_convert.txt', 'w')

    for line in text:
        row = line.split('|')
        if row[10] != '':
            row[10] = row[10][:-2]
        for i in range(7,11):
            if row[i] == '':
                continue
            row[i] = datetime.datetime.fromtimestamp(int(row[i])).strftime('%d.%m.%Y %H:%M:%S')
        output_file.write("|".join(row) + '\n')
        
    output_file.close() 
    f.close()
    print('Module bodytime: Success')

