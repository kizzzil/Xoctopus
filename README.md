# Xoctopus
Xoctopus - ваш помощник при анализе триажей собранных с помощью UAC и KAPE. 

### ВНИМАНИЕ
1. Установить зависимости: `pip install -r requirements.txt`
2. Для модуля zimmerman_extractor нужен путь до папки с утилитами Zimmerman (по умолчанию `/mnt/c/tools/`).
   Задать другой путь: параметр `-z /path/to/tools` или переменная окружения `ZIMMERMAN_TOOLS_PATH`.

Результаты модулей сохраняются в папку триажа (файлы `Xoctopus_*`), сводные результаты - в родительскую папку триажей (`super_*`).
Если какой-то модуль упал, остальные продолжат работу, а в конце будет выведен список упавших модулей.

### Находки и логи
| Файл | Где | Что |
|---|---|---|
| `Xoctopus_findings.csv` | папка триажа | находки анализаторов: `time, host, module, severity, title, details, evidence_path` |
| `super_Xoctopus_findings.csv` | папка с триажами | находки всех хостов (модуль `summaryzators/all/findings_sum`) |
| `Xoctopus.log` | папка триажа | лог модулей по этому триажу |
| `Xoctopus_run.log` | папка с триажами | общий лог всех прогонов |

Строка лога: `[дд.мм.гггг ЧЧ:ММ:СС] [LEVEL] [host] module: message`, уровни `INFO`, `WARN`, `ERROR`, `ALERT` (находка).
Находки с severity `low` не выводятся в консоль и лог, они есть только в `Xoctopus_findings.csv` (в логе - их количество).
Все время (в логах и в результатах, например bodytime) - в UTC.

### Как написать модуль
Модуль - папка `modules/<parsers|analyzators|summaryzators>/<lin|win|all>/<name>/<name>.py`.
Окружение: `TRIAGE_PATH`, `TRIAGE_NAME` (для summaryzators - `TRIAGE_PATHES` и `XOCTOPUS_RUN_DIR`).
```python
import xoctopus_log as log
log.info('done')
log.warn('input file not found')          # нет входных данных -> WARN и exit code 0
log.error('tool failed'); sys.exit(1)     # ошибка -> ERROR и exit code != 0
log.alert('Process masquerading', details='pid 42: ...', evidence=res_path, severity='high')
```
Список доступных модулей: `python3 Xoctopus.py --help`


Типичный запуск для одного триажа
```bash
python3 Xoctopus.py -t /path/to/uac/triage
```
Запуск одного плагина

```bash
python3 Xoctopus.py -t /path/to/uac/triage -p plug_name
```

Запуск для множества триажей для директории `./Xoctopus.py/../`
```bash
python3 Xoctopus.py -c
```


Запуск для множества триажей для директории `./Xoctopus.py/../`, но с одним плагином
```bash
python3 Xoctopus.py -c -p plug_name
```



Полный прогон (парсеры, анализаторы и сводка) для множества триажей
```bash
python3 Xoctopus.py -m /path/to/triages -a
```

### Тесты
```bash
pip install pytest
python3 -m pytest tests
```
