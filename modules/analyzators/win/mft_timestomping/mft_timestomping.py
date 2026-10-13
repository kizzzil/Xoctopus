import os
import re
import csv
import glob
import sys
from collections import Counter
import xoctopus_log as log

triage = os.environ["TRIAGE_PATH"]

# Исполняемые файлы и скрипты
EXTENSIONS = {'.exe', '.dll', '.sys', '.scr', '.ps1', '.bat', '.cmd', '.vbs', '.vbe', '.js', '.jse', '.wsf', '.hta'}
# Папки, куда может писать пользователь или вредонос (пути из MFTECmd: .\Users\...)
SUSPICIOUS_DIRS = re.compile(r'^\.\\(Users\\|ProgramData\\|Windows\\Temp|PerfLogs|\$Recycle\.Bin|Intel\\)', re.I)
EXCLUDE_DIRS = re.compile(r'\\Start Menu\\|\\Package Cache\\|\\Installer Cache\\', re.I)
# Если в одну минуту появилось много файлов с SI<FN - это установщик или распаковка архива, а не точечная подмена
MAX_PER_MINUTE = 20

def is_si_before_fn(row):
    return row['SI<FN'] == 'True' and row['Created0x30'] and row['Created0x10'] < row['Created0x30']

def os_image_day(rows):
    '''День сборки образа Windows: файлы ОС, скопированные из образа, сохраняют эту дату в SI'''
    days = Counter(row['Created0x10'][:10] for row in rows
                   if row['ParentPath'].lower().startswith('.\\windows') and is_si_before_fn(row))
    return days.most_common(1)[0][0] if days else None

def analyze(mft_path, disk):
    with open(mft_path, 'r', encoding='utf-8-sig', newline='') as f:
        rows = list(csv.DictReader(f))
    image_day = os_image_day(rows)
    per_minute = Counter(row['Created0x30'][:16] for row in rows if is_si_before_fn(row))

    result = []
    for row in rows:
        if row['InUse'] != 'True' or row['IsDirectory'] == 'True' or row['IsAds'] == 'True':
            continue
        if row['Extension'].lower() not in EXTENSIONS:
            continue
        path = row['ParentPath']
        if not SUSPICIOUS_DIRS.match(path) or EXCLUDE_DIRS.search(path + '\\'):
            continue
        # Время создания в $STANDARD_INFORMATION раньше, чем в $FILE_NAME - признак подмены времени
        if not is_si_before_fn(row):
            continue
        # Файлы из образа Windows сохраняют дату сборки образа
        if image_day and row['Created0x10'].startswith(image_day):
            continue
        if per_minute[row['Created0x30'][:16]] > MAX_PER_MINUTE:
            continue
        row['FullPath'] = f"{disk}:{path[1:]}\\{row['FileName']}"
        result.append(row)
    return result

def main():
    mft_files = [p for p in glob.glob(f'{triage}/MFT_*.csv') if re.search(r'[\\/]MFT_[A-Z]\.csv$', p)]
    if not mft_files:
        log.warn('MFT_<disk>.csv not found, run parser zimmerman_extractor first')
        sys.exit(0)

    res_path = f'{triage}/Xoctopus_mft_timestomping.csv'
    columns = ['FullPath', 'Created0x10', 'Created0x30', 'LastModified0x10', 'LastModified0x30', 'uSecZeros', 'FileSize', 'EntryNumber']
    with open(res_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        for mft_path in sorted(mft_files):
            disk = mft_path[-5]
            for row in analyze(mft_path, disk):
                writer.writerow([row[c] for c in columns])
                # Округленное до секунды время (uSecZeros) характерно для утилит подмены времени
                zeros = row['uSecZeros'] == 'True'
                log.alert('Possible timestomping (SI created < FN created)',
                          details=f"{row['FullPath']}: SI {row['Created0x10'][:19]}, FN {row['Created0x30'][:19]}"
                                  + (', zero microseconds' if zeros else ''),
                          evidence=res_path, severity='high' if zeros else 'medium', time=row['Created0x30'][:19])
    log.info('done')

if __name__ == '__main__':
    main()
