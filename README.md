# Xoctopus
Xoctopus - ваш помощник при анализе триажей собранных с помощью UAC и KAPE. 

### ВНИМАНИЕ
1. Установить зависимости: `pip install -r requirements.txt`
2. Для модуля zimmerman_extractor нужен путь до папки с утилитами Zimmerman (по умолчанию `/mnt/c/tools/`).
   Задать другой путь: параметр `-z /path/to/tools` или переменная окружения `ZIMMERMAN_TOOLS_PATH`.

Результаты модулей сохраняются в папку триажа (файлы `Xoctopus_*`), сводные результаты - в родительскую папку триажей (`super_*`).
Если какой-то модуль упал, остальные продолжат работу, а в конце будет выведен список упавших модулей.
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
