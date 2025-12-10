# Xoctopus
Xoctopus - ваш помощник при анализе триажей собранных с помощью UAC и KAPE. 

### ВНИМАНИЕ
1. Для использования встроенного плагина zimmerman_tools необходимо в файле `Xoctopus.py` указать путь до папки с утилитами Zimmerman.
2. `pip install click` если еще не установлен.


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


