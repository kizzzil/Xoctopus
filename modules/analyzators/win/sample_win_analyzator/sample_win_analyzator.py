
import os
import xoctopus_log as log
triage = os.environ["TRIAGE_PATH"]

def main():
    log.info('run sample win analyzator')
    # Находки пишутся так:
    # log.alert('Title', details='...', evidence=f'{triage}/Xoctopus_result.txt', severity='high')

if __name__ == '__main__':
    main()
